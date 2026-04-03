from django.db import models

from apps.roles.models import Roles

class Usuarios(models.Model):
    ESTATUS_CHOICES = [
        ('activo', 'Activo'),
        ('pendiente', 'Pendiente'),
        ('inactivo', 'Inactivo'),
    ]

    id_usuario = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=60, blank=True, null=True)
    correo = models.CharField(unique=True, max_length=50)
    contrasena = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='activo')
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column='id_rol')

    class Meta:
        db_table = 'usuarios'
        ordering = ['id_usuario']