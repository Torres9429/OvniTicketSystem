from rest_framework import serializers
from .models import Roles


class RolesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ('id_rol', 'nombre', 'fecha_creacion')


class RolesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ('id_rol', 'nombre', 'fecha_creacion', 'fecha_actualizacion')


class RolesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ('nombre', 'fecha_creacion', 'fecha_actualizacion')

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value


class RolesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ('nombre',)

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value
