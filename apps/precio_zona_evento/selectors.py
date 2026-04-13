from .models import PrecioZonaEvento
from datetime import datetime

def get_all_precio_zona_evento():
    precio_zona_evento = PrecioZonaEvento.objects.all()
    return precio_zona_evento

def buscar_precio_zona_evento_por_id(id_precio_zona_evento):
    return PrecioZonaEvento.objects.filter(id_precio_zona_evento=id_precio_zona_evento).first()

def buscar_precio_zona_evento_por_id_zona(id_zona: int):
    precio_zona_evento = PrecioZonaEvento.objects.filter(id_zona=id_zona)
    return precio_zona_evento

def buscar_precio_zona_evento_por_id_evento(id_evento: int):
    precio_zona_evento = PrecioZonaEvento.objects.filter(id_evento=id_evento)
    return precio_zona_evento

def buscar_precio_zona_evento_por_precio(precio: float):
    precio_zona_evento = PrecioZonaEvento.objects.filter(precio=precio)
    return precio_zona_evento

def buscar_precio_zona_evento_por_fecha_creacion(fecha_creacion: datetime.date):
    precio_zona_evento = PrecioZonaEvento.objects.filter(fecha_creacion=fecha_creacion)
    return precio_zona_evento