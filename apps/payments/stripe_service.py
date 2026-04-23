"""
Stripe integration service for OvniTicket.

Two responsibilities:
  1. crear_sesion_checkout  — build a Stripe Checkout Session and return it.
  2. completar_compra_stripe — called from the webhook to create the order and
     tickets once Stripe confirms the payment.
  3. obtener_orden_por_sesion — returns the Ordenes row linked to a session,
     used by the frontend success page to resolve the order id.
"""

import json
import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.asientos.models import EstadoAsientoEvento
from apps.eventos.models import Eventos
from apps.grid_cells.models import GridCells
from apps.ordenes.models import Ordenes
from apps.precio_zona_evento.models import PrecioZonaEvento
from apps.tickets.models import Tickets

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Stripe session IDs fit in 64 chars (cs_test_... / cs_live_...) but use first
# 64 chars as a safeguard when storing them as operation_id.
_OP_ID_MAX = 64


def _build_line_items(cells, zone_price_map, evento_nombre):
    """Return a list of Stripe line_item dicts for the given seats."""
    items = []
    for cell in cells:
        precio = zone_price_map[cell.id_zona_id]
        if cell.row is not None and cell.col is not None:
            seat_label = f"Fila {cell.row + 1} - Col {cell.col + 1}"
        else:
            seat_label = f"Asiento #{cell.id_grid_cells}"

        items.append({
            "price_data": {
                "currency": "mxn",
                "product_data": {
                    "name": f"Boleto — {evento_nombre}",
                    "description": seat_label,
                },
                "unit_amount": int(precio * 100),  # centavos
            },
            "quantity": 1,
        })
    return items


def crear_sesion_checkout(
    id_evento,
    usuario,
    ids_grid_cell=None,
    operation_id=None,
    asientos_layout=None,
):
    """
    Validate seat prices then create and return a Stripe Checkout Session.

    Raises ValueError for configuration problems (missing prices, unknown
    seats) so callers can surface them as 400 errors.
    """
    resolved_ids = ids_grid_cell

    # Compatibilidad con el flujo nuevo del frontend (row/col/zone_id).
    if (not resolved_ids) and asientos_layout:
        from apps.asientos.services import resolve_layout_seat_refs_to_grid_cells

        resolved_ids = resolve_layout_seat_refs_to_grid_cells(
            id_evento=id_evento,
            asientos_layout=asientos_layout,
        )

    if not resolved_ids:
        raise ValueError("Debes enviar al menos un asiento para generar el pago.")

    cells = list(
        GridCells.objects.filter(id_grid_cells__in=resolved_ids).select_related("id_zona")
    )
    if len(cells) != len(resolved_ids):
        raise ValueError("Algunos asientos solicitados no existen.")

    zone_ids = list({cell.id_zona_id for cell in cells})
    price_rows = PrecioZonaEvento.objects.filter(
        id_evento=id_evento,
        id_zona__in=zone_ids,
    )
    zone_price_map = {row.id_zona_id: float(row.precio) for row in price_rows}

    missing = [z for z in zone_ids if z not in zone_price_map]
    if missing:
        raise ValueError(
            "El evento no tiene precios configurados para todas las zonas. "
            "Contacta al organizador."
        )

    evento = Eventos.objects.get(pk=id_evento)
    line_items = _build_line_items(cells, zone_price_map, evento.nombre)

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=(
            f"{frontend_url}/pago/exitoso?session_id={{CHECKOUT_SESSION_ID}}"
        ),
        cancel_url=f"{frontend_url}/checkout",
        metadata={
            "id_evento": str(id_evento),
            "ids_grid_cell": json.dumps(resolved_ids),
            "operation_id": operation_id or "",
            "id_usuario": str(usuario.pk),
        },
        client_reference_id=str(operation_id or usuario.pk),
    )

    logger.info(
        "Stripe session created: session=%s usuario=%s evento=%s",
        session.id, usuario.pk, id_evento,
    )
    return session


@transaction.atomic
def completar_compra_stripe(session):
    """
    Idempotent handler for checkout.session.completed webhook events.

    Creates the order and tickets, then marks seats as VENDIDO.
    Safe to call multiple times for the same session (idempotency via
    operation_id or session.id).

    Returns the Ordenes instance (existing or newly created).
    """
    raw_op_id = session.metadata.get("operation_id") or ""
    operation_id = raw_op_id[:_OP_ID_MAX] if raw_op_id else session.id[:_OP_ID_MAX]

    # Idempotency — return existing order without re-creating anything.
    orden_existente = Ordenes.objects.filter(operation_id=operation_id).first()
    if orden_existente is not None:
        logger.info(
            "Stripe webhook: idempotent replay operation_id=%s orden=%s",
            operation_id, orden_existente.pk,
        )
        return orden_existente

    id_evento = int(session.metadata["id_evento"])
    ids_grid_cell = json.loads(session.metadata["ids_grid_cell"])
    id_usuario = int(session.metadata["id_usuario"])

    from apps.usuarios.models import Usuarios
    usuario = Usuarios.objects.get(pk=id_usuario)
    evento = Eventos.objects.get(pk=id_evento)

    cells = list(
        GridCells.objects.filter(id_grid_cells__in=ids_grid_cell).select_related("id_zona")
    )
    logger.debug(
        "completar_compra_stripe: found %d cells for ids=%s",
        len(cells), ids_grid_cell,
    )
    for cell in cells:
        logger.debug(
            "  cell %d: tipo=%s row=%s col=%s id_zona=%s",
            cell.id_grid_cells, cell.tipo, cell.row, cell.col, cell.id_zona_id,
        )

    # Obtener asientos asociados a los grid_cells y crear los faltantes
    from apps.asientos.models import Asientos
    asientos_map = {}

    # Procesar cada grid_cell para obtener o crear su asiento
    for cell in cells:
        if cell.tipo == 'ZONA DE ASIENTOS':
            asiento, created = Asientos.objects.get_or_create(
                id_grid_cell_id=cell.id_grid_cells,
                defaults={
                    'grid_row': cell.row,
                    'grid_col': cell.col,
                    'numero_asiento': cell.col + 1,
                    'existe': 1,
                    'id_zona_id': cell.id_zona_id,
                }
            )
            asientos_map[cell.id_grid_cells] = asiento.id_asiento
            if created:
                logger.info(
                    "Created asiento %d for grid_cell %d",
                    asiento.id_asiento, cell.id_grid_cells,
                )
            else:
                logger.debug(
                    "Found existing asiento %d for grid_cell %d",
                    asiento.id_asiento, cell.id_grid_cells,
                )
        else:
            logger.warning(
                "Cell %d has tipo=%s (not ZONA DE ASIENTOS), no asiento created",
                cell.id_grid_cells, cell.tipo,
            )

    zone_ids = list({cell.id_zona_id for cell in cells})
    zone_price_map = {
        row.id_zona_id: float(row.precio)
        for row in PrecioZonaEvento.objects.filter(
            id_evento=id_evento, id_zona__in=zone_ids
        )
    }
    total = sum(zone_price_map[cell.id_zona_id] for cell in cells)

    now = timezone.now()
    orden = Ordenes.objects.create(
        total=total,
        estatus=Ordenes.ESTATUS_PAGADO,
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_evento_id=evento.pk,
        id_usuario_id=usuario.pk,
        operation_id=operation_id,
    )

    # Crear boletos (tickets)
    tickets_creados = 0
    if len(cells) > 0:
        tickets_to_create = []
        for cell in cells:
            if cell.id_zona_id not in zone_price_map:
                logger.warning(
                    "Cell %s has zone %s but no price in zone_price_map",
                    cell.id_grid_cells, cell.id_zona_id
                )
                continue

            # Obtener el asiento asociado a esta grid_cell (debe existir ahora)
            id_asiento = asientos_map.get(cell.id_grid_cells)
            if not id_asiento:
                logger.warning(
                    "Cell %s (tipo=%s) has no asiento - skipping ticket creation",
                    cell.id_grid_cells, cell.tipo
                )
                continue

            tickets_to_create.append(
                Tickets(
                    precio=zone_price_map[cell.id_zona_id],
                    id_orden_id=orden.pk,
                    id_asiento_id=id_asiento,
                    id_grid_cell_id=cell.id_grid_cells,
                    id_evento_id=id_evento,
                )
            )

        if tickets_to_create:
            try:
                Tickets.objects.bulk_create(tickets_to_create)
                tickets_creados = len(tickets_to_create)
                logger.info(
                    "Created %d tickets for orden=%s",
                    len(tickets_to_create), orden.pk
                )
            except Exception as e:
                logger.error(
                    "Error creating tickets for orden=%s: %s",
                    orden.pk, str(e), exc_info=True
                )
                raise
        else:
            logger.warning("No valid tickets to create for orden=%s", orden.pk)
    else:
        logger.warning("No cells found for ids_grid_cell=%s", ids_grid_cell)

    # Mark seats as sold regardless of current hold state (payment already done).
    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    ).update(estado=EstadoAsientoEvento.VENDIDO)

    logger.info(
        "Stripe purchase completed: orden=%s usuario=%s evento=%s tickets=%d",
        orden.pk, usuario.pk, id_evento, tickets_creados,
    )
    return orden


def obtener_orden_por_sesion(session_id):
    """
    Look up the Ordenes row associated with a Stripe session.

    Returns the Ordenes instance or None if the webhook hasn't fired yet.
    """
    raw = session_id[:_OP_ID_MAX]

    # First try session.id stored directly as operation_id.
    orden = Ordenes.objects.filter(operation_id=raw).first()
    if orden:
        return orden

    # Fallback: look up the session from Stripe to get the original operation_id
    # (the UUID the frontend generated).
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        frontend_op_id = (session.metadata.get("operation_id") or "")[:_OP_ID_MAX]
        if frontend_op_id:
            return Ordenes.objects.filter(operation_id=frontend_op_id).first()
    except stripe.error.StripeError as exc:
        logger.warning("obtener_orden_por_sesion: stripe error — %s", exc)

    return None
