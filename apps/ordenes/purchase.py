"""
Purchase orchestration for OvniTicket.

`ejecutar_compra` is the single entry-point that ties together:
  seat validation → price calculation → payment → order/ticket creation → seat confirmation.

Everything runs inside one atomic transaction so a mid-flight failure
leaves the DB in a clean state.
"""

import logging

from django.db import transaction

from apps.asientos.models import EstadoAsientoEvento
from apps.asientos.models import Asientos
from apps.asientos.services import confirmar_compra, liberar_asientos_usuario, SeatUnavailableError
from apps.eventos.models import Eventos
from apps.grid_cells.models import GridCells
from apps.precio_zona_evento.models import PrecioZonaEvento
from apps.tickets.models import Tickets

from .models import Ordenes
from .payment import procesar_pago
from .services import crear_orden

logger = logging.getLogger(__name__)


class PaymentFailedError(Exception):
    """Raised when the payment gateway rejects the charge."""
    def __init__(self, message: str, gateway_error: str | None = None):
        super().__init__(message)
        self.gateway_error = gateway_error


class EventPricingError(Exception):
    """Raised when the event is not correctly priced (missing PrecioZonaEvento rows).
    This is a *configuration* error, not a seat-availability error, and should
    surface to the user as a distinct HTTP status so the frontend doesn't
    mis-report it as 'someone else took your seats'."""
    def __init__(self, message: str, zonas_sin_precio: list[int] | None = None):
        super().__init__(message)
        self.zonas_sin_precio = zonas_sin_precio or []


@transaction.atomic
def ejecutar_compra(
    id_evento: int,
    ids_grid_cell: list[int],
    usuario,
    metodo_pago: str = "mock",
    token: str | None = None,
    operation_id: str | None = None,
    request=None,
) -> dict:
    """
    Orchestrate a complete ticket purchase.

    Parameters
    ----------
    id_evento : int
        PK of the Eventos row.
    ids_grid_cell : list[int]
        PKs of the GridCells the user wants to buy.
    usuario : Usuarios
        Authenticated user making the purchase.
    metodo_pago : str
        Payment method string forwarded to the payment module.
    token : str | None
        Optional gateway token (pass ``'fail'`` to test a decline).
    request :
        Django request object forwarded to audit-log helpers.

    Returns
    -------
    dict
        ``{ 'orden': Ordenes, 'tickets': list[Tickets], 'transaction_id': str }``

    Raises
    ------
    SeatUnavailableError
        If any seat is no longer held by this user when the transaction opens.
    PaymentFailedError
        If the payment gateway declines the charge.
    """

    if operation_id is not None:
        orden_existente = Ordenes.objects.filter(operation_id=operation_id).first()
        if orden_existente is not None:
            tickets_existentes = list(Tickets.objects.filter(id_orden=orden_existente))
            logger.info(
                "ejecutar_compra: idempotent replay — operation_id=%s orden=%s",
                operation_id, orden_existente.pk,
            )
            return {
                "orden": orden_existente,
                "tickets": tickets_existentes,
                "transaction_id": orden_existente.operation_id or "replay",
            }

    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=usuario,
        )
    )

    if len(estados) != len(ids_grid_cell):
        logger.warning(
            "ejecutar_compra: seat hold mismatch for usuario=%s evento=%s "
            "expected=%d found=%d",
            usuario.pk, id_evento, len(ids_grid_cell), len(estados),
        )
        raise SeatUnavailableError(
            "Uno o más asientos ya no están retenidos por este usuario. "
            "Por favor, inicia el proceso de compra de nuevo."
        )

    evento = Eventos.objects.get(pk=id_evento)

    cells = list(
        GridCells.objects.filter(
            id_grid_cells__in=ids_grid_cell,
        ).select_related("id_zona")
    )

    if len(cells) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos (grid_cells) no existen.")

    cell_zone_map: dict[int, int] = {
        cell.id_grid_cells: cell.id_zona_id for cell in cells
    }

    zone_ids = list(set(cell_zone_map.values()))

    price_rows = PrecioZonaEvento.objects.filter(
        id_evento=id_evento,
        id_zona__in=zone_ids,
    )
    zone_price_map: dict[int, float] = {
        row.id_zona_id: row.precio for row in price_rows
    }

    missing_zones = [z for z in zone_ids if z not in zone_price_map]
    if missing_zones:
        raise EventPricingError(
            "Este evento no tiene precios configurados para todas sus zonas. "
            "Contacta al organizador para que agregue los precios faltantes.",
            zonas_sin_precio=missing_zones,
        )

    total: float = sum(
        zone_price_map[cell_zone_map[cell_pk]]
        for cell_pk in ids_grid_cell
    )
    logger.debug(
        "ejecutar_compra: total=%.2f para %d asientos (evento=%s, usuario=%s)",
        total, len(ids_grid_cell), id_evento, usuario.pk,
    )

    resultado = procesar_pago(monto=total, metodo_pago=metodo_pago, token=token)

    if not resultado["success"]:
        liberar_asientos_usuario(id_evento=id_evento, usuario=usuario)
        logger.warning(
            "ejecutar_compra: payment failed for usuario=%s — %s",
            usuario.pk, resultado["error"],
        )
        raise PaymentFailedError(
            "El pago no pudo procesarse.",
            gateway_error=resultado["error"],
        )

    logger.info(
        "ejecutar_compra: payment success — transaction_id=%s usuario=%s",
        resultado["transaction_id"], usuario.pk,
    )

    orden: Ordenes = crear_orden(
        total=total,
        estatus=Ordenes.ESTATUS_PAGADO,
        id_evento=evento,
        id_usuario=usuario,
        operation_id=operation_id,
        request=request,
    )

    cell_pk_to_cell = {cell.id_grid_cells: cell for cell in cells}
    asientos_por_grid_cell = {
        asiento.id_grid_cell_id: asiento
        for asiento in Asientos.objects.filter(id_grid_cell_id__in=ids_grid_cell)
    }
    tickets: list[Tickets] = []

    for cell_pk in ids_grid_cell:
        cell = cell_pk_to_cell[cell_pk]
        precio = zone_price_map[cell.id_zona_id]
        asiento = asientos_por_grid_cell.get(cell_pk)

        ticket = Tickets.objects.create(
            precio=precio,
            id_orden=orden,
            id_asiento=asiento,
            id_grid_cell=cell,
            id_evento=evento,
        )
        tickets.append(ticket)

    logger.info(
        "ejecutar_compra: %d tickets created for orden=%s",
        len(tickets), orden.pk,
    )

    confirmar_compra(
        id_evento=id_evento,
        ids_grid_cell=ids_grid_cell,
        usuario=usuario,
    )

    return {"orden": orden, "tickets": tickets, "transaction_id": resultado["transaction_id"]}