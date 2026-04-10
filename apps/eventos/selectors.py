import datetime

from django.db.models import Q
from apps.eventos.models import Eventos

def get_all_eventos():
    eventos = Eventos.objects.all()
    return eventos

def get_eventos_disponibles():
    eventos = Eventos.objects.filter(estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def buscar_eventos_por_nombre(nombre: str):
    eventos = Eventos.objects.filter(nombre__icontains=nombre, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def buscar_eventos_por_fecha(fecha: datetime.date):
    eventos = Eventos.objects.filter(fecha_inicio__lte=fecha, fecha_fin__gte=fecha, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos

def buscar_eventos_por_lugar(id_lugar: int):
    eventos = Eventos.objects.filter(id_lugar=id_lugar, estatus=Eventos.ESTATUS_PUBLICADO)
    return eventos