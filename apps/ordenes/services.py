from .models import Ordenes


def crear_orden(total: float, estatus: str, fecha_creacion, fecha_actualizacion, id_evento, id_usuario) -> Ordenes:
    return Ordenes.objects.create(
        total=total,
        estatus=estatus,
        fecha_creacion=fecha_creacion,
        fecha_actualizacion=fecha_actualizacion,
        id_evento_id=id_evento.pk,
        id_usuario_id=id_usuario.pk,
    )


def actualizar_orden(orden: Ordenes, total: float, estatus: str, id_evento, id_usuario) -> Ordenes:
    orden.total = total
    orden.estatus = estatus
    orden.id_evento = id_evento
    orden.id_usuario = id_usuario
    orden.save(update_fields=['total', 'estatus', 'id_evento', 'id_usuario', 'fecha_actualizacion'])
    return orden


def eliminar_orden(orden: Ordenes) -> None:
    orden.delete()
