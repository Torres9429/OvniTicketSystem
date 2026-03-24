from .models import Roles


def crear_rol(nombre: str, fecha_creacion, fecha_actualizacion) -> Roles:
    return Roles.objects.create(
        nombre=nombre,
        fecha_creacion=fecha_creacion,
        fecha_actualizacion=fecha_actualizacion,
    )


def actualizar_rol(rol: Roles, nombre: str) -> Roles:
    rol.nombre = nombre
    rol.save(update_fields=['nombre', 'fecha_actualizacion'])
    return rol


def eliminar_rol(rol: Roles) -> None:
    rol.delete()
