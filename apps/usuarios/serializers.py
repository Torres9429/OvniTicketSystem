import re
from rest_framework import serializers
from .models import Usuarios
from apps.roles.models import Roles
from datetime import date

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
    contrasena = serializers.CharField(write_only=True)

    class Meta:
        model = Usuarios
        fields = (
            'nombre', 'apellidos', 'correo', 'contrasena',
            'fecha_nacimiento',
        )
    
    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_correo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El correo es obligatorio.")
        if "@" not in value:
            raise serializers.ValidationError("El correo no es válido.")
        return value
    
    def validate_contrasena(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("La contraseña debe tener al menos una letra mayúscula.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("La contraseña debe tener al menos una letra minúscula.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("La contraseña debe tener al menos un número.")
        if not re.search(r'[!@#$%&.]', value):
            raise serializers.ValidationError("La contraseña debe tener al menos un carácter especial.")
        return value

    def validate_fecha_nacimiento(self, value):
        today = date.today()
        edad = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if edad < 18:
            raise serializers.ValidationError("El usuario debe ser mayor de edad.")
        return value


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
