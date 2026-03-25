from .models import PrecioZonaEvento

def crear_precio_zona_evento(precio: float, fecha_creacion, fecha_modificacion, id_zona: int, id_evento: int):
    return PrecioZonaEvento.objects.create(
        precio=precio, 
        fecha_creacion=fecha_creacion, 
        fecha_modificacion=fecha_modificacion, 
        id_zona_id=id_zona, 
        id_evento_id=id_evento
        )

def actualizar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento, precio: float, fecha_modificacion, id_zona: int, id_evento: int):
    precio_zona_evento.precio = precio
    precio_zona_evento.fecha_modificacion = fecha_modificacion
    precio_zona_evento.id_zona_id = id_zona
    precio_zona_evento.id_evento_id = id_evento
    precio_zona_evento.save(update_fields=['precio', 'fecha_modificacion', 'id_zona', 'id_evento'])
    return precio_zona_evento

def eliminar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento):
    precio_zona_evento.delete()