from rest_framework import serializers
from .models import Ordenes
from apps.eventos.models import Eventos
from apps.usuarios.models import Usuarios


class OrdenesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordenes
        fields = '__all__'
        read_only_fields = ('id_orden',)


class OrdenesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordenes
        fields = ('id_orden', 'total', 'estatus', 'fecha_creacion', 'id_evento', 'id_usuario')


class OrdenesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordenes
        fields = (
            'id_orden', 'total', 'estatus',
            'fecha_creacion', 'fecha_actualizacion',
            'id_evento', 'id_usuario',
        )


class OrdenesCreateSerializer(serializers.ModelSerializer):
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all())

    class Meta:
        model = Ordenes
        fields = (
            'total', 'estatus', 'id_evento'
        )

    def validate_total(self, value):
        if value is None:
            raise serializers.ValidationError("El total es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El total no puede ser negativo.")
        return value

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        usuario = getattr(request, "user", None)
        if not usuario or not getattr(usuario, "pk", None):
            return attrs

        estatus = attrs.get("estatus", Ordenes.ESTATUS_PENDIENTE)
        existe_duplicada = Ordenes.objects.filter(
            id_usuario_id=usuario.pk,
            id_evento=attrs["id_evento"],
            total=attrs["total"],
            estatus=estatus,
        ).exists()

        if existe_duplicada:
            raise serializers.ValidationError(
                "Ya existe una orden con los mismos datos para este usuario y evento."
            )

        return attrs


class OrdenesUpdateSerializer(serializers.ModelSerializer):
    id_evento = serializers.PrimaryKeyRelatedField(queryset=Eventos.objects.all())

    class Meta:
        model = Ordenes
        fields = ('total', 'estatus', 'id_evento')

    def validate_total(self, value):
        if value is None:
            raise serializers.ValidationError("El total es obligatorio.")
        if value < 0:
            raise serializers.ValidationError("El total no puede ser negativo.")
        return value

    def validate_estatus(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El estatus es obligatorio.")
        return value
