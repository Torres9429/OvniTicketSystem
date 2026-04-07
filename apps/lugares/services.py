from django.utils import timezone
from .models import Lugares
from apps.auditoria_logs.services import registrar_auditoria


def crear_lugar(nombre: str, ciudad: str, pais: str, direccion: str, estatus: str, id_dueno, request=None) -> Lugares:
    now = timezone.now()
    lugar = Lugares.objects.create(
        nombre=nombre,
        ciudad=ciudad,
        pais=pais,
        direccion=direccion,
        estatus=estatus,
        id_dueno_id=id_dueno.pk,
        fecha_creacion=now,
        fecha_actualizacion=now
    )
    registrar_auditoria(
        entidad='lugares',
        accion='CREAR',
        id_usuario=id_dueno,
        valores_antes=None,
        valores_despues={'nombre': lugar.nombre, 'ciudad': lugar.ciudad, 'pais': lugar.pais, 'direccion': lugar.direccion, 'estatus': lugar.estatus, 'id_dueno': id_dueno.nombre},
        ip=request,
    )
    return lugar


def actualizar_lugar(lugar: Lugares, nombre: str, ciudad: str, pais: str, direccion: str, estatus: str, id_dueno, request=None) -> Lugares:
    valores_antes = {'nombre': lugar.nombre, 'ciudad': lugar.ciudad, 'pais': lugar.pais, 'direccion': lugar.direccion, 'estatus': lugar.estatus, 'id_dueno': lugar.id_dueno.nombre}
    lugar.nombre = nombre
    lugar.ciudad = ciudad
    lugar.pais = pais
    lugar.direccion = direccion
    lugar.estatus = estatus
    lugar.id_dueno = id_dueno
    lugar.save(update_fields=['nombre', 'ciudad', 'pais', 'direccion', 'estatus', 'id_dueno', 'fecha_actualizacion'])
    registrar_auditoria(
        entidad='lugares',
        accion='ACTUALIZAR',
        id_usuario=id_dueno,
        valores_antes=valores_antes,
        valores_despues={'nombre': lugar.nombre, 'ciudad': lugar.ciudad, 'pais': lugar.pais, 'direccion': lugar.direccion, 'estatus': lugar.estatus, 'id_dueno': id_dueno.nombre},
        ip=request,
    )
    return lugar


def desactivar_lugar(lugar: Lugares, id_usuario=None, request=None) -> Lugares:
    valores_antes = {'estatus': lugar.estatus, 'fecha_actualizacion': str(lugar.fecha_actualizacion)}
    lugar.estatus = 'INHABILITADO'
    lugar.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='lugares',
            accion='DESACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': 'INHABILITADO', 'fecha_actualizacion': str(lugar.fecha_actualizacion)},
            ip=request,
        )
    return lugar


def activar_lugar(lugar: Lugares, id_usuario=None, request=None) -> Lugares:
    valores_antes = {'estatus': lugar.estatus, 'fecha_actualizacion': str(lugar.fecha_actualizacion)}
    lugar.estatus = 'PUBLICADO'
    lugar.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='lugares',
            accion='ACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': 'PUBLICADO', 'fecha_actualizacion': str(lugar.fecha_actualizacion)},
            ip=request,
        )
    return lugar
