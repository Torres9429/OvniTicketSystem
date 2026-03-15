from django.db import models
from apps.usuarios.models import Usuarios

class Lugares(models.Model):
    id_lugar = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=70)
    ciudad = models.CharField(max_length=45)
    pais = models.CharField(max_length=45)
    direccion = models.CharField(max_length=150)
    estatus = models.CharField(max_length=12)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()

    id_dueno = models.ForeignKey(
        Usuarios,
        on_delete=models.DO_NOTHING,
        db_column="id_dueno"
    )

    class Meta:
        db_table = "lugares"
        ordering = ['id_lugar']
