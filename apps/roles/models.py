from django.db import models

class Roles(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=20)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        db_table = 'roles'
        ordering = ['id_rol']