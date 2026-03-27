from django.db import models
from apps.usuarios.models import Usuarios

class AuditoriaLogs(models.Model):
    id_auditoria_log = models.BigAutoField(primary_key=True)
    accion = models.CharField(max_length=60)
    entidad = models.CharField(max_length=45, blank=True)
    id_entidad = models.IntegerField(blank=True, null=True)
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.DO_NOTHING, db_column='id_usuario')
    detalles = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'auditoria_logs'
        ordering = ['id_auditoria_log']