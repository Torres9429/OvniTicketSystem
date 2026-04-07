from django.utils import timezone
from .models import Zonas
from apps.auditoria_logs.services import registrar_auditoria

def crear_zona(nombre: str, color: str, id_layout: int, id_usuario=None, request=None):
    now = timezone.now()
    zona = Zonas.objects.create(
        nombre=nombre, 
        color=color, 
        fecha_creacion=now, 
        fecha_modificacion=now, 
        id_layout=id_layout
        )
    if id_usuario:
        registrar_auditoria(
            entidad='zonas',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'nombre': zona.nombre, 'color': zona.color, 'fecha_creacion': str(zona.fecha_creacion), 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk},
            ip=request,
        )
    return zona


def actualizar_zona(zona: Zonas, nombre: str, color: str, id_layout: int, id_usuario=None, request=None):
    now = timezone.now()
    valores_antes = {'nombre': zona.nombre, 'color': zona.color, 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk}
    zona.nombre = nombre
    zona.color = color
    zona.fecha_modificacion = now
    zona.id_layout_id = id_layout.pk
    zona.save(update_fields=['nombre', 'color', 'fecha_modificacion', 'id_layout'])
    if id_usuario:
        registrar_auditoria(
            entidad='zonas',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'nombre': zona.nombre, 'color': zona.color, 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk},
            ip=request,
        )
    return zona

def eliminar_zona(zona: Zonas, id_usuario=None, request=None):
    valores_antes = {'nombre': zona.nombre, 'color': zona.color, 'fecha_modificacion': str(zona.fecha_modificacion)}
    if id_usuario:
        registrar_auditoria(
            entidad='zonas',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    zona.delete()