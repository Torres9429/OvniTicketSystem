from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Asientos, EstadoAsientoEvento
from apps.auditoria_logs.services import registrar_auditoria


class SeatUnavailableError(Exception):
    """Raised when one or more seats are not available for hold/purchase."""
    pass


# ───────────────────────────── legacy CRUD ─────────────────────────────

def create_asiento(data, id_usuario=None, request=None):
    asiento = Asientos.objects.create(
        grid_row=data.get('grid_row'),
        grid_col=data.get('grid_col'),
        numero_asiento=data.get('numero_asiento'),
        existe=data.get('existe'),
        id_zona=data.get('id_zona')
    )
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk},
            ip=request,
        )
    return asiento

def update_asiento(asiento, data, id_usuario=None, request=None):
    valores_antes = {'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk}
    asiento.grid_row = data.get('grid_row', asiento.grid_row)
    asiento.grid_col = data.get('grid_col', asiento.grid_col)
    asiento.numero_asiento = data.get('numero_asiento', asiento.numero_asiento)
    asiento.existe = data.get('existe', asiento.existe)
    id_zona = data.get('id_zona', asiento.id_zona)
    asiento.id_zona_id = id_zona.pk
    asiento.save()
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk},
            ip=request,
        )
    return asiento

def delete_asiento(asiento, id_usuario=None, request=None):
    valores_antes = {'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk}
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    asiento.delete()
    return True


# ───────────────── seat state machine (hold / release / confirm) ─────────────────

def _liberar_expirados(id_evento):
    """Release all holds whose timeout has passed (lazy check)."""
    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        estado=EstadoAsientoEvento.RETENIDO,
        retenido_hasta__lt=timezone.now(),
    ).update(
        estado=EstadoAsientoEvento.DISPONIBLE,
        retenido_por=None,
        retenido_hasta=None,
    )


def obtener_disponibilidad_evento(id_evento):
    """Return seat states for an event after releasing expired holds."""
    _liberar_expirados(id_evento)
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
    ).values('id_grid_cell', 'estado')


def inicializar_estado_asientos(id_evento, id_layout):
    """Create EstadoAsientoEvento rows for every seat-type grid cell in the layout.
    Called when an event is published or when availability is first queried.

    Also backfills PrecioZonaEvento rows from Zonas.precio if they don't
    exist yet — this protects events created before the auto-sync hook
    was added to crear_evento."""
    from apps.grid_cells.models import GridCells
    from apps.precio_zona_evento.services import sincronizar_precios_zona_evento
    from apps.eventos.models import Eventos

    existing = EstadoAsientoEvento.objects.filter(id_evento=id_evento).exists()
    if not existing:
        seat_cells = GridCells.objects.filter(
            id_layout=id_layout,
            tipo='ZONA DE ASIENTOS',
        )
        estados = [
            EstadoAsientoEvento(
                id_grid_cell=cell,
                id_evento_id=id_evento,
                estado=EstadoAsientoEvento.DISPONIBLE,
            )
            for cell in seat_cells
        ]
        EstadoAsientoEvento.objects.bulk_create(estados, ignore_conflicts=True)

    # Defensive backfill: ensure PrecioZonaEvento rows exist for every zone
    # in the layout. Idempotent — doesn't overwrite existing prices.
    try:
        evento = Eventos.objects.get(pk=id_evento)
        sincronizar_precios_zona_evento(evento)
    except Eventos.DoesNotExist:
        pass


@transaction.atomic
def retener_asientos(id_evento, ids_grid_cell, usuario):
    """Hold seats atomically. Raises SeatUnavailableError if any are taken.

    Same-user extension/reduction is supported:
    - Seats already held by this user get their expiry refreshed.
    - Seats previously held by this user but NOT in the new list are released.
    - Seats held by another user or in VENDIDO state raise SeatUnavailableError.

    Returns a dict: {"retenido_hasta": <iso8601 str>, "ids_grid_cell": [<int>, ...]}
    """
    from apps.eventos.models import Eventos

    evento = Eventos.objects.get(pk=id_evento)
    tiempo = evento.tiempo_espera  # minutes
    ahora = timezone.now()

    # Release expired holds first
    _liberar_expirados(id_evento)

    # Lock the requested rows
    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
        )
    )

    if len(estados) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos no existen para este evento.")

    for estado in estados:
        if estado.estado == EstadoAsientoEvento.DISPONIBLE:
            # Normal path — can be held
            pass
        elif estado.estado == EstadoAsientoEvento.RETENIDO and estado.retenido_por_id == usuario.pk:
            # Same-user extension — allowed, will just refresh the expiry
            pass
        else:
            # RETENIDO by someone else, or VENDIDO
            raise SeatUnavailableError(
                f"Asiento (grid_cell={estado.id_grid_cell_id}) no disponible."
            )

    # Determine which cells this user already holds for this event but are NOT
    # in the new ids_grid_cell list — those must be released (user deselected them).
    ids_previamente_retenidos_por_usuario = [
        e.id_grid_cell_id
        for e in EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=usuario,
        )
        if e.id_grid_cell_id not in ids_grid_cell
    ]

    if ids_previamente_retenidos_por_usuario:
        EstadoAsientoEvento.objects.filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_previamente_retenidos_por_usuario,
        ).update(
            estado=EstadoAsientoEvento.DISPONIBLE,
            retenido_por=None,
            retenido_hasta=None,
        )

    nueva_expiracion = ahora + timedelta(minutes=tiempo)

    # Hold / refresh all requested cells
    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    ).update(
        estado=EstadoAsientoEvento.RETENIDO,
        retenido_por=usuario,
        retenido_hasta=nueva_expiracion,
    )

    return {
        "retenido_hasta": nueva_expiracion.isoformat(),
        "ids_grid_cell": list(ids_grid_cell),
    }


@transaction.atomic
def confirmar_compra(id_evento, ids_grid_cell, usuario):
    """Mark held seats as sold. Called after payment confirmation."""
    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=usuario,
        )
    )

    if len(estados) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos ya no están retenidos por este usuario.")

    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    ).update(estado=EstadoAsientoEvento.VENDIDO)

    return estados


def liberar_asientos_usuario(id_evento, usuario):
    """Release all seats held by a user for an event (cancel checkout)."""
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        retenido_por=usuario,
        estado=EstadoAsientoEvento.RETENIDO,
    ).update(
        estado=EstadoAsientoEvento.DISPONIBLE,
        retenido_por=None,
        retenido_hasta=None,
    )