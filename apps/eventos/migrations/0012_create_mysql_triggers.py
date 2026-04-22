from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0011_create_db_scheduled_events'),
        ('asientos', '0002_asientos_id_grid_cell_estadoasientoevento'),
        ('ordenes', '0004_create_search_views'),
        ('tickets', '0003_tickets_fecha_actualizacion_tickets_fecha_creacion'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DROP TRIGGER IF EXISTS trg_eventos_validar_fechas_bi;
                CREATE TRIGGER trg_eventos_validar_fechas_bi
                BEFORE INSERT ON eventos
                FOR EACH ROW
                BEGIN
                    IF NEW.fecha_fin <= NEW.fecha_inicio THEN
                        SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'fecha_fin debe ser mayor que fecha_inicio';
                    END IF;
                END;

                DROP TRIGGER IF EXISTS trg_eventos_validar_fechas_bu;
                CREATE TRIGGER trg_eventos_validar_fechas_bu
                BEFORE UPDATE ON eventos
                FOR EACH ROW
                BEGIN
                    IF NEW.fecha_fin <= NEW.fecha_inicio THEN
                        SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'fecha_fin debe ser mayor que fecha_inicio';
                    END IF;
                END;
            ''',
            reverse_sql='''
                DROP TRIGGER IF EXISTS trg_eventos_validar_fechas_bu;
                DROP TRIGGER IF EXISTS trg_eventos_validar_fechas_bi;
            ''',
        ),
        migrations.RunSQL(
            sql='''
                DROP TRIGGER IF EXISTS trg_tickets_sincronizar_asiento_bi;
                CREATE TRIGGER trg_tickets_sincronizar_asiento_bi
                BEFORE INSERT ON tickets
                FOR EACH ROW
                BEGIN
                    DECLARE v_id_asiento BIGINT DEFAULT NULL;
                    DECLARE v_id_grid_cell BIGINT DEFAULT NULL;

                    IF NEW.id_asiento IS NOT NULL THEN
                        SELECT a.id_grid_cell
                          INTO v_id_grid_cell
                          FROM asientos a
                         WHERE a.id_asiento = NEW.id_asiento
                         LIMIT 1;

                        IF v_id_grid_cell IS NULL THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'El id_asiento no existe o no tiene id_grid_cell asociado';
                        END IF;

                        IF NEW.id_grid_cell IS NULL THEN
                            SET NEW.id_grid_cell = v_id_grid_cell;
                        ELSEIF NEW.id_grid_cell <> v_id_grid_cell THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'id_asiento e id_grid_cell no coinciden';
                        END IF;
                    ELSEIF NEW.id_grid_cell IS NOT NULL THEN
                        SELECT a.id_asiento
                          INTO v_id_asiento
                          FROM asientos a
                         WHERE a.id_grid_cell = NEW.id_grid_cell
                         LIMIT 1;

                        IF v_id_asiento IS NULL THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'No existe un asiento asociado al id_grid_cell del ticket';
                        END IF;

                        SET NEW.id_asiento = v_id_asiento;
                    END IF;
                END;

                DROP TRIGGER IF EXISTS trg_tickets_sincronizar_asiento_bu;
                CREATE TRIGGER trg_tickets_sincronizar_asiento_bu
                BEFORE UPDATE ON tickets
                FOR EACH ROW
                BEGIN
                    DECLARE v_id_asiento BIGINT DEFAULT NULL;
                    DECLARE v_id_grid_cell BIGINT DEFAULT NULL;

                    IF NEW.id_asiento IS NOT NULL THEN
                        SELECT a.id_grid_cell
                          INTO v_id_grid_cell
                          FROM asientos a
                         WHERE a.id_asiento = NEW.id_asiento
                         LIMIT 1;

                        IF v_id_grid_cell IS NULL THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'El id_asiento no existe o no tiene id_grid_cell asociado';
                        END IF;

                        IF NEW.id_grid_cell IS NULL THEN
                            SET NEW.id_grid_cell = v_id_grid_cell;
                        ELSEIF NEW.id_grid_cell <> v_id_grid_cell THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'id_asiento e id_grid_cell no coinciden';
                        END IF;
                    ELSEIF NEW.id_grid_cell IS NOT NULL THEN
                        SELECT a.id_asiento
                          INTO v_id_asiento
                          FROM asientos a
                         WHERE a.id_grid_cell = NEW.id_grid_cell
                         LIMIT 1;

                        IF v_id_asiento IS NULL THEN
                            SIGNAL SQLSTATE '45000'
                                SET MESSAGE_TEXT = 'No existe un asiento asociado al id_grid_cell del ticket';
                        END IF;

                        SET NEW.id_asiento = v_id_asiento;
                    END IF;
                END;
            ''',
            reverse_sql='''
                DROP TRIGGER IF EXISTS trg_tickets_sincronizar_asiento_bu;
                DROP TRIGGER IF EXISTS trg_tickets_sincronizar_asiento_bi;
            ''',
        ),
        migrations.RunSQL(
            sql='''
                DROP TRIGGER IF EXISTS trg_ordenes_marcar_asientos_vendidos_au;
                CREATE TRIGGER trg_ordenes_marcar_asientos_vendidos_au
                AFTER UPDATE ON ordenes
                FOR EACH ROW
                BEGIN
                    IF OLD.estatus <> 'pagado' AND NEW.estatus = 'pagado' THEN
                        UPDATE estado_asiento_evento e
                        INNER JOIN tickets t
                            ON t.id_orden = NEW.id_orden
                           AND t.id_evento = NEW.id_evento
                           AND t.id_grid_cell = e.id_grid_cell
                        SET
                            e.estado = 'vendido',
                            e.retenido_por = NULL,
                            e.retenido_hasta = NULL
                        WHERE e.id_evento = NEW.id_evento
                          AND e.estado IN ('retenido', 'disponible');
                    END IF;
                END;
            ''',
            reverse_sql='''
                DROP TRIGGER IF EXISTS trg_ordenes_marcar_asientos_vendidos_au;
            ''',
        ),
    ]
