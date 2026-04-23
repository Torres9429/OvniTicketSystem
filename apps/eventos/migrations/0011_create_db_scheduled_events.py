from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0010_alter_eventos_descripcion_alter_eventos_foto'),
        ('asientos', '0002_asientos_id_grid_cell_estadoasientoevento'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DROP EVENT IF EXISTS ev_cerrar_eventos_expirados;
                CREATE EVENT ev_cerrar_eventos_expirados
                ON SCHEDULE EVERY 1 HOUR
                STARTS CURRENT_TIMESTAMP + INTERVAL 1 MINUTE
                ON COMPLETION PRESERVE
                ENABLE
                DO
                    UPDATE eventos
                    SET
                        estatus = 'FINALIZADO',
                        fecha_actualizacion = UTC_TIMESTAMP()
                    WHERE estatus = 'PUBLICADO'
                      AND fecha_fin < UTC_TIMESTAMP();

                DROP EVENT IF EXISTS ev_liberar_retenciones_expiradas;
                CREATE EVENT ev_liberar_retenciones_expiradas
                ON SCHEDULE EVERY 1 MINUTE
                STARTS CURRENT_TIMESTAMP + INTERVAL 1 MINUTE
                ON COMPLETION PRESERVE
                ENABLE
                DO
                    UPDATE estado_asiento_evento
                    SET
                        estado = 'disponible',
                        retenido_por = NULL,
                        retenido_hasta = NULL
                    WHERE estado = 'retenido'
                      AND retenido_hasta IS NOT NULL
                      AND retenido_hasta < UTC_TIMESTAMP();
            ''',
            reverse_sql='''
                DROP EVENT IF EXISTS ev_liberar_retenciones_expiradas;
                DROP EVENT IF EXISTS ev_cerrar_eventos_expirados;
            ''',
        ),
    ]
