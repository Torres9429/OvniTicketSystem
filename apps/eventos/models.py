from django.db import models
from apps.lugares.models import Lugares
from apps.layouts.models import Layouts

class Eventos(models.Model):
    ESTATUS_BORRADOR = "BORRADOR"
    ESTATUS_PUBLICADO = "PUBLICADO"
    ESTATUS_CANCELADO = "CANCELADO"
    ESTASTUS_FINALIZADO = "FINALIZADO"

    ESTATUS_CHOICES = [
        (ESTATUS_BORRADOR, "Borrador"),
        (ESTATUS_PUBLICADO, "Publicado"),
        (ESTATUS_CANCELADO, "Cancelado"),
        (ESTASTUS_FINALIZADO, "Finalizado"),
    ]

    id_evento = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=150, blank=True, default='')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tiempo_espera = models.IntegerField()
    foto = models.TextField(blank=True, default='')
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_lugar = models.ForeignKey(Lugares, on_delete=models.DO_NOTHING, db_column='id_lugar')
    id_version = models.ForeignKey(Layouts, on_delete=models.DO_NOTHING, db_column='id_version')

    class Meta:
        db_table = 'eventos'
        ordering = ['id_evento']