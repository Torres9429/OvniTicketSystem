from django.db.models import Q
from apps.layouts.models import Layouts


def get_all_layouts():
    layouts = Layouts.objects.all()
    return layouts


def get_layouts_disponibles():
    layouts = Layouts.objects.filter(estatus='PUBLICADO')
    return layouts


def buscar_layouts_por_lugar(id_lugar: int):
    layouts = Layouts.objects.filter(id_lugar=id_lugar, estatus='PUBLICADO')
    return layouts


def get_ultima_version_layout_por_lugar(id_lugar: int, include_drafts=False):
    qs = Layouts.objects.filter(id_lugar=id_lugar)
    if not include_drafts:
        qs = qs.filter(estatus='PUBLICADO')
    return qs.order_by('-version', '-id_layout').first()

def get_all_layouts_por_lugar(id_lugar: int):
    return Layouts.objects.filter(id_lugar=id_lugar).order_by('-version')


def get_ultima_version_por_lugar(id_lugar: int):
    return (
        Layouts.objects.filter(id_lugar=id_lugar)
        .order_by('-version')
        .first()
    )