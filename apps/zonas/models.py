from django.db import models
from apps.layouts.models import Layouts

class Zonas(models.Model):
    id_zona = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    color = models.CharField(max_length=7)
    fecha_creacion = models.DateTimeField()
    fecha_modificacion = models.DateTimeField()
    id_layout = models.ForeignKey(Layouts, on_delete=models.DO_NOTHING, db_column='id_layout')

    class Meta:
        db_table = 'zonas'
        ordering = ['id_zona']
