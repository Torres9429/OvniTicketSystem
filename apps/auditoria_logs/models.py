from django.db import models
from apps.usuarios.models import Usuarios

class AuditoriaLogs(models.Model):
    id_auditoria_log = models.BigAutoField(primary_key=True)
    entidad = models.CharField(max_length=45, blank=True, default="")
    accion = models.CharField(max_length=60)
    valores_antes = models.JSONField(blank=True, null=True)   
    valores_despues = models.JSONField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.DO_NOTHING, db_column='id_usuario')
    ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'auditoria_logs'
        ordering = ['id_auditoria_log']