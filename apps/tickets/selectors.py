from django.db import connection
from django.db.models import Case, IntegerField, When

from apps.tickets.models import Tickets


def get_all_tickets():
    return Tickets.objects.all()


def _obtener_ids_tickets(sql: str, params: tuple | None = None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def _queryset_tickets_por_ids(ids_tickets: list[int]):
    if not ids_tickets:
        return Tickets.objects.none()

    orden_personalizado = Case(
        *[When(id_ticket=ticket_id, then=pos) for pos, ticket_id in enumerate(ids_tickets)],
        output_field=IntegerField(),
    )
    return Tickets.objects.filter(id_ticket__in=ids_tickets).order_by(orden_personalizado)


def get_tickets_por_orden(id_orden: int):
    ids_tickets = _obtener_ids_tickets(
        """
        SELECT id_ticket
        FROM v_tickets_lookup
        WHERE id_orden = %s
        ORDER BY id_ticket DESC
        """,
        (id_orden,),
    )
    return _queryset_tickets_por_ids(ids_tickets)


def get_tickets_por_evento(id_evento: int):
    ids_tickets = _obtener_ids_tickets(
        """
        SELECT id_ticket
        FROM v_tickets_lookup
        WHERE id_evento = %s
        ORDER BY id_ticket DESC
        """,
        (id_evento,),
    )
    return _queryset_tickets_por_ids(ids_tickets)
