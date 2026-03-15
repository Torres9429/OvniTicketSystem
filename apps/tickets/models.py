from django.db import models

from apps.eventos.models import Eventos
from apps.ordenes.models import Ordenes
from apps.asientos.models import Asientos

class Tickets(models.Model):
    id_ticket = models.BigAutoField(primary_key=True)
    precio = models.FloatField()
    id_orden = models.ForeignKey(Ordenes, on_delete=models.DO_NOTHING, db_column='id_orden')
    id_asiento = models.ForeignKey(Asientos, on_delete=models.DO_NOTHING, db_column='id_asiento')
    id_evento = models.ForeignKey(Eventos, on_delete=models.DO_NOTHING, db_column='id_evento')

    class Meta:
        db_table = 'tickets'
        ordering = ['id_ticket']