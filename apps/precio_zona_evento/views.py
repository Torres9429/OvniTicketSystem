import logging
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.common.permissions import IsOrganizador
from .services import crear_precio_zona_evento, actualizar_precio_zona_evento, eliminar_precio_zona_evento
from .selectors import get_all_precio_zona_evento, buscar_precio_zona_evento_por_id
from .serializers import (PrecioZonaEventoSerializer, PrecioZonaEventoListSerializer, PrecioZonaEventoCreateSerializer, PrecioZonaEventoUpdateSerializer, PrecioZonaEventoDetailSerializer)

logger = logging.getLogger(__name__)

class PrecioZonaEventoViewSet(viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsOrganizador()]
    def get_serializer_class(self):
        if self.action == "list":
            return PrecioZonaEventoListSerializer
        if self.action == "retrieve":
            return PrecioZonaEventoDetailSerializer
        if self.action == "create":
            return PrecioZonaEventoCreateSerializer
        if self.action == "update":
            return PrecioZonaEventoUpdateSerializer
        return PrecioZonaEventoDetailSerializer
    
    def list(self, request):
        precio_zona_evento = get_all_precio_zona_evento()
        serializer = self.get_serializer_class()(precio_zona_evento, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        precio_zona_evento = buscar_precio_zona_evento_por_id(pk)
        if not precio_zona_evento:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(precio_zona_evento)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /precio-zona-evento/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /precio-zona-evento/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            precio_zona_evento = crear_precio_zona_evento(
                **serializer.validated_data,
                id_usuario=request.user,
                request=request
            )
            output = PrecioZonaEventoSerializer(precio_zona_evento)
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /precio-zona-evento/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        precio_zona_evento = buscar_precio_zona_evento_por_id(pk)
        if not precio_zona_evento:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            precio_zona_evento_actualizado = actualizar_precio_zona_evento(precio_zona_evento, **serializer.validated_data, id_usuario=request.user, request=request)
            return Response(PrecioZonaEventoSerializer(precio_zona_evento_actualizado).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        precio_zona_evento = buscar_precio_zona_evento_por_id(pk)
        if not precio_zona_evento:
            return Response(status=status.HTTP_404_NOT_FOUND)
        eliminar_precio_zona_evento(precio_zona_evento, id_usuario=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)