from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0013_eventos_estadisticas'),
        ('tickets', '0003_tickets_fecha_actualizacion_tickets_fecha_creacion'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DROP EVENT IF EXISTS evento_actualizar_estadisticas_diario;
                
                CREATE EVENT evento_actualizar_estadisticas_diario
                ON SCHEDULE EVERY 1 DAY
                STARTS CURRENT_TIMESTAMP
                DO
                BEGIN
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
                    WHERE e.estatus IN ('PUBLICADO', 'FINALIZADO');
                END;
            ''',
            reverse_sql='''
                DROP EVENT IF EXISTS evento_actualizar_estadisticas_diario;
            ''',
        ),
    ]
