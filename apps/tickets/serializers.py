from rest_framework import serializers
from .models import Tickets
from apps.ordenes.models import Ordenes
from apps.asientos.models import Asientos
from apps.eventos.models import Eventos


class TicketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tickets
        fields = '__all__'
        read_only_fields = ('id_ticket',)


class TicketsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tickets
        fields = ('id_ticket', 'precio', 'id_orden', 'id_asiento', 'id_evento')


class TicketsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tickets
        fields = ('id_ticket', 'precio', 'id_orden', 'id_asiento', 'id_evento')


class TicketsCreateSerializer(serializers.ModelSerializer):
    id_orden = serializers.PrimaryKeyRelatedField(queryset=Ordenes.objects.all())
    id_asiento = serializers.PrimaryKeyRelatedField(queryset=Asientos.objects.all())
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all())

    class Meta:
        model = Tickets
        fields = ('precio', 'id_orden', 'id_asiento', 'id_evento')

    def validate_precio(self, value):
        if value is None:
            raise serializers.ValidationError("El precio es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value


class TicketsUpdateSerializer(serializers.ModelSerializer):
    id_orden = serializers.PrimaryKeyRelatedField(queryset=Ordenes.objects.all())
    id_asiento = serializers.PrimaryKeyRelatedField(queryset=Asientos.objects.all())
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all())

    class Meta:
        model = Tickets
        fields = ('precio', 'id_orden', 'id_asiento', 'id_evento')

    def validate_precio(self, value):
        if value is None:
            raise serializers.ValidationError("El precio es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value
