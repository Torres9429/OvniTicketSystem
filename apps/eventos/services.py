
from django.utils import timezone
from .models import Eventos
from apps.auditoria_logs.services import registrar_auditoria

def crear_evento(nombre: str, descripcion: str, fecha_inicio, fecha_fin, tiempo_espera: int, foto: str, id_lugar, id_version, estatus: str, id_usuario, request=None) -> Eventos:
    from apps.precio_zona_evento.services import sincronizar_precios_zona_evento

    now = timezone.now()
    evento = Eventos.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tiempo_espera=tiempo_espera,
        foto=foto,
        id_lugar_id=id_lugar.pk,
        id_version_id=id_version.pk,
        estatus = estatus,
        fecha_creacion = now,
        fecha_actualizacion = now
    )
    # Copia automáticamente los precios de las zonas del layout a
    # PrecioZonaEvento para que la compra funcione sin configuración manual.
    sincronizar_precios_zona_evento(evento, id_usuario=id_usuario, request=request)
    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'nombre': evento.nombre, 'descripcion': evento.descripcion, 'fecha_inicio': str(evento.fecha_inicio), 'fecha_fin': str(evento.fecha_fin), 'tiempo_espera': evento.tiempo_espera, 'foto': evento.foto, 'id_lugar': id_lugar.nombre, 'id_version': id_version.version, 'estatus': evento.estatus},
            ip=request,
        )
    return evento

def actualizar_evento(evento: Eventos, nombre: str, descripcion: str, fecha_inicio, fecha_fin, tiempo_espera: int, foto: str, estatus: str, id_lugar: int, id_version: int, id_usuario=None, request=None) -> Eventos:
    from apps.precio_zona_evento.services import sincronizar_precios_zona_evento

    valores_antes = {'nombre': evento.nombre, 'descripcion': evento.descripcion, 'fecha_inicio': str(evento.fecha_inicio), 'fecha_fin': str(evento.fecha_fin), 'tiempo_espera': evento.tiempo_espera, 'foto': evento.foto, 'id_lugar': evento.id_lugar.pk, 'id_version': evento.id_version.pk, 'estatus': evento.estatus}
    evento.nombre = nombre
    evento.descripcion = descripcion
    evento.fecha_inicio = fecha_inicio
    evento.fecha_fin = fecha_fin
    evento.tiempo_espera = tiempo_espera
    evento.foto = foto
    evento.estatus = estatus
    evento.id_lugar = id_lugar
    evento.id_version = id_version
    evento.save( update_fields=['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'tiempo_espera', 'foto', 'estatus', 'id_lugar', 'id_version', 'fecha_actualizacion'])
    # Si el organizador cambió el layout o actualizó precios en las zonas del
    # layout, re-sincroniza los PrecioZonaEvento faltantes (no sobrescribe
    # precios ya establecidos por evento).
    sincronizar_precios_zona_evento(evento, id_usuario=id_usuario, request=request)
    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'nombre': evento.nombre, 'descripcion': evento.descripcion, 'fecha_inicio': str(evento.fecha_inicio), 'fecha_fin': str(evento.fecha_fin), 'tiempo_espera': evento.tiempo_espera, 'foto': evento.foto, 'id_lugar': id_lugar.pk, 'id_version': id_version.pk, 'estatus': evento.estatus},
            ip=request,
        )
    return evento

def eliminar_evento(evento: Eventos, id_usuario=None, request=None) -> None:
    valores_antes = {'nombre': evento.nombre, 'descripcion': evento.descripcion, 'fecha_inicio': str(evento.fecha_inicio), 'fecha_fin': str(evento.fecha_fin), 'tiempo_espera': evento.tiempo_espera, 'foto': evento.foto, 'id_lugar': evento.id_lugar.pk, 'id_version': evento.id_version.pk, 'estatus': evento.estatus}
    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    evento.delete()

def desactivar_evento(evento: Eventos, id_usuario=None, request=None) -> Eventos:
    valores_antes = {'estatus': evento.estatus, 'fecha_actualizacion': str(evento.fecha_actualizacion)}
    evento.estatus = Eventos.ESTATUS_CANCELADO
    evento.fecha_actualizacion = timezone.now()
    evento.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='DESACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': evento.estatus, 'fecha_actualizacion': str(evento.fecha_actualizacion)},
            ip=request,
        )
    return evento

def activar_evento(evento: Eventos, id_usuario=None, request=None) -> Eventos:
    valores_antes = {'estatus': evento.estatus, 'fecha_actualizacion': str(evento.fecha_actualizacion)}
    evento.estatus = Eventos.ESTATUS_PUBLICADO
    evento.fecha_actualizacion = timezone.now()
    evento.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': evento.estatus, 'fecha_actualizacion': str(evento.fecha_actualizacion)},
            ip=request,
        )
    return evento

