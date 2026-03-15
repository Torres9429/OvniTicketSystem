from django.db import models
from apps.usuarios.models import Usuarios
from apps.lugares.models import Lugares

class Layouts(models.Model):
    id_layout = models.BigAutoField(primary_key=True)
    grid_rows = models.IntegerField()
    grid_cols = models.IntegerField()
    version = models.IntegerField()
    estatus = models.CharField(max_length=9)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_dueno = models.ForeignKey(Usuarios, on_delete=models.DO_NOTHING, db_column='id_dueno')
    id_lugar = models.ForeignKey(Lugares, on_delete=models.DO_NOTHING, db_column='id_lugar')

    class Meta:
        db_table = 'layouts'
        ordering = ['id_layout']
