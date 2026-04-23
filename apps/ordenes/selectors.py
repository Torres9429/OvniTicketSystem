from django.db import connection
from django.db.models import Case, IntegerField, When

from apps.ordenes.models import Ordenes

_ORDEN_RECIENTE = ('-fecha_creacion', '-id_orden')


def get_all_ordenes():
    return Ordenes.objects.all().order_by(*_ORDEN_RECIENTE)


def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _obtener_ids_ordenes(sql: str, params: tuple | None = None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def _queryset_ordenes_por_ids(ids_ordenes: list[int]):
    if not ids_ordenes:
        return Ordenes.objects.none()

    orden_personalizado = Case(
        *[When(id_orden=orden_id, then=pos) for pos, orden_id in enumerate(ids_ordenes)],
        output_field=IntegerField(),
    )
    return Ordenes.objects.filter(id_orden__in=ids_ordenes).order_by(orden_personalizado)


def get_ordenes_por_evento(id_evento: int):
    ids_ordenes = _obtener_ids_ordenes(
        """
        SELECT id_orden
        FROM v_ordenes_lookup
        WHERE id_evento = %s
        ORDER BY fecha_creacion DESC, id_orden DESC
        """,
        (id_evento,),
    )
    return _queryset_ordenes_por_ids(ids_ordenes)


def get_ordenes_por_usuario(id_usuario: int):
    ids_ordenes = _obtener_ids_ordenes(
        """
        SELECT id_orden
        FROM v_ordenes_lookup
        WHERE id_usuario = %s
        ORDER BY fecha_creacion DESC, id_orden DESC
        """,
        (id_usuario,),
    )
    return _queryset_ordenes_por_ids(ids_ordenes)


def get_dashboard_ventas_por_organizador(id_usuario: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id_evento,
                nombre,
                fecha_inicio,
                estatus,
                boletos_vendidos,
                asientos_totales,
                CASE
                    WHEN asientos_totales > 0
                        THEN ROUND((boletos_vendidos * 100.0) / asientos_totales, 1)
                    ELSE 0.0
                END AS ocupacion_pct,
                revenue
            FROM v_dashboard_ventas_evento
            WHERE id_dueno = %s
              AND estatus IN ('PUBLICADO', 'FINALIZADO')
            ORDER BY fecha_inicio DESC, id_evento DESC
            """,
            (id_usuario,),
        )
        eventos = _dictfetchall(cursor)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(revenue), 0) AS total_vendido,
                COALESCE(SUM(boletos_vendidos), 0) AS boletos_vendidos,
                COALESCE(SUM(ordenes_pagadas), 0) AS ordenes_pagadas,
                COALESCE(SUM(ordenes_pendientes), 0) AS ordenes_pendientes,
                COUNT(*) AS eventos_totales,
                SUM(CASE WHEN boletos_vendidos > 0 THEN 1 ELSE 0 END) AS eventos_con_ventas
            FROM v_dashboard_ventas_evento
            WHERE id_dueno = %s
              AND estatus IN ('PUBLICADO', 'FINALIZADO')
            """,
            (id_usuario,),
        )
        resumen = _dictfetchall(cursor)[0]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id_orden,
                fecha_creacion,
                id_evento,
                nombre_evento,
                total,
                estatus,
                comprador
            FROM v_ordenes_recientes_organizador
            WHERE id_dueno = %s
              AND estatus = %s
            ORDER BY fecha_creacion DESC, id_orden DESC
            LIMIT 10
            """,
            (id_usuario, Ordenes.ESTATUS_PAGADO),
        )
        ordenes_recientes = _dictfetchall(cursor)

    return {
        "resumen": resumen,
        "eventos": eventos,
        "ordenes_recientes": ordenes_recientes,
    }
