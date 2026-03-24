from .models import Tickets


def crear_ticket(precio: float, id_orden, id_asiento, id_evento) -> Tickets:
    return Tickets.objects.create(
        precio=precio,
        id_orden_id=id_orden.pk,
        id_asiento_id=id_asiento.pk,
        id_evento_id=id_evento.pk,
    )


def actualizar_ticket(ticket: Tickets, precio: float, id_orden, id_asiento, id_evento) -> Tickets:
    ticket.precio = precio
    ticket.id_orden = id_orden
    ticket.id_asiento = id_asiento
    ticket.id_evento = id_evento
    ticket.save(update_fields=['precio', 'id_orden', 'id_asiento', 'id_evento'])
    return ticket


def eliminar_ticket(ticket: Tickets) -> None:
    ticket.delete()
