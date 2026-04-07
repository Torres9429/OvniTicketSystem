import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import Usuarios
from apps.roles.models import Roles
from datetime import date

ERROR_CORREO_OBLIGATORIO = "El correo es obligatorio."

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
            raise serializers.ValidationError(ERROR_CORREO_OBLIGATORIO)
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
        if not re.search(r'\d', value):
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
            raise serializers.ValidationError(ERROR_CORREO_OBLIGATORIO)
        return value.strip().lower()


class LoginSerializer(serializers.Serializer):
    correo = serializers.CharField()
    contrasena = serializers.CharField(write_only=True)

    def validate_correo(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError(ERROR_CORREO_OBLIGATORIO)
        return value

    def validate_contrasena(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La contraseña es obligatoria.")
        return value


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Serializer personalizado para refrescar tokens.
    Busca el usuario en el modelo Usuarios en lugar de usar Django User.
    """
    def validate(self, attrs):
        # Validar el refresh token
        refresh = self.token_class(attrs['refresh'])
        
        try:
            # Extraer user_id del token
            user_id = refresh.get('user_id')
            if not user_id:
                raise InvalidToken('Token does not contain user_id')
            
            # Buscar el usuario en Usuarios (no en django.contrib.auth.User)
            Usuarios.objects.get(id_usuario=user_id)
            
        except Usuarios.DoesNotExist:
            raise InvalidToken('Usuario no encontrado o fue eliminado')
        except KeyError:
            raise InvalidToken('Token does not contain user_id')
        
        # Generar nuevo access token
        data = {'access': str(refresh.access_token)}
        
        return data
