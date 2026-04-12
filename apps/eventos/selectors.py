import datetime

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
    _finalizar_eventos_expirados()
    return Eventos.objects.all()

def get_eventos_disponibles():
    _finalizar_eventos_expirados()
    return Eventos.objects.filter(estatus=Eventos.ESTATUS_PUBLICADO)

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
    return Eventos.objects.filter(id_lugar__id_dueno=id_usuario)