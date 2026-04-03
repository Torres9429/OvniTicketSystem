from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Usuarios


def crear_usuario(nombre: str, correo: str, contrasena: str, fecha_nacimiento, id_rol, apellidos: str =None, estatus: str = 'activo') -> Usuarios:
    return Usuarios.objects.create(
        nombre=nombre,
        apellidos=apellidos,
        correo=correo,
        contrasena=make_password(contrasena),
        fecha_nacimiento=fecha_nacimiento,
        estatus=estatus,
        fecha_creacion=timezone.now(),
        fecha_actualizacion=timezone.now(),
        id_rol_id=id_rol.pk,
    )


def actualizar_usuario(usuario: Usuarios, nombre: str, correo: str, fecha_nacimiento, id_rol, apellidos: str = None) -> Usuarios:
    usuario.nombre = nombre
    usuario.apellidos = apellidos
    usuario.correo = correo
    usuario.fecha_nacimiento = fecha_nacimiento
    usuario.id_rol = id_rol
    usuario.save(update_fields=['nombre', 'apellidos', 'correo', 'fecha_nacimiento', 'id_rol', 'fecha_actualizacion'])
    return usuario


def eliminar_usuario(usuario: Usuarios) -> None:
    usuario.delete()


def aprobar_usuario(usuario: Usuarios) -> Usuarios:
    usuario.estatus = 'activo'
    usuario.fecha_actualizacion = timezone.now()
    usuario.save(update_fields=['estatus', 'fecha_actualizacion'])
    return usuario


def desactivar_usuario(usuario: Usuarios) -> Usuarios:
    usuario.estatus = 'inactivo'
    usuario.fecha_actualizacion = timezone.now()
    usuario.save(update_fields=['estatus', 'fecha_actualizacion'])
    return usuario
