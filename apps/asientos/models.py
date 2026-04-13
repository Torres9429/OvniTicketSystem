from django.db import models
from apps.zonas.models import Zonas


class Asientos(models.Model):
    id_asiento = models.BigAutoField(primary_key=True)
    grid_row = models.IntegerField()
    grid_col = models.IntegerField()
    numero_asiento = models.IntegerField()
    existe = models.IntegerField()
    id_zona = models.ForeignKey(Zonas, on_delete=models.DO_NOTHING, db_column='id_zona')
    id_grid_cell = models.ForeignKey(
        'grid_cells.GridCells', on_delete=models.SET_NULL,
        null=True, blank=True, db_column='id_grid_cell',
    )

    class Meta:
        db_table = 'asientos'
        ordering = ['id_asiento']


class EstadoAsientoEvento(models.Model):
    DISPONIBLE = 'disponible'
    RETENIDO = 'retenido'
    VENDIDO = 'vendido'

    ESTADOS = [
        (DISPONIBLE, 'Disponible'),
        (RETENIDO, 'Retenido'),
        (VENDIDO, 'Vendido'),
    ]

    id = models.BigAutoField(primary_key=True)
    id_grid_cell = models.ForeignKey(
        'grid_cells.GridCells', on_delete=models.CASCADE, db_column='id_grid_cell',
    )
    id_evento = models.ForeignKey(
        'eventos.Eventos', on_delete=models.CASCADE, db_column='id_evento',
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default=DISPONIBLE)
    retenido_por = models.ForeignKey(
        'usuarios.Usuarios', null=True, blank=True,
        on_delete=models.SET_NULL, db_column='retenido_por',
    )
    retenido_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'estado_asiento_evento'
        unique_together = ('id_grid_cell', 'id_evento')
        ordering = ['id']
