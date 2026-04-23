from django.db import connection
from django.utils import timezone
from .models import Eventos
from apps.auditoria_logs.services import registrar_auditoria
import logging

logger = logging.getLogger(__name__)


def actualizar_estadisticas_eventos():
    """
    Actualiza las estadísticas de todos los eventos:
    - boletos_vendidos: cantidad de tickets vendidos
    - ingresos_totales: suma de precios de tickets
    - ocupacion_pct: porcentaje de asientos ocupados
    
    Se ejecuta automáticamente cada día via evento MySQL.
    Puede ejecutarse manualmente para testing.
    
    Returns:
        dict: {"actualizado": int, "errores": int}
    """
    with connection.cursor() as cursor:
        cursor.execute('''
            UPDATE eventos e
            SET 
                e.boletos_vendidos = (
                    SELECT COUNT(*)
                    FROM tickets t
                    WHERE t.id_evento = e.id_evento
                ),
                e.ingresos_totales = (
                    SELECT COALESCE(SUM(t.precio), 0)
                    FROM tickets t
                    WHERE t.id_evento = e.id_evento
                ),
                e.ocupacion_pct = (
                    CASE
                        WHEN (SELECT COUNT(*) FROM grid_cells gc 
                              WHERE gc.id_layout = e.id_version 
                              AND gc.tipo = 'ZONA DE ASIENTOS') > 0
                        THEN ROUND(
                            (SELECT COUNT(*) FROM tickets t WHERE t.id_evento = e.id_evento) * 100.0 /
                            (SELECT COUNT(*) FROM grid_cells gc 
                             WHERE gc.id_layout = e.id_version 
                             AND gc.tipo = 'ZONA DE ASIENTOS'),
                            1
                        )
                        ELSE 0.0
                    END
                )
            WHERE e.estatus IN ('PUBLICADO', 'FINALIZADO')
        ''')
        
        actualizados = cursor.rowcount
        logger.info(
            f"Estadísticas de eventos actualizadas: {actualizados} eventos"
        )
        
        return {
            "actualizado": actualizados,
            "errores": 0,
        }


def crear_evento(nombre, descripcion, fecha_inicio, fecha_fin, tiempo_espera, foto, estatus, id_lugar, id_version, id_usuario=None, request=None):
    """Crea un nuevo evento."""
    ahora = timezone.now()
    evento = Eventos.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tiempo_espera=tiempo_espera,
        foto=foto,
        estatus=estatus,
        id_lugar_id=id_lugar,
        id_version_id=id_version,
        fecha_creacion=ahora,
        fecha_actualizacion=ahora,
    )

    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={
                'nombre': evento.nombre,
                'estatus': evento.estatus,
                'fecha_inicio': evento.fecha_inicio.isoformat() if evento.fecha_inicio else None,
            },
            ip=request,
        )

    logger.info(f"Evento creado: evento={evento.pk} nombre={evento.nombre}")
    return evento


def actualizar_evento(evento, nombre=None, descripcion=None, fecha_inicio=None, fecha_fin=None, tiempo_espera=None, foto=None, estatus=None, id_lugar=None, id_version=None, id_usuario=None, request=None):
    """Actualiza un evento existente."""
    valores_antes = {
        'nombre': evento.nombre,
        'estatus': evento.estatus,
        'fecha_inicio': evento.fecha_inicio.isoformat() if evento.fecha_inicio else None,
    }

    if nombre is not None:
        evento.nombre = nombre
    if descripcion is not None:
        evento.descripcion = descripcion
    if fecha_inicio is not None:
        evento.fecha_inicio = fecha_inicio
    if fecha_fin is not None:
        evento.fecha_fin = fecha_fin
    if tiempo_espera is not None:
        evento.tiempo_espera = tiempo_espera
    if foto is not None:
        evento.foto = foto
    if estatus is not None:
        evento.estatus = estatus
    if id_lugar is not None:
        evento.id_lugar_id = id_lugar
    if id_version is not None:
        evento.id_version_id = id_version

    evento.fecha_actualizacion = timezone.now()
    evento.save()

    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={
                'nombre': evento.nombre,
                'estatus': evento.estatus,
                'fecha_inicio': evento.fecha_inicio.isoformat() if evento.fecha_inicio else None,
            },
            ip=request,
        )

    logger.info(f"Evento actualizado: evento={evento.pk}")
    return evento


def activar_evento(evento, id_usuario=None, request=None):
    """Activa un evento (cambia estatus a PUBLICADO)."""
    evento.estatus = Eventos.ESTATUS_PUBLICADO
    evento.fecha_actualizacion = timezone.now()
    evento.save()

    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ACTIVAR',
            id_usuario=id_usuario,
            valores_antes={'estatus': 'BORRADOR'},
            valores_despues={'estatus': evento.estatus},
            ip=request,
        )

    logger.info(f"Evento activado: evento={evento.pk}")
    return evento


def desactivar_evento(evento, id_usuario=None, request=None):
    """Desactiva un evento (cambia estatus a CANCELADO)."""
    evento.estatus = Eventos.ESTATUS_CANCELADO
    evento.fecha_actualizacion = timezone.now()
    evento.save()

    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='DESACTIVAR',
            id_usuario=id_usuario,
            valores_antes={'estatus': evento.estatus},
            valores_despues={'estatus': Eventos.ESTATUS_CANCELADO},
            ip=request,
        )

    logger.info(f"Evento desactivado: evento={evento.pk}")
    return evento


def eliminar_evento(evento, id_usuario=None, request=None):
    """Elimina un evento."""
    evento_id = evento.pk
    evento_nombre = evento.nombre

    if id_usuario:
        registrar_auditoria(
            entidad='eventos',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes={'nombre': evento.nombre},
            valores_despues=None,
            ip=request,
        )

    evento.delete()
    logger.info(f"Evento eliminado: evento={evento_id} nombre={evento_nombre}")
    return True
