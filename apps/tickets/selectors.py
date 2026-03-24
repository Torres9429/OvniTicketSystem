from apps.tickets.models import Tickets


def get_all_tickets():
    return Tickets.objects.all()


def get_tickets_por_orden(id_orden: int):
    return Tickets.objects.filter(id_orden=id_orden)


def get_tickets_por_evento(id_evento: int):
    return Tickets.objects.filter(id_evento=id_evento)
