from rest_framework import serializers
from .models import Asientos
from apps.zonas.models import Zonas

class AsientosListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asientos
        fields = ('id_asiento', 'grid_row', 'grid_col', 'numero_asiento', 'existe')


class AsientosDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asientos
        fields = ('id_asiento', 'grid_row', 'grid_col', 'numero_asiento', 'existe', 'id_zona')


class AsientosCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asientos
        fields = ('grid_row', 'grid_col', 'numero_asiento', 'existe', 'id_zona')

    def validate(self, data):
        if data.get('grid_row') < 0:
            raise serializers.ValidationError("grid_row no puede ser negativo.")

        if data.get('grid_col') < 0:
            raise serializers.ValidationError("grid_col no puede ser negativo.")

        if data.get('numero_asiento') <= 0:
            raise serializers.ValidationError("El número de asiento debe ser mayor a 0.")

        return data


class AsientosUpdateSerializer(serializers.ModelSerializer):
    id_zona = serializers.PrimaryKeyRelatedField(queryset=Zonas.objects.all())
    
    class Meta:
        model = Asientos
        fields = ('grid_row', 'grid_col', 'numero_asiento', 'existe', 'id_zona')

    def validate(self, data):
        if 'grid_row' in data and data['grid_row'] < 0:
            raise serializers.ValidationError("grid_row no puede ser negativo.")

        if 'grid_col' in data and data['grid_col'] < 0:
            raise serializers.ValidationError("grid_col no puede ser negativo.")

        if 'numero_asiento' in data and data['numero_asiento'] <= 0:
            raise serializers.ValidationError("El número de asiento debe ser mayor a 0.")

        return data