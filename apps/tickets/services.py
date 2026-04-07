from .models import Tickets
from apps.auditoria_logs.services import registrar_auditoria

def crear_ticket(precio: float, id_orden, id_asiento, id_evento, id_usuario=None, request=None) -> Tickets:
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
