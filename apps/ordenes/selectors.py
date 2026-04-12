from apps.ordenes.models import Ordenes

# Orden por defecto para todos los listados: más reciente primero.
# Tiebreaker por id_orden descendente para estabilidad si dos órdenes
# comparten el mismo timestamp.
_ORDEN_RECIENTE = ('-fecha_creacion', '-id_orden')


def get_all_ordenes():
    return Ordenes.objects.all().order_by(*_ORDEN_RECIENTE)


def get_ordenes_por_evento(id_evento: int):
    return Ordenes.objects.filter(id_evento=id_evento).order_by(*_ORDEN_RECIENTE)


def get_ordenes_por_usuario(id_usuario: int):
    return Ordenes.objects.filter(id_usuario=id_usuario).order_by(*_ORDEN_RECIENTE)
