from .models import Zonas

def crear_zona(nombre: str, color: str, fecha_creacion, fecha_modificacion, id_layout: int):
    return Zonas.objects.create(
        nombre=nombre, 
        color=color, 
        fecha_creacion=fecha_creacion, 
        fecha_modificacion=fecha_modificacion, 
        id_layout=id_layout.pk
        )

def actualizar_zona(zona: Zonas, nombre: str, color: str, fecha_modificacion, id_layout: int):
    zona.nombre = nombre
    zona.color = color
    zona.fecha_modificacion = fecha_modificacion
    zona.id_layout_id = id_layout.pk
    zona.save(update_fields=['nombre', 'color', 'fecha_modificacion', 'id_layout'])
    return zona

def eliminar_zona(zona: Zonas):
    zona.delete()