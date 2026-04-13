from django.utils import timezone
from .models import PrecioZonaEvento
from apps.auditoria_logs.services import registrar_auditoria

def crear_precio_zona_evento(precio: float, id_zona: int, id_evento: int, id_usuario=None, request=None):
    now = timezone.now()
    precio_zona_evento = PrecioZonaEvento.objects.create(
        precio=precio,
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_zona=id_zona,
        id_evento=id_evento
    )
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'precio': precio_zona_evento.precio, 'fecha_creacion': str(precio_zona_evento.fecha_creacion), 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk},
            ip=request,
        )
    return precio_zona_evento

def actualizar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento, precio: float, id_zona: int, id_evento: int, id_usuario=None, request=None):
    now = timezone.now()
    valores_antes = {'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona_id, 'id_evento': precio_zona_evento.id_evento_id}
    precio_zona_evento.precio = precio
    precio_zona_evento.fecha_actualizacion= now
    precio_zona_evento.id_zona_id = id_zona.pk
    precio_zona_evento.id_evento_id = id_evento.pk
    precio_zona_evento.save(update_fields=['precio', 'fecha_actualizacion', 'id_zona', 'id_evento'])
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk},
            ip=request,
        )
    return precio_zona_evento

def sincronizar_precios_zona_evento(evento, id_usuario=None, request=None):
    """Garantiza que existan filas de PrecioZonaEvento para cada zona del
    layout del evento, usando `zonas.precio` como fuente de verdad.

    - Si una zona del layout NO tiene PZE para este evento, la crea.
    - Si una zona ya tiene PZE y el precio difiere de `zona.precio`, lo
      actualiza. El precio del layout es la única fuente de verdad — no hay
      override por evento en el MVP actual.
    - Llamar esta función es idempotente.

    Se llama desde `apps/eventos/services.py::crear_evento` y
    `actualizar_evento`, y también como fallback defensivo en
    `apps/asientos/services.py::inicializar_estado_asientos`.
    """
    from apps.zonas.models import Zonas

    zonas = list(Zonas.objects.filter(id_layout=evento.id_version_id))
    if not zonas:
        return {"creados": 0, "actualizados": 0}

    existentes_map = {
        pze.id_zona_id: pze
        for pze in PrecioZonaEvento.objects.filter(
            id_evento=evento, id_zona__in=[z.pk for z in zonas]
        )
    }

    now = timezone.now()
    creados = 0
    actualizados = 0
    for zona in zonas:
        precio_base = float(zona.precio or 0)
        pze = existentes_map.get(zona.pk)
        if pze is None:
            PrecioZonaEvento.objects.create(
                precio=precio_base,
                fecha_creacion=now,
                fecha_actualizacion=now,
                id_zona=zona,
                id_evento=evento,
            )
            creados += 1
        elif abs(float(pze.precio or 0) - precio_base) > 1e-9:
            pze.precio = precio_base
            pze.fecha_actualizacion = now
            pze.save(update_fields=['precio', 'fecha_actualizacion'])
            actualizados += 1

    if (creados or actualizados) and id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='SINCRONIZAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={
                'id_evento': evento.pk,
                'creados': creados,
                'actualizados': actualizados,
            },
            ip=request,
        )
    return {"creados": creados, "actualizados": actualizados}


def propagar_precio_zona_a_eventos(zona, id_usuario=None, request=None):
    """Cuando el organizador cambia el precio base de una zona (desde el
    editor de layout), propaga ese precio a todos los eventos que usan
    ese layout.

    Crea PZE faltantes y actualiza existentes al nuevo precio.
    Devuelve el total de eventos tocados.
    """
    from apps.eventos.models import Eventos

    eventos = Eventos.objects.filter(id_version=zona.id_layout_id)
    tocados = 0
    for evento in eventos:
        resultado = sincronizar_precios_zona_evento(
            evento, id_usuario=id_usuario, request=request
        )
        if resultado["creados"] or resultado["actualizados"]:
            tocados += 1
    return tocados


def eliminar_precio_zona_evento(precio_zona_evento: PrecioZonaEvento, id_usuario=None, request=None):
    valores_antes = {'precio': precio_zona_evento.precio, 'fecha_actualizacion': str(precio_zona_evento.fecha_actualizacion), 'id_zona': precio_zona_evento.id_zona.pk, 'id_evento': precio_zona_evento.id_evento.pk}
    if id_usuario:
        registrar_auditoria(
            entidad='precio_zona_evento',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    precio_zona_evento.delete()