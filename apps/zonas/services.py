from django.utils import timezone
from .models import Zonas
from apps.auditoria_logs.services import registrar_auditoria

def crear_zona(nombre: str, color: str, id_layout: int, precio: float = 0, id_usuario=None, request=None):
    now = timezone.now()
    zona = Zonas.objects.create(
        nombre=nombre,
        color=color,
        precio=float(precio or 0),
        fecha_creacion=now,
        fecha_modificacion=now,
        id_layout=id_layout,
    )
    if id_usuario:
        registrar_auditoria(
            entidad='zonas',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'nombre': zona.nombre, 'color': zona.color, 'precio': zona.precio, 'fecha_creacion': str(zona.fecha_creacion), 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk},
            ip=request,
        )
    return zona


def actualizar_zona(zona: Zonas, nombre: str, color: str, id_layout: int, precio: float = None, id_usuario=None, request=None):
    from apps.precio_zona_evento.services import propagar_precio_zona_a_eventos

    now = timezone.now()
    valores_antes = {'nombre': zona.nombre, 'color': zona.color, 'precio': zona.precio, 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk}
    precio_anterior = float(zona.precio or 0)
    zona.nombre = nombre
    zona.color = color
    if precio is not None:
        zona.precio = float(precio)
    zona.fecha_modificacion = now
    zona.id_layout_id = id_layout.pk
    zona.save(update_fields=['nombre', 'color', 'precio', 'fecha_modificacion', 'id_layout'])
    # Si el precio cambió, propagar a todos los eventos que usan este layout.
    if precio is not None and abs(float(precio) - precio_anterior) > 1e-9:
        propagar_precio_zona_a_eventos(zona, id_usuario=id_usuario, request=request)
    if id_usuario:
        registrar_auditoria(
            entidad='zonas',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'nombre': zona.nombre, 'color': zona.color, 'precio': zona.precio, 'fecha_modificacion': str(zona.fecha_modificacion), 'id_layout': zona.id_layout.pk},
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