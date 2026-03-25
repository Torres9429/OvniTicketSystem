from rest_framework import serializers
from .models import PrecioZonaEvento
from apps.zonas.models import Zonas
from apps.eventos.models import Eventos

from apps.layouts.models import Layouts

class PrecioZonaEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioZonaEvento
        fields = '__all__'

class PrecioZonaEventoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioZonaEvento
        fields = ('precio', 'fecha_creacion', 'fecha_modificacion', 'id_zona', 'id_evento')


class PrecioZonaEventoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioZonaEvento
        fields = ('precio', 'fecha_creacion', 'fecha_modificacion', 'id_zona', 'id_evento')

class PrecioZonaEventoCreateSerializer(serializers.ModelSerializer):
    precio = serializers.FloatField(required=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    id_zona = serializers.PrimaryKeyRelatedField(queryset=Zonas.objects.all(), required=True)
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all(), required=True)

    class Meta:
        model = PrecioZonaEvento
        fields = ('precio', 'fecha_creacion', 'fecha_modificacion', 'id_zona', 'id_evento')

    def validate_precio(self, value):
        if value is None:
            raise serializers.ValidationError("El campo precio es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El campo precio no puede ser negativo.")
        return value
    
class PrecioZonaEventoUpdateSerializer(serializers.ModelSerializer):
    precio = serializers.FloatField(required=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    id_zona = serializers.PrimaryKeyRelatedField(queryset=Zonas.objects.all(), required=True)
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all(), required=True)

    class Meta:
        model = PrecioZonaEvento
        fields = ('precio', 'fecha_creacion', 'fecha_modificacion', 'id_zona', 'id_evento')

    def validate_precio(self, value):
        if value is None:
            raise serializers.ValidationError("El campo precio es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El campo precio no puede ser negativo.")
        return value