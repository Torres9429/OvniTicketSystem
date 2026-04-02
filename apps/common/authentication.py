from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

from apps.usuarios.models import Usuarios


class JWTAuthentication(BaseJWTAuthentication):
    """
    Extiende JWTAuthentication de simplejwt para resolver el usuario
    desde el modelo Usuarios (no el User de Django).
    """

    def get_user(self, validated_token):
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise InvalidToken("Token no contiene user_id")

        try:
            return Usuarios.objects.select_related("id_rol").get(id_usuario=user_id)
        except Usuarios.DoesNotExist:
            raise AuthenticationFailed("Usuario no encontrado")
