from django.db import models
from apps.eventos.models import Eventos
from apps.usuarios.models import Usuarios

class Ordenes(models.Model):
    id_orden = models.BigAutoField(primary_key=True)
    total = models.FloatField()
    estatus = models.CharField(max_length=9)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_evento = models.ForeignKey(Eventos, on_delete=models.DO_NOTHING, db_column='id_evento')
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.DO_NOTHING, db_column='id_usuario')

    class Meta:
        db_table = 'ordenes'
        ordering = ['id_orden']
