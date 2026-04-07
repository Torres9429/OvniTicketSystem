from rest_framework import serializers
from django.utils import timezone
from .models import Layouts
from apps.lugares.models import Lugares
from apps.usuarios.models import Usuarios
from apps.layouts.models import Layouts


def _validate_layout_data_payload(value):
    if value is None:
        return value

    required = ["version", "canvasWidth", "canvasHeight", "zones", "sections", "elements"]
    missing = [k for k in required if k not in value]
    if missing:
        raise serializers.ValidationError(f"Faltan claves en layout_data: {missing}")

    if not isinstance(value.get("zones"), list):
        raise serializers.ValidationError("layout_data.zones debe ser una lista.")
    if not isinstance(value.get("sections"), list):
        raise serializers.ValidationError("layout_data.sections debe ser una lista.")
    if not isinstance(value.get("elements"), list):
        raise serializers.ValidationError("layout_data.elements debe ser una lista.")

    return value

class LayoutsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layouts
        fields = "__all__"
        read_only_fields = ("id_layout", "version", "fecha_creacion", "fecha_actualizacion")


class LayoutsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layouts
        fields = ('id_layout', 'grid_rows', 'grid_cols', 'version', 'estatus', 'fecha_creacion', 'id_lugar', 'id_dueno')


class LayoutsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layouts
        fields = (
            'id_layout', 'grid_rows', 'grid_cols', 'version', 'estatus', 'fecha_creacion',
            'fecha_actualizacion', 'id_lugar', 'id_dueno', 'layout_data'
        )


class LayoutsCreateSerializer(serializers.ModelSerializer):
    estatus = serializers.CharField(required=True, allow_null=False, allow_blank=False, max_length=9)
    id_lugar = serializers.PrimaryKeyRelatedField(queryset=Lugares.objects.all())
    id_dueno = serializers.PrimaryKeyRelatedField(queryset=Usuarios.objects.all())
    layout_data = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Layouts
        fields = (
            'grid_rows', 'grid_cols', 'version', 'estatus', 'id_lugar', 'id_dueno', 'layout_data'
        )

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        return value

    def validate_grid_rows(self, value):
        if value is None:
            raise serializers.ValidationError("El número de filas de la cuadrícula es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El número de filas de la cuadrícula no puede ser negativo.")
        return value

    def validate_grid_cols(self, value):
        if value is None:
            raise serializers.ValidationError("El número de columnas de la cuadrícula es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El número de columnas de la cuadrícula no puede ser negativo.")
        return value

    def validate_layout_data(self, value):
        return _validate_layout_data_payload(value)


class LayoutsUpdateSerializer(serializers.ModelSerializer):
    id_lugar = serializers.PrimaryKeyRelatedField(queryset=Lugares.objects.all())
    id_dueno = serializers.PrimaryKeyRelatedField(queryset=Usuarios.objects.all())
    layout_data = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Layouts
        fields = (
            'grid_rows', 'grid_cols', 'version', 'estatus', 'id_lugar', 'id_dueno', 'layout_data'
        )

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        return value

    def validate_grid_rows(self, value):
        if value is None:
            raise serializers.ValidationError("El número de filas de la cuadrícula es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El número de filas de la cuadrícula no puede ser negativo.")
        return value

    def validate_grid_cols(self, value):
        if value is None:
            raise serializers.ValidationError("El número de columnas de la cuadrícula es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El número de columnas de la cuadrícula no puede ser negativo.")
        return value

    def validate_layout_data(self, value):
        return _validate_layout_data_payload(value)