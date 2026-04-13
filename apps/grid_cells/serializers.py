from rest_framework import serializers
from .models import GridCells
from apps.zonas.models import Zonas
from apps.layouts.models import Layouts

TIPOS_VALIDOS = ['VACÍO', 'VACIO', 'PASILLO', 'ESCENARIO', 'ZONA DE ASIENTOS']


class GridCellsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridCells
        fields = '__all__'
        read_only_fields = ('id_grid_cells',)


class GridCellsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridCells
        fields = ('id_grid_cells', 'tipo', 'row', 'col', 'id_zona', 'id_layout')


class GridCellsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridCells
        fields = ('id_grid_cells', 'tipo', 'row', 'col', 'id_zona', 'id_layout')


class GridCellsCreateSerializer(serializers.ModelSerializer):
    id_zona   = serializers.PrimaryKeyRelatedField(queryset=Zonas.objects.all(), required=False, allow_null=True)
    id_layout = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all())

    class Meta:
        model  = GridCells
        fields = ('tipo', 'row', 'col', 'id_zona', 'id_layout')

    def validate_tipo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El tipo de la celda es obligatorio.")
        if value not in TIPOS_VALIDOS:
            raise serializers.ValidationError(
                f"Tipo inválido. Opciones: {', '.join(TIPOS_VALIDOS)}"
            )
        return value

    def validate_row(self, value):
        if value is None:
            raise serializers.ValidationError("La fila es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La fila no puede ser negativa.")
        return value

    def validate_col(self, value):
        if value is None:
            raise serializers.ValidationError("La columna es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La columna no puede ser negativa.")
        return value

    def validate(self, data):
        id_layout = data.get('id_layout')
        row = data.get('row')
        col = data.get('col')
        if GridCells.objects.filter(id_layout=id_layout, row=row, col=col).exists():
            raise serializers.ValidationError({
                'row': f"Ya existe una celda en la posición ({row}, {col}) para este layout."
            })
        return data


class GridCellsUpdateSerializer(serializers.ModelSerializer):
    id_zona   = serializers.PrimaryKeyRelatedField(queryset=Zonas.objects.all(), required=False, allow_null=True)
    id_layout = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all())

    class Meta:
        model  = GridCells
        fields = ('tipo', 'row', 'col', 'id_zona', 'id_layout')

    def validate_tipo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El tipo de la celda es obligatorio.")
        if value not in TIPOS_VALIDOS:
            raise serializers.ValidationError(
                f"Tipo inválido. Opciones: {', '.join(TIPOS_VALIDOS)}"
            )
        return value

    def validate_row(self, value):
        if value is None:
            raise serializers.ValidationError("La fila es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La fila no puede ser negativa.")
        return value

    def validate_col(self, value):
        if value is None:
            raise serializers.ValidationError("La columna es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La columna no puede ser negativa.")
        return value

    def validate(self, data):
        id_layout = data.get('id_layout')
        row = data.get('row')
        col = data.get('col')
        qs = GridCells.objects.filter(id_layout=id_layout, row=row, col=col)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                'row': f"Ya existe una celda en la posición ({row}, {col}) para este layout."
            })
        return data