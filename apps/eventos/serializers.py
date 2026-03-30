from rest_framework import serializers
from django.utils import timezone
from .models import Eventos
from apps.lugares.models import Lugares
from apps.layouts.models import Layouts


class EventosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eventos
        fields = '__all__'
        read_only_fields = ('id_evento', 'fecha_creacion', 'fecha_actualizacion')


class EventosListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eventos
        fields = ('id_evento', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'fecha_creacion', 'id_lugar', 'estatus', 'foto')


class EventosDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eventos
        fields = (
            'id_evento', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'tiempo_espera', 'foto', 'estatus', 'fecha_creacion',
            'fecha_actualizacion', 'id_lugar', 'id_version'
        )


class EventosCreateSerializer(serializers.ModelSerializer):
    descripcion = serializers.CharField(required=False, allow_null=True, max_length=150)
    foto = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)
    estatus = serializers.BooleanField(required=False, default=True)
    id_lugar = serializers.PrimaryKeyRelatedField(queryset=Lugares.objects.all())
    id_version = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all())

    class Meta:
        model  = Eventos
        fields = (
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'tiempo_espera', 'foto', 'estatus', 'id_lugar', 'id_version', 
            'fecha_creacion', 'fecha_actualizacion'
        )

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del evento es obligatorio.")
        return value

    def validate_tiempo_espera(self, value):
        if value is None:
            raise serializers.ValidationError("El tiempo de espera es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El tiempo de espera no puede ser negativo.")
        return value

    def validate_fecha_inicio(self, value):
        if not value:
            raise serializers.ValidationError("La fecha de inicio es obligatoria.")
        return value

    def validate_fecha_fin(self, value):
        if not value:
            raise serializers.ValidationError("La fecha de fin es obligatoria.")
        return value

    def validate(self, data):
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin    = data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError({
                'fecha_fin': "La fecha de fin no puede ser anterior o igual a la fecha de inicio."
            })
        return data


class EventosUpdateSerializer(serializers.ModelSerializer):
    id_lugar   = serializers.PrimaryKeyRelatedField(queryset=Lugares.objects.all())
    id_version = serializers.PrimaryKeyRelatedField(queryset=Layouts.objects.all())

    class Meta:
        model  = Eventos
        fields = (
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin',
            'tiempo_espera', 'foto', 'estatus', 'id_lugar', 'id_version'
        )

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del evento es obligatorio.")
        return value

    def validate_tiempo_espera(self, value):
        if value is None:
            raise serializers.ValidationError("El tiempo de espera es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El tiempo de espera no puede ser negativo.")
        return value

    def validate(self, data):
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin    = data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError({
                'fecha_fin': "La fecha de fin no puede ser anterior o igual a la fecha de inicio."
            })
        return data