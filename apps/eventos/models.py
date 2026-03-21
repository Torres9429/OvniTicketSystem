from django.db import models
from apps.lugares.models import Lugares
from apps.layouts.models import Layouts

class Eventos(models.Model):
    id_evento = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=150, blank=False, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tiempo_espera = models.IntegerField()
    foto = models.CharField(max_length=255, blank=True, null=True)
    estatus = models.BooleanField(default=1)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_lugar = models.ForeignKey(Lugares, on_delete=models.DO_NOTHING, db_column='id_lugar')
    id_version = models.ForeignKey(Layouts, on_delete=models.DO_NOTHING, db_column='id_version')

    class Meta:
        db_table = 'eventos'
        ordering = ['id_evento']
