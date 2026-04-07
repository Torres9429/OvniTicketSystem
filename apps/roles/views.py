import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from .models import Roles
from .serializers import (
    RolesListSerializer, RolesDetailSerializer,
    RolesCreateSerializer, RolesUpdateSerializer,
)
from .services import crear_rol, actualizar_rol, eliminar_rol
from .selectors import get_all_roles

logger = logging.getLogger(__name__)


class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()

    def get_queryset(self):
        return get_all_roles()

    def get_serializer_class(self):
        if self.action == 'list':
            return RolesListSerializer
        if self.action == 'retrieve':
            return RolesDetailSerializer
        if self.action == 'create':
            return RolesCreateSerializer
        if self.action in ('update', 'partial_update'):
            return RolesUpdateSerializer
        return RolesDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /roles/ — listando roles")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /roles/ — {len(response.data)} roles retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /roles/{pk}/ — buscando rol")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /roles/{pk}/ — rol encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /roles/{pk}/ — rol no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /roles/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /roles/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol = crear_rol(**serializer.validated_data, id_usuario=request.user, request=request)
            output = RolesDetailSerializer(rol)
            logger.info(f"POST /roles/ — rol creado con id={rol.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /roles/ — error al crear rol: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el rol"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /roles/{pk}/ — payload: {request.data}")
        try:
            rol = Roles.objects.get(pk=pk)
        except Roles.DoesNotExist:
            logger.warning(f"PUT /roles/{pk}/ — rol no encontrado")
            return Response({"error": "Rol no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(rol, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /roles/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol = actualizar_rol(rol, **serializer.validated_data, id_usuario=request.user, request=request )
            output = RolesDetailSerializer(rol)
            logger.info(f"PUT /roles/{pk}/ — rol actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /roles/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el rol"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /roles/{pk}/ — payload: {request.data}")
        try:
            rol = Roles.objects.get(pk=pk)
        except Roles.DoesNotExist:
            logger.warning(f"PATCH /roles/{pk}/ — rol no encontrado")
            return Response({"error": "Rol no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(rol, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /roles/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol = actualizar_rol(rol, **serializer.validated_data)
            output = RolesDetailSerializer(rol)
            logger.info(f"PATCH /roles/{pk}/ — rol actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /roles/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el rol"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /roles/{pk}/ — solicitud recibida")
        try:
            rol = Roles.objects.get(pk=pk)
        except Roles.DoesNotExist:
            logger.warning(f"DELETE /roles/{pk}/ — rol no encontrado")
            return Response({"error": "Rol no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        try:
            eliminar_rol(rol, id_usuario=request.user, request=request)
            logger.info(f"DELETE /roles/{pk}/ — rol eliminado")
            return Response(
                {"message": "Rol eliminado correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"DELETE /roles/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar el rol"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
