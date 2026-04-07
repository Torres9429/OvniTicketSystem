import logging
from django.contrib.auth.hashers import check_password
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from apps.common.permissions import IsAdmin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .models import Usuarios
from .serializers import (
    UsuariosListSerializer, UsuariosDetailSerializer,
    UsuariosCreateSerializer, UsuariosUpdateSerializer,
    LoginSerializer, CustomTokenRefreshSerializer,
)
from .models import Roles
from .services import crear_usuario, actualizar_usuario, eliminar_usuario, aprobar_usuario, desactivar_usuario
from .selectors import get_all_usuarios, get_usuarios_por_rol

logger = logging.getLogger(__name__)
ERROR_USUARIO_NO_ENCONTRADO = "Usuario no encontrado"


class RegistroUsuarioView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UsuariosCreateSerializer(data=request.data) 
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            rol = Roles.objects.get(nombre='usuario')
            usuario = crear_usuario(**serializer.validated_data, id_rol=rol, estatus='activo', request=request)
            return Response(UsuariosDetailSerializer(usuario).data, status=status.HTTP_201_CREATED)
        except Roles.DoesNotExist:
            return Response({"error": "Rol 'usuario' no encontrado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}", exc_info=True)
            return Response({"error": "Error interno"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class RegistroOrganizadorView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UsuariosCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            rol = Roles.objects.get(nombre='organizador')
            crear_usuario(
                **serializer.validated_data,
                id_rol=rol,
                estatus='pendiente',
                request=request
            )
            return Response(
                {"message": "Solicitud enviada, espera la aprobación del administrador."},
                status=status.HTTP_201_CREATED
            )
        except Roles.DoesNotExist:
            return Response({"error": "Rol 'cliente' no encontrado"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error al registrar cliente: {e}", exc_info=True)
            return Response({"error": "Error interno"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsuariosViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all()

    def get_permissions(self):
        if self.action in ('aprobar', 'desactivar', 'destroy', 'list', 'retrieve', 'update', 'partial_update'):
            return [IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        return get_all_usuarios()

    def get_serializer_class(self):
        if self.action == 'list':
            return UsuariosListSerializer
        if self.action == 'retrieve':
            return UsuariosDetailSerializer
        if self.action == 'create':
            return UsuariosCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UsuariosUpdateSerializer
        return UsuariosDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /usuarios/ — listando usuarios")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /usuarios/ — {len(response.data)} usuarios retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /usuarios/{pk}/ — buscando usuario")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /usuarios/{pk}/ — usuario encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /usuarios/{pk}/ — usuario no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /usuarios/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /usuarios/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = crear_usuario(**serializer.validated_data, request=request)
            output = UsuariosDetailSerializer(usuario)
            logger.info(f"POST /usuarios/ — usuario creado con id={usuario.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /usuarios/ — error al crear usuario: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /usuarios/{pk}/ — payload: {request.data}")
        try:
            usuario = Usuarios.objects.get(pk=pk)
        except Usuarios.DoesNotExist:
            logger.warning(f"PUT /usuarios/{pk}/ — usuario no encontrado")
            return Response({"error": ERROR_USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(usuario, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /usuarios/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = actualizar_usuario(usuario, **serializer.validated_data, request=request)
            output = UsuariosDetailSerializer(usuario)
            logger.info(f"PUT /usuarios/{pk}/ — usuario actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /usuarios/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /usuarios/{pk}/ — payload: {request.data}")
        try:
            usuario = Usuarios.objects.get(pk=pk)
        except Usuarios.DoesNotExist:
            logger.warning(f"PATCH /usuarios/{pk}/ — usuario no encontrado")
            return Response({"error": ERROR_USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(usuario, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /usuarios/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = actualizar_usuario(usuario, **serializer.validated_data, request=request)
            output = UsuariosDetailSerializer(usuario)
            logger.info(f"PATCH /usuarios/{pk}/ — usuario actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /usuarios/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /usuarios/{pk}/ — solicitud recibida")
        try:
            usuario = Usuarios.objects.get(pk=pk)
        except Usuarios.DoesNotExist:
            logger.warning(f"DELETE /usuarios/{pk}/ — usuario no encontrado")
            return Response({"error": ERROR_USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        try:
            eliminar_usuario(usuario, request=request)
            logger.info(f"DELETE /usuarios/{pk}/ — usuario eliminado")
            return Response(
                {"message": "Usuario eliminado correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"DELETE /usuarios/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar el usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
    @action(detail=True, methods=["patch"], url_path="aprobar")
    def aprobar(self, request, pk=None):
        try:
            usuario = Usuarios.objects.get(pk=pk)
        except Usuarios.DoesNotExist:
            return Response({"error": ERROR_USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        if usuario.estatus != 'pendiente':
            return Response({"error": "El usuario no está pendiente de aprobación"}, status=status.HTTP_400_BAD_REQUEST)

        usuario = aprobar_usuario(usuario, request=request)
        return Response({"message": "Usuario aprobado correctamente"}, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=["patch"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        try:
            usuario = Usuarios.objects.get(pk=pk)
        except Usuarios.DoesNotExist:
            return Response({"error": ERROR_USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        usuario = desactivar_usuario(usuario, request=request)
        return Response({"message": "Usuario desactivado correctamente"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="por-rol/(?P<id_rol>[^/.]+)")
    def por_rol(self, request, id_rol=None):
        logger.debug(f"GET /usuarios/por-rol/{id_rol}/")
        try:
            usuarios = get_usuarios_por_rol(id_rol=id_rol)
            serializer = UsuariosListSerializer(usuarios, many=True)
            logger.info(f"GET /usuarios/por-rol/{id_rol}/ — {usuarios.count()} usuarios")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /usuarios/por-rol/{id_rol}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener usuarios del rol"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("POST /auth/login/ — intento de login")
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /auth/login/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        correo = serializer.validated_data["correo"]
        contrasena = serializer.validated_data["contrasena"]
        
        logger.debug(f"DEBUG — correo: '{correo}' | contrasena: '{contrasena}'")
        
        try:
            usuario = Usuarios.objects.select_related("id_rol").get(correo=correo)
        except Usuarios.DoesNotExist:
            logger.warning(f"POST /auth/login/ — correo no encontrado: {correo}")
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(contrasena, usuario.contrasena):
            logger.warning(f"POST /auth/login/ — contraseña incorrecta para: {correo}")
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        if usuario.estatus == 'pendiente':
            return Response({"error": "Tu cuenta está pendiente de aprobación."}, status=status.HTTP_403_FORBIDDEN)
        if usuario.estatus == 'inactivo':
            return Response({"error": "Tu cuenta está desactivada."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken()
        refresh["user_id"] = usuario.id_usuario
        refresh["correo"] = usuario.correo
        refresh["rol"] = usuario.id_rol.nombre

        logger.info(f"POST /auth/login/ — login exitoso para usuario id={usuario.id_usuario}")
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "usuario": {
                    "id_usuario": usuario.id_usuario,
                    "nombre": usuario.nombre,
                    "correo": usuario.correo,
                    "rol": usuario.id_rol.nombre,
                },
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para refrescar tokens JWT.
    Usa CustomTokenRefreshSerializer para buscar usuarios en Usuarios
    en lugar del modelo User de Django.
    """
    serializer_class = CustomTokenRefreshSerializer
