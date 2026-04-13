from django.db.models import Q
from apps.lugares.models import Lugares


def get_all_lugares():
    lugares = Lugares.objects.all()
    return lugares


def get_lugares_disponibles():
    lugares = Lugares.objects.exclude(estatus='INHABILITADO')
    return lugares


def buscar_lugares_por_nombre(nombre: str):
    lugares = Lugares.objects.filter(nombre__icontains=nombre, estatus='PUBLICADO')
    return lugares


def buscar_lugares_por_ciudad(ciudad: str):
    lugares = Lugares.objects.filter(ciudad__icontains=ciudad, estatus='PUBLICADO')
    return lugares


def get_lugares_por_dueno(id_dueno: int):
    """Obtener todos los lugares de un dueño específico"""
    return Lugares.objects.filter(id_dueno=id_dueno)
