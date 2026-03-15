from django.db import models
from apps.zonas.models import Zonas

class Asientos(models.Model):
    id_asiento = models.BigAutoField(primary_key=True)
    grid_row = models.IntegerField()
    grid_col = models.IntegerField()
    numero_asiento = models.IntegerField()
    existe = models.IntegerField()
    id_zona = models.ForeignKey(Zonas, on_delete=models.DO_NOTHING, db_column='id_zona')

    class Meta:
        db_table = 'asientos'
        ordering = ['id_asiento']
