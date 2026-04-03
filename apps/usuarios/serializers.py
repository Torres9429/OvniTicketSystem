from rest_framework import serializers
from .models import Usuarios
from apps.roles.models import Roles


class UsuariosListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ('id_usuario', 'nombre', 'apellidos', 'correo', 'id_rol')


class UsuariosDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = (
            'id_usuario', 'nombre', 'apellidos', 'correo',
            'fecha_nacimiento', 'fecha_creacion', 'fecha_actualizacion', 'id_rol',
        )


class UsuariosCreateSerializer(serializers.ModelSerializer):
    id_rol = serializers.PrimaryKeyRelatedField(queryset=Roles.objects.all())
    contrasena = serializers.CharField(write_only=True)

    class Meta:
        model = Usuarios
        fields = (
            'nombre', 'apellidos', 'correo', 'contrasena',
            'fecha_nacimiento', 'fecha_creacion', 'fecha_actualizacion', 'id_rol',
        )

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_correo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El correo es obligatorio.")
        return value.strip().lower()


class UsuariosUpdateSerializer(serializers.ModelSerializer):
    id_rol = serializers.PrimaryKeyRelatedField(queryset=Roles.objects.all())

    class Meta:
        model = Usuarios
        fields = ('nombre', 'apellidos', 'correo', 'fecha_nacimiento', 'id_rol')

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_correo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El correo es obligatorio.")
        return value.strip().lower()


class LoginSerializer(serializers.Serializer):
    correo = serializers.CharField()
    contrasena = serializers.CharField(write_only=True)

    def validate_correo(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("El correo es obligatorio.")
        return value

    def validate_contrasena(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La contraseña es obligatoria.")
        return value
