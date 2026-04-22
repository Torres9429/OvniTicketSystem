from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Asientos, EstadoAsientoEvento
from apps.auditoria_logs.services import registrar_auditoria


class SeatUnavailableError(Exception):
    pass

def create_asiento(data, id_usuario=None, request=None):
    asiento = Asientos.objects.create(
        grid_row=data.get('grid_row'),
        grid_col=data.get('grid_col'),
        numero_asiento=data.get('numero_asiento'),
        existe=data.get('existe'),
        id_zona=data.get('id_zona'),
        id_grid_cell=data.get('id_grid_cell'),
    )
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={
                'grid_row': asiento.grid_row,
                'grid_col': asiento.grid_col,
                'numero_asiento': asiento.numero_asiento,
                'existe': asiento.existe,
                'id_zona': asiento.id_zona.pk,
                'id_grid_cell': asiento.id_grid_cell_id,
            },
            ip=request,
        )
    return asiento

def update_asiento(asiento, data, id_usuario=None, request=None):
    valores_antes = {
        'grid_row': asiento.grid_row,
        'grid_col': asiento.grid_col,
        'numero_asiento': asiento.numero_asiento,
        'existe': asiento.existe,
        'id_zona': asiento.id_zona.pk,
        'id_grid_cell': asiento.id_grid_cell_id,
    }
    asiento.grid_row = data.get('grid_row', asiento.grid_row)
    asiento.grid_col = data.get('grid_col', asiento.grid_col)
    asiento.numero_asiento = data.get('numero_asiento', asiento.numero_asiento)
    asiento.existe = data.get('existe', asiento.existe)
    id_zona = data.get('id_zona', asiento.id_zona)
    asiento.id_zona_id = id_zona.pk
    asiento.id_grid_cell = data.get('id_grid_cell', asiento.id_grid_cell)
    asiento.save()
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={
                'grid_row': asiento.grid_row,
                'grid_col': asiento.grid_col,
                'numero_asiento': asiento.numero_asiento,
                'existe': asiento.existe,
                'id_zona': asiento.id_zona.pk,
                'id_grid_cell': asiento.id_grid_cell_id,
            },
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


def _liberar_expirados(id_evento):
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
    _liberar_expirados(id_evento)
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
    ).values('id_grid_cell', 'estado')


def inicializar_estado_asientos(id_evento, id_layout):
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

    try:
        evento = Eventos.objects.get(pk=id_evento)
        sincronizar_precios_zona_evento(evento)
    except Eventos.DoesNotExist:
        pass


@transaction.atomic
def retener_asientos(id_evento, ids_grid_cell, usuario):
    from apps.eventos.models import Eventos

    evento = Eventos.objects.get(pk=id_evento)
    tiempo = evento.tiempo_espera 
    ahora = timezone.now()

    _liberar_expirados(id_evento)

    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
        )
    )

    if len(estados) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos no existen para este evento.")

    for estado in estados:
        is_available = estado.estado == EstadoAsientoEvento.DISPONIBLE
        is_held_by_user = (estado.estado == EstadoAsientoEvento.RETENIDO and 
                           estado.retenido_por_id == usuario.pk)
        
        if not (is_available or is_held_by_user):
            raise SeatUnavailableError(
                f"Asiento (grid_cell={estado.id_grid_cell_id}) no disponible."
            )

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
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        retenido_por=usuario,
        estado=EstadoAsientoEvento.RETENIDO,
    ).update(
        estado=EstadoAsientoEvento.DISPONIBLE,
        retenido_por=None,
        retenido_hasta=None,
    )