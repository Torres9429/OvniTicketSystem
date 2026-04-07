from django.db import models
from apps.usuarios.models import Usuarios
from apps.lugares.models import Lugares
from django.utils import timezone

class Layouts(models.Model):
    ESTATUS_BORRADOR = "BORRADOR"
    ESTATUS_PUBLICADO = "PUBLICADO"

    ESTATUS_CHOICES = [
        (ESTATUS_BORRADOR, "Borrador"),
        (ESTATUS_PUBLICADO, "Publicado"),
    ]

    id_layout = models.BigAutoField(primary_key=True)
    grid_rows = models.IntegerField()
    grid_cols = models.IntegerField()
    version = models.IntegerField()
    estatus = models.CharField(max_length=9, choices=ESTATUS_CHOICES)
    layout_data = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Ayuda a detectar cambios sin comparar JSON completo
    checksum_layout = models.CharField(max_length=64, null=True, blank=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    id_dueno = models.ForeignKey(
        Usuarios,
        on_delete=models.PROTECT,
        db_column="id_dueno",
        related_name="layouts_creados",
    )
    id_lugar = models.ForeignKey(
        Lugares,
        on_delete=models.PROTECT,
        db_column="id_lugar",
        related_name="layouts",
    )

    class Meta:
        db_table = 'layouts'
        ordering = ['id_layout']
