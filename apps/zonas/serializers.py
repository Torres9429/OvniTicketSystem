from rest_framework import serializers
from .models import Zonas
from apps.layouts.models import Layouts

class ZonasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zonas
        fields = '__all__'


class ZonasListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zonas
        fields = ('nombre', 'color', 'fecha_creacion', 'fecha_modificacion', 'id_layout')

class ZonasDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zonas
        fields = ('nombre', 'color', 'fecha_creacion', 'fecha_modificacion', 'id_layout')

class ZonasCreateSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=30, required=True, allow_null=True)
    color = serializers.CharField(max_length=7, required=True, allow_null=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    id_layout = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all(), required=True)
    
    class Meta:
        model = Zonas
        fields = ('nombre', 'color', 'fecha_creacion', 'fecha_modificacion', 'id_layout')

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El campo nombre es obligatorio.")
        return value

    def validate_color(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El campo color es obligatorio.")
        return value
    

class ZonasUpdateSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=30, required=True, allow_null=True)
    color = serializers.CharField(max_length=7, required=True, allow_null=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    id_layout = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all(), required=True)
    
    class Meta:
        model = Zonas
        fields = 'nombre', 'color', 'fecha_modificacion', 'id_layout'

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El campo nombre es obligatorio.")
        return value

    def validate_color(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El campo color es obligatorio.")
        return value