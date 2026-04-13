import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.common.permissions import IsOrganizador
from .models import Zonas
from .services import crear_zona, actualizar_zona, eliminar_zona
from .selectors import get_all_zonas, buscar_zona_por_id, buscar_zona_por_nombre, buscar_zona_por_color, buscar_zona_por_fecha_creacion, buscar_zona_por_layout
from .serializers import (ZonasSerializer, ZonasListSerializer, ZonasCreateSerializer, ZonasUpdateSerializer, ZonasDetailSerializer)

logger = logging.getLogger(__name__)

class ZonasViewSet(viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsOrganizador()]
    def get_serializer_class(self):
        if self.action == "list":
            return ZonasListSerializer
        if self.action == "retrieve":
            return ZonasDetailSerializer
        if self.action == "create":
            return ZonasCreateSerializer
        if self.action == "update":
            return ZonasUpdateSerializer
        return ZonasDetailSerializer
    
    def list(self, request):
        zonas = get_all_zonas()
        serializer = self.get_serializer_class()(zonas, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        zona = buscar_zona_por_id(pk)
        if not zona:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(zona, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        logger.debug(f"POST /zonas/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"POST /zonas/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            zona = crear_zona(
                nombre=serializer.validated_data.get('nombre'),
                color=serializer.validated_data.get('color'),
                id_layout=serializer.validated_data.get('id_layout'),
                precio=serializer.validated_data.get('precio', 0),
                id_usuario=request.user,
                request=request
            )
            logger.info(f"POST /zonas/ — zona creada con id={zona.pk}")
            return Response(ZonasSerializer(zona).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /zonas/ — error al crear zona: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear la zona"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def update(self, request, pk=None):
        logger.debug(f"PUT /zonas/{pk}/ — payload: {request.data}")
        try:
            zona = Zonas.objects.get(pk=pk)
        except Zonas.DoesNotExist:
            logger.warning(f"PUT /zonas/{pk}/ — zona no encontrada")
            return Response({"error": "Zona no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer_class()(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"PUT /zonas/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            zona_actualizada = actualizar_zona(zona, **serializer.validated_data, id_usuario=request.user, request=request)
            logger.info(f"PUT /zonas/{pk}/ — zona actualizada correctamente")
            return Response(ZonasSerializer(zona_actualizada).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /zonas/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar la zona"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def destroy(self, request, pk=None):
        logger.debug(f"DELETE /zonas/{pk}/ — solicitud recibida")
        try:
            zona = Zonas.objects.get(pk=pk)
        except Zonas.DoesNotExist:
            logger.warning(f"DELETE /zonas/{pk}/ — zona no encontrada")
            return Response({"error": "Zona no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        if zona.asientos_set.exists():
            logger.warning(f"DELETE /zonas/{pk}/ — zona tiene asientos asociados")
            return Response(
                {"error": "No se puede eliminar la zona porque tiene asientos asociados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            eliminar_zona(zona, id_usuario=request.user, request=request)
            logger.info(f"DELETE /zonas/{pk}/ — zona eliminada")
            return Response(
                {"message": "Zona eliminada correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"DELETE /zonas/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar la zona"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )