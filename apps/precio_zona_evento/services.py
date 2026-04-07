from django.utils import timezone
from .models import PrecioZonaEvento
from apps.auditoria_logs.services import registrar_auditoria

def crear_precio_zona_evento(precio: float, id_zona: int, id_evento: int, id_usuario=None, request=None):
    now = timezone.now()
    precio_zona_evento = PrecioZonaEvento.objects.create(
        precio=precio,
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_zona=id_zona,
        id_evento=id_evento
    )
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'precio': precio_zona_evento.precio, 'fecha_creacion': str(precio_zona_evento.fecha_creacion), 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk},
            ip=request,
        )
    return precio_zona_evento

def actualizar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento, precio: float, id_zona: int, id_evento: int, id_usuario=None, request=None):
    now = timezone.now()
    valores_antes = {'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona_id, 'id_evento': precio_zona_evento.id_evento_id}
    precio_zona_evento.precio = precio
    precio_zona_evento.fecha_actualizacion= now
    precio_zona_evento.id_zona_id = id_zona.pk
    precio_zona_evento.id_evento_id = id_evento.pk
    precio_zona_evento.save(update_fields=['precio', 'fecha_actualizacion', 'id_zona', 'id_evento'])
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk},
            ip=request,
        )
    return precio_zona_evento

def eliminar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento, id_usuario=None, request=None):
    valores_antes = {'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk}
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    precio_zona_evento.delete()