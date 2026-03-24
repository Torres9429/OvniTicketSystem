from apps.usuarios.models import Usuarios


def get_all_usuarios():
    return Usuarios.objects.all()


def get_usuarios_por_rol(id_rol: int):
    return Usuarios.objects.filter(id_rol=id_rol)
