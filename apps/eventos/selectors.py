import datetime

from django.db import connection
from django.db.models import Case, IntegerField, When
from django.db.models import Q
from django.utils import timezone
from apps.eventos.models import Eventos


def _finalizar_eventos_expirados():
    """Lazy check: auto-finalize published events whose fecha_fin has passed."""
    Eventos.objects.filter(
        estatus=Eventos.ESTATUS_PUBLICADO,
        fecha_fin__lt=timezone.now(),
    ).update(
        estatus=Eventos.ESTASTUS_FINALIZADO,
        fecha_actualizacion=timezone.now(),
    )


def get_all_eventos():
    return Eventos.objects.all()


def _obtener_ids_eventos(sql: str, params: tuple | None = None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def _queryset_eventos_por_ids(ids_eventos: list[int]):
    if not ids_eventos:
        return Eventos.objects.none()

    orden_personalizado = Case(
        *[When(id_evento=event_id, then=pos) for pos, event_id in enumerate(ids_eventos)],
        output_field=IntegerField(),
    )
    return Eventos.objects.filter(id_evento__in=ids_eventos).order_by(orden_personalizado)

def get_eventos_disponibles():
    ids_eventos = _obtener_ids_eventos(
        """
        SELECT id_evento
        FROM v_eventos_publicados
        ORDER BY fecha_inicio ASC, id_evento ASC
        """
    )
    return _queryset_eventos_por_ids(ids_eventos)

def buscar_eventos_por_nombre(nombre: str):
    eventos = Eventos.objects.filter(nombre__icontains=nombre, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def buscar_eventos_por_fecha(fecha: datetime.date):
    eventos = Eventos.objects.filter(fecha_inicio__lte=fecha, fecha_fin__gte=fecha, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def buscar_eventos_por_lugar(id_lugar: int):
    eventos = Eventos.objects.filter(id_lugar=id_lugar, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def get_eventos_por_usuario(id_usuario: int):
    """Obtener todos los eventos de los lugares que posee un usuario específico"""
    ids_eventos = _obtener_ids_eventos(
        """
        SELECT id_evento
        FROM v_eventos_por_dueno
        WHERE id_dueno = %s
        ORDER BY id_evento DESC
        """,
        (id_usuario,),
    )
    return _queryset_eventos_por_ids(ids_eventos)