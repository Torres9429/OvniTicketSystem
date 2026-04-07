from rest_framework import serializers
from .models import AuditoriaLogs

class AuditoriaLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditoriaLogs
        fields = (
            'id_auditoria_log', 
            'entidad',
            'accion', 
            'valores_antes', 
            'valores_despues',
            'fecha_creacion', 
            'id_usuario',
            'ip'
        )
