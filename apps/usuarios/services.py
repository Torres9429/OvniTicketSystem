from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Usuarios
from apps.auditoria_logs.services import registrar_auditoria

def crear_usuario(nombre: str, correo: str, contrasena: str, fecha_nacimiento, id_rol, apellidos: str =None, estatus: str = 'activo', request=None) -> Usuarios:
    usuario = Usuarios.objects.create(
        nombre=nombre,
        apellidos=apellidos,
        correo=correo,
        contrasena=make_password(contrasena, hasher='bcrypt_sha256'),
        fecha_nacimiento=fecha_nacimiento,
        estatus=estatus,
        fecha_creacion=timezone.now(),
        fecha_actualizacion=timezone.now(),
        id_rol_id=id_rol.pk,
    )
    registrar_auditoria(
        entidad='usuarios',
        accion='CREAR',
        id_usuario=usuario,
        valores_antes=None,
        valores_despues={'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': id_rol.nombre},
        ip=request,
    )
    return usuario


def actualizar_usuario(usuario: Usuarios, nombre: str, correo: str, fecha_nacimiento, id_rol, apellidos: str = None, request=None) -> Usuarios:
    valores_antes = {'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': usuario.id_rol.nombre}
    usuario.nombre = nombre
    usuario.apellidos = apellidos
    usuario.correo = correo
    usuario.fecha_nacimiento = fecha_nacimiento
    usuario.id_rol = id_rol
    usuario.save(update_fields=['nombre', 'apellidos', 'correo', 'fecha_nacimiento', 'id_rol', 'fecha_actualizacion'])
    registrar_auditoria(
        entidad='usuarios',
        accion='ACTUALIZAR',
        id_usuario=usuario,
        valores_antes=valores_antes,
        valores_despues={'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': id_rol.nombre},
        ip=request,
    )
    return usuario


def eliminar_usuario(usuario: Usuarios, request=None) -> None:
    valores_antes = {'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': usuario.id_rol.nombre}
    registrar_auditoria(
        entidad='usuarios',
        accion='ELIMINAR',
        id_usuario=usuario,
        valores_antes=valores_antes,
        valores_despues=None,
        ip=request,
    )
    usuario.delete()


def aprobar_usuario(usuario: Usuarios, request=None) -> Usuarios:
    valores_antes={'estatus': usuario.estatus}
    usuario.estatus = 'activo'
    usuario.fecha_actualizacion = timezone.now()
    usuario.save(update_fields=['estatus', 'fecha_actualizacion'])
    registrar_auditoria(
        entidad='usuarios',
        accion='APROBAR',
        id_usuario=usuario,
        valores_antes=valores_antes,
        valores_despues={'estatus': 'activo'},
        ip=request,
    )
    return usuario


def desactivar_usuario(usuario: Usuarios, request=None) -> Usuarios:
    valores_antes={'estatus': usuario.estatus}
    usuario.estatus = 'inactivo'
    usuario.fecha_actualizacion = timezone.now()
    usuario.save(update_fields=['estatus', 'fecha_actualizacion'])
    registrar_auditoria(
        entidad='usuarios',
        accion='DESACTIVAR',
        id_usuario=usuario,
        valores_antes=valores_antes,
        valores_despues={'estatus': 'inactivo'},
        ip=request,
    )
    return usuario
