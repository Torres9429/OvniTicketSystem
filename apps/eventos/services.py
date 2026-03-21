from .models import Eventos

def crear_evento(nombre: str, descripcion: str, fecha_inicio, fecha_fin, tiempo_espera: int, foto: str, id_lugar, id_version, estatus: bool, fecha_creacion, fecha_actualizacion):
    return Eventos.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tiempo_espera=tiempo_espera,
        foto=foto,
        id_lugar_id=id_lugar.pk,
        id_version_id=id_version.pk,
        estatus = estatus,
        fecha_creacion = fecha_creacion,
        fecha_actualizacion = fecha_actualizacion
    )

def actualizar_evento(evento: Eventos, nombre: str, descripcion: str, fecha_inicio, fecha_fin, tiempo_espera: int, foto: str, estatus: bool, id_lugar: int, id_version: int) -> Eventos:
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
    return evento

def desactivar_evento(evento: Eventos) -> Eventos:
    evento.estatus = False
    evento.save(update_fields=['estatus', 'fecha_actualizacion'])
    return evento

def activar_evento(evento: Eventos) -> Eventos:
    evento.estatus = True
    evento.save(update_fields=['estatus', 'fecha_actualizacion'])
    return evento