from django.db import models

from apps.eventos.models import Eventos
from apps.zonas.models import Zonas

class PrecioZonaEvento(models.Model):
    id_precio_zona_evento = models.BigAutoField(primary_key=True)
    precio = models.FloatField()
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_zona = models.ForeignKey(Zonas, on_delete=models.DO_NOTHING, db_column='id_zona')
    id_evento = models.ForeignKey(Eventos, on_delete=models.DO_NOTHING, db_column='id_evento')

    class Meta:
        db_table = 'precio_zona_evento'
        ordering = ['id_precio_zona_evento']