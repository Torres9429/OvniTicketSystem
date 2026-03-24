from apps.ordenes.models import Ordenes


def get_all_ordenes():
    return Ordenes.objects.all()


def get_ordenes_por_evento(id_evento: int):
    return Ordenes.objects.filter(id_evento=id_evento)


def get_ordenes_por_usuario(id_usuario: int):
    return Ordenes.objects.filter(id_usuario=id_usuario)
