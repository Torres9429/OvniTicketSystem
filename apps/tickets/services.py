from django.db import transaction
from .models import Tickets
from apps.asientos.models import Asientos
from apps.auditoria_logs.services import registrar_auditoria


class AsientoNoDisponibleError(Exception):
    pass


def crear_ticket(precio: float, id_orden, id_asiento, id_evento, id_usuario=None, request=None) -> Tickets:
    with transaction.atomic():
        # Bloqueo a nivel de fila sobre el asiento para serializar solicitudes concurrentes
        # del mismo asiento. Mientras esta transacción no termine, cualquier otra que
        # intente bloquear el mismo asiento quedará en espera.
        Asientos.objects.select_for_update().get(pk=id_asiento.pk)

        # Verificar que el asiento no esté ya reservado para este evento.
        # Se excluyen órdenes canceladas, que liberan el asiento.
        ya_reservado = Tickets.objects.filter(
            id_asiento=id_asiento,
            id_evento=id_evento,
        ).exclude(id_orden__estatus='cancelled').exists()

        if ya_reservado:
            raise AsientoNoDisponibleError("El asiento ya está reservado para este evento.")

        ticket = Tickets.objects.create(
            precio=precio,
            id_orden_id=id_orden.pk,
            id_asiento_id=id_asiento.pk,
            id_evento_id=id_evento.pk,
        )

    if id_usuario:
        registrar_auditoria(
            entidad='tickets',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'precio': ticket.precio, 'id_orden': id_orden.pk, 'id_asiento': id_asiento.pk, 'id_evento': id_evento.pk},
            ip=request,
        )
    return ticket


def actualizar_ticket(ticket: Tickets, precio: float, id_orden, id_asiento, id_evento, id_usuario=None, request=None) -> Tickets:
    valores_antes = {'precio': ticket.precio, 'id_orden': ticket.id_orden.pk, 'id_asiento': ticket.id_asiento.pk, 'id_evento': ticket.id_evento.pk}
    ticket.precio = precio
    ticket.id_orden = id_orden
    ticket.id_asiento = id_asiento
    ticket.id_evento = id_evento
    ticket.save(update_fields=['precio', 'id_orden', 'id_asiento', 'id_evento'])
    if id_usuario:
        registrar_auditoria(
            entidad='tickets',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'precio': ticket.precio, 'id_orden': ticket.id_orden.pk, 'id_asiento': ticket.id_asiento.pk, 'id_evento': ticket.id_evento.pk},
            ip=request,
        )
    return ticket


def eliminar_ticket(ticket: Tickets, id_usuario=None, request=None) -> None:
    valores_antes = {'precio': ticket.precio, 'id_orden': ticket.id_orden.pk, 'id_asiento': ticket.id_asiento.pk, 'id_evento': ticket.id_evento.pk}
    if id_usuario:
        registrar_auditoria(
            entidad='tickets',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    ticket.delete()
