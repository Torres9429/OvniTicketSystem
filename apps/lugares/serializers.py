from rest_framework import serializers
from django.utils import timezone
from .models import Lugares
from apps.usuarios.models import Usuarios


class LugaresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lugares
        fields = '__all__'
        read_only_fields = ('id_lugar', 'fecha_creacion', 'fecha_actualizacion')


class LugaresListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lugares
        fields = ('id_lugar', 'nombre', 'ciudad', 'pais', 'estatus', 'fecha_creacion', 'id_dueno')


class LugaresDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lugares
        fields = (
            'id_lugar', 'nombre', 'ciudad', 'pais', 'direccion',
            'estatus', 'fecha_creacion', 'fecha_actualizacion', 'id_dueno'
        )


class LugaresCreateSerializer(serializers.ModelSerializer):
    estatus = serializers.CharField(required=True, allow_null=False, allow_blank=False, max_length=12)
    id_dueno = serializers.PrimaryKeyRelatedField(queryset=Usuarios.objects.all())

    class Meta:
        model = Lugares
        fields = (
            'nombre', 'ciudad', 'pais', 'direccion', 'estatus',
            'fecha_creacion', 'fecha_actualizacion', 'id_dueno'
        )

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del lugar es obligatorio.")
        return value

    def validate_ciudad(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La ciudad es obligatoria.")
        return value

    def validate_pais(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El país es obligatorio.")
        return value

    def validate_direccion(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La dirección es obligatoria.")
        return value

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        valid_statuses = ['BORRADOR', 'PUBLICADO', 'INHABILITADO']
        if value.strip().upper() not in valid_statuses:
            raise serializers.ValidationError(f"El estatus debe ser uno de: {', '.join(valid_statuses)}.")
        return value.strip().upper()


class LugaresUpdateSerializer(serializers.ModelSerializer):
    id_dueno = serializers.PrimaryKeyRelatedField(queryset=Usuarios.objects.all())

    class Meta:
        model = Lugares
        fields = (
            'nombre', 'ciudad', 'pais', 'direccion', 'estatus', 'id_dueno'
        )

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del lugar es obligatorio.")
        return value

    def validate_ciudad(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La ciudad es obligatoria.")
        return value

    def validate_pais(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El país es obligatorio.")
        return value

    def validate_direccion(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La dirección es obligatoria.")
        return value

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        valid_statuses = ['BORRADOR', 'PUBLICADO', 'INHABILITADO']
        if value.strip().upper() not in valid_statuses:
            raise serializers.ValidationError(f"El estatus debe ser uno de: {', '.join(valid_statuses)}.")
        return value.strip().upper()
