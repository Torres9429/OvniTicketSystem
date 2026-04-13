from django.db import models
from apps.eventos.models import Eventos
from apps.usuarios.models import Usuarios

class Ordenes(models.Model):
    ESTATUS_PENDIENTE = 'pendiente'
    ESTATUS_PAGADO = 'pagado'
    ESTATUS_CANCELADO = 'cancelado'
    ESTATUS_REEMBOLSADO = 'reembolsado'
    ESTATUS_CHOICES = [
        (ESTATUS_PENDIENTE, 'Pendiente'),
        (ESTATUS_PAGADO, 'Pagado'),
        (ESTATUS_CANCELADO, 'Cancelado'),
        (ESTATUS_REEMBOLSADO, 'Reembolsado'),
    ]

    id_orden = models.BigAutoField(primary_key=True)
    total = models.FloatField()
    estatus = models.CharField(max_length=12, choices=ESTATUS_CHOICES, default=ESTATUS_PENDIENTE)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_evento = models.ForeignKey(Eventos, on_delete=models.DO_NOTHING, db_column='id_evento')
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.DO_NOTHING, db_column='id_usuario')
    operation_id = models.CharField(
        max_length=64, null=True, blank=True, unique=True, db_index=True,
        db_column='operation_id',
    )

    class Meta:
        db_table = 'ordenes'
        ordering = ['id_orden']
