from .models import Zonas
from datetime import datetime

def get_all_zonas():
    zonas = Zonas.objects.all()
    return zonas

def buscar_zona_por_id(id_zona):
    zonas = Zonas.objects.filter(id_zona=id_zona)
    return zonas

def buscar_zona_por_nombre(nombre: str):
    zonas = Zonas.objects.filter(nombre__icontains=nombre)
    return zonas

def buscar_zona_por_color(color: str):
    zonas = Zonas.objects.filter(color__icontains=color)
    return zonas

def buscar_zona_por_fecha_creacion(fecha_creacion: datetime.date):
    zonas = Zonas.objects.filter(fecha_creacion=fecha_creacion)
    return zonas

def buscar_zona_por_layout(id_layout: int):
    zonas = Zonas.objects.filter(id_layout=id_layout)
    return zonas