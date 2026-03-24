from .models import Lugares


def crear_lugar(nombre: str, ciudad: str, pais: str, direccion: str, estatus: str, id_dueno, fecha_creacion, fecha_actualizacion):
    return Lugares.objects.create(
        nombre=nombre,
        ciudad=ciudad,
        pais=pais,
        direccion=direccion,
        estatus=estatus,
        id_dueno_id=id_dueno.pk,
        fecha_creacion=fecha_creacion,
        fecha_actualizacion=fecha_actualizacion
    )


def actualizar_lugar(lugar: Lugares, nombre: str, ciudad: str, pais: str, direccion: str, estatus: str, id_dueno) -> Lugares:
    lugar.nombre = nombre
    lugar.ciudad = ciudad
    lugar.pais = pais
    lugar.direccion = direccion
    lugar.estatus = estatus
    lugar.id_dueno = id_dueno
    lugar.save(update_fields=['nombre', 'ciudad', 'pais', 'direccion', 'estatus', 'id_dueno', 'fecha_actualizacion'])
    return lugar


def desactivar_lugar(lugar: Lugares) -> Lugares:
    lugar.estatus = 'INHABILITADO'
    lugar.save(update_fields=['estatus', 'fecha_actualizacion'])
    return lugar


def activar_lugar(lugar: Lugares) -> Lugares:
    lugar.estatus = 'PUBLICADO'
    lugar.save(update_fields=['estatus', 'fecha_actualizacion'])
    return lugar
