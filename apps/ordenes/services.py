from django.utils import timezone
from .models import Ordenes
from apps.auditoria_logs.services import registrar_auditoria

def crear_orden(total: float, estatus: str, id_evento, id_usuario, request=None) -> Ordenes:
    now = timezone.now()
    orden = Ordenes.objects.create(
        total=total,
        estatus=estatus,
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_evento_id=id_evento.pk,
        id_usuario_id=id_usuario.pk,
    )
    registrar_auditoria(
        entidad='ordenes',
        accion='CREAR',
        id_usuario=id_usuario,
        valores_antes=None,
        valores_despues={'total': orden.total, 'estatus': orden.estatus, 'fecha_creacion': str(orden.fecha_creacion), 'fecha_actualizacion': str(orden.fecha_actualizacion), 'id_evento': id_evento.nombre, 'id_usuario': id_usuario.nombre},
        ip=request,
    )
    return orden


def actualizar_orden(orden: Ordenes, total: float, estatus: str, id_evento, id_usuario, request=None) -> Ordenes:
    valores_antes = {'total': orden.total, 'estatus': orden.estatus, 'fecha_actualizacion': str(orden.fecha_actualizacion)}
    orden.total = total
    orden.estatus = estatus
    orden.id_evento = id_evento
    orden.id_usuario = id_usuario
    orden.save(update_fields=['total', 'estatus', 'id_evento', 'id_usuario', 'fecha_actualizacion'])
    registrar_auditoria(
        entidad='ordenes',
        accion='ACTUALIZAR',
        id_usuario=id_usuario,
        valores_antes=valores_antes,
        valores_despues={'total': orden.total, 'estatus': orden.estatus, 'fecha_actualizacion': str(orden.fecha_actualizacion)},
        ip=request,
    )
    return orden


def eliminar_orden(orden: Ordenes, id_usuario=None, request=None) -> None:
    valores_antes = {'total': orden.total, 'estatus': orden.estatus, 'fecha_actualizacion': str(orden.fecha_actualizacion)}
    if id_usuario:
        registrar_auditoria(
            entidad='ordenes',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    orden.delete()
