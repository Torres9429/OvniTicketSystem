from django.db import migrations


def _crear_indices_busqueda(apps, schema_editor):
    # MySQL no soporta CREATE INDEX IF NOT EXISTS en todas las versiones.
    connection = schema_editor.connection
    indices = [
        ("ordenes", "idx_ordenes_evento_estatus_fecha", "CREATE INDEX idx_ordenes_evento_estatus_fecha ON ordenes (id_evento, estatus, fecha_creacion)"),
        ("ordenes", "idx_ordenes_usuario_fecha", "CREATE INDEX idx_ordenes_usuario_fecha ON ordenes (id_usuario, fecha_creacion)"),
        ("tickets", "idx_tickets_orden_evento", "CREATE INDEX idx_tickets_orden_evento ON tickets (id_orden, id_evento)"),
        ("eventos", "idx_eventos_estatus_fechas", "CREATE INDEX idx_eventos_estatus_fechas ON eventos (estatus, fecha_inicio, fecha_fin)"),
        ("grid_cells", "idx_grid_cells_layout_tipo", "CREATE INDEX idx_grid_cells_layout_tipo ON grid_cells (id_layout, tipo)"),
        ("estado_asiento_evento", "idx_estado_asiento_evento_busqueda", "CREATE INDEX idx_estado_asiento_evento_busqueda ON estado_asiento_evento (id_evento, estado, retenido_hasta)"),
    ]

    with connection.cursor() as cursor:
        for table_name, index_name, create_sql in indices:
            cursor.execute(
                """
                SELECT COUNT(1)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                  AND index_name = %s
                """,
                [table_name, index_name],
            )
            exists = cursor.fetchone()[0] > 0
            if not exists:
                cursor.execute(create_sql)


def _eliminar_indices_busqueda(apps, schema_editor):
    connection = schema_editor.connection
    indices = [
        ("ordenes", "idx_ordenes_evento_estatus_fecha"),
        ("ordenes", "idx_ordenes_usuario_fecha"),
        ("tickets", "idx_tickets_orden_evento"),
        ("eventos", "idx_eventos_estatus_fechas"),
        ("grid_cells", "idx_grid_cells_layout_tipo"),
        ("estado_asiento_evento", "idx_estado_asiento_evento_busqueda"),
    ]

    with connection.cursor() as cursor:
        for table_name, index_name in indices:
            cursor.execute(
                """
                SELECT COUNT(1)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                  AND index_name = %s
                """,
                [table_name, index_name],
            )
            exists = cursor.fetchone()[0] > 0
            if exists:
                cursor.execute(f"DROP INDEX {index_name} ON {table_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('ordenes', '0003_ordenes_operation_id'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DROP VIEW IF EXISTS v_eventos_publicados;
                CREATE VIEW v_eventos_publicados AS
                SELECT
                    e.id_evento,
                    e.nombre,
                    e.descripcion,
                    e.fecha_inicio,
                    e.fecha_fin,
                    e.tiempo_espera,
                    e.foto,
                    e.estatus,
                    e.fecha_creacion,
                    e.fecha_actualizacion,
                    e.id_lugar,
                    e.id_version
                FROM eventos e
                WHERE e.estatus = 'PUBLICADO';

                DROP VIEW IF EXISTS v_eventos_por_dueno;
                CREATE VIEW v_eventos_por_dueno AS
                SELECT
                    e.id_evento,
                    l.id_dueno
                FROM eventos e
                INNER JOIN lugares l ON l.id_lugar = e.id_lugar;

                DROP VIEW IF EXISTS v_ordenes_lookup;
                CREATE VIEW v_ordenes_lookup AS
                SELECT
                    o.id_orden,
                    o.total,
                    o.estatus,
                    o.fecha_creacion,
                    o.fecha_actualizacion,
                    o.id_evento,
                    o.id_usuario,
                    o.operation_id,
                    e.nombre AS nombre_evento,
                    l.id_dueno,
                    u.correo AS correo_usuario
                FROM ordenes o
                INNER JOIN eventos e ON e.id_evento = o.id_evento
                INNER JOIN lugares l ON l.id_lugar = e.id_lugar
                LEFT JOIN usuarios u ON u.id_usuario = o.id_usuario;

                DROP VIEW IF EXISTS v_tickets_lookup;
                CREATE VIEW v_tickets_lookup AS
                SELECT
                    t.id_ticket,
                    t.precio,
                    t.fecha_creacion,
                    t.fecha_actualizacion,
                    t.id_orden,
                    t.id_asiento,
                    t.id_grid_cell,
                    t.id_evento
                FROM tickets t;

                DROP VIEW IF EXISTS v_dashboard_ventas_evento;
                CREATE VIEW v_dashboard_ventas_evento AS
                SELECT
                    e.id_evento,
                    e.nombre,
                    e.fecha_inicio,
                    e.estatus,
                    l.id_dueno,
                    COALESCE(cap.asientos_totales, 0) AS asientos_totales,
                    COALESCE(ord.revenue, 0) AS revenue,
                    COALESCE(ord.ordenes_pagadas, 0) AS ordenes_pagadas,
                    COALESCE(ord.ordenes_pendientes, 0) AS ordenes_pendientes,
                    COALESCE(tk.boletos_vendidos, 0) AS boletos_vendidos
                FROM eventos e
                INNER JOIN lugares l ON l.id_lugar = e.id_lugar
                LEFT JOIN (
                    SELECT
                        o.id_evento,
                        SUM(CASE WHEN o.estatus = 'pagado' THEN o.total ELSE 0 END) AS revenue,
                        SUM(CASE WHEN o.estatus = 'pagado' THEN 1 ELSE 0 END) AS ordenes_pagadas,
                        SUM(CASE WHEN o.estatus = 'pendiente' THEN 1 ELSE 0 END) AS ordenes_pendientes
                    FROM ordenes o
                    GROUP BY o.id_evento
                ) ord ON ord.id_evento = e.id_evento
                LEFT JOIN (
                    SELECT
                        o.id_evento,
                        COUNT(t.id_ticket) AS boletos_vendidos
                    FROM ordenes o
                    INNER JOIN tickets t ON t.id_orden = o.id_orden
                    WHERE o.estatus = 'pagado'
                    GROUP BY o.id_evento
                ) tk ON tk.id_evento = e.id_evento
                LEFT JOIN (
                    SELECT
                        gc.id_layout,
                        COUNT(*) AS asientos_totales
                    FROM grid_cells gc
                    WHERE gc.tipo = 'ZONA DE ASIENTOS'
                    GROUP BY gc.id_layout
                ) cap ON cap.id_layout = e.id_version;

                DROP VIEW IF EXISTS v_ordenes_recientes_organizador;
                CREATE VIEW v_ordenes_recientes_organizador AS
                SELECT
                    o.id_orden,
                    o.fecha_creacion,
                    o.id_evento,
                    e.nombre AS nombre_evento,
                    o.total,
                    o.estatus,
                    u.correo AS comprador,
                    l.id_dueno
                FROM ordenes o
                INNER JOIN eventos e ON e.id_evento = o.id_evento
                INNER JOIN lugares l ON l.id_lugar = e.id_lugar
                LEFT JOIN usuarios u ON u.id_usuario = o.id_usuario;

            ''',
            reverse_sql='''
                DROP VIEW IF EXISTS v_ordenes_recientes_organizador;
                DROP VIEW IF EXISTS v_dashboard_ventas_evento;
                DROP VIEW IF EXISTS v_tickets_lookup;
                DROP VIEW IF EXISTS v_ordenes_lookup;
                DROP VIEW IF EXISTS v_eventos_por_dueno;
                DROP VIEW IF EXISTS v_eventos_publicados;
            ''',
        ),
        migrations.RunPython(
            _crear_indices_busqueda,
            reverse_code=_eliminar_indices_busqueda,
        ),
    ]
