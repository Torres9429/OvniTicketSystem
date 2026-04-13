from django.db import models
from apps.zonas.models import Zonas
from apps.layouts.models import Layouts

class GridCells(models.Model):
    id_grid_cells = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=16)
    row = models.IntegerField()
    col = models.IntegerField()
    id_zona = models.ForeignKey(Zonas, on_delete=models.DO_NOTHING, db_column='id_zona', null=True, blank=True)
    id_layout = models.ForeignKey(Layouts, on_delete=models.DO_NOTHING, db_column='id_layout')

    class Meta:
        db_table = 'grid_cells'
        ordering = ['id_grid_cells']
