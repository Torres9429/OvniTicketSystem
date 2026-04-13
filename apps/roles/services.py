from .models import Roles
from apps.auditoria_logs.services import registrar_auditoria


def crear_rol(nombre: str, fecha_creacion, fecha_actualizacion, id_usuario=None, request=None) -> Roles:
    rol = Roles.objects.create(
        nombre=nombre,
        fecha_creacion=fecha_creacion,
        fecha_actualizacion=fecha_actualizacion,
    )
    if id_usuario:
        registrar_auditoria(
            entidad='roles',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'nombre': rol.nombre, 'fecha_creacion': str(rol.fecha_creacion), 'fecha_actualizacion': str(rol.fecha_actualizacion)},
            ip=request,
        )
    return rol


def actualizar_rol(rol: Roles, nombre: str, id_usuario=None, request=None) -> Roles:
    valores_antes = {'nombre': rol.nombre, 'fecha_actualizacion': str(rol.fecha_actualizacion)}
    rol.nombre = nombre
    rol.save(update_fields=['nombre', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='roles',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'nombre': rol.nombre, 'fecha_actualizacion': str(rol.fecha_actualizacion)},
            ip=request,
        )
    return rol


def eliminar_rol(rol: Roles, id_usuario=None, request=None) -> None:
    valores_antes = {'nombre': rol.nombre, 'fecha_actualizacion': str(rol.fecha_actualizacion)}
    if id_usuario:
        registrar_auditoria(
            entidad='roles',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    rol.delete()
