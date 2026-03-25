from rest_framework import viewsets, status
from .services import crear_precio_zona_evento, actualizar_precio_zona_evento, eliminar_precio_zona_evento
from .selectors import get_all_precio_zona_evento, buscar_precio_zona_evento_por_id
from .serializers import (PrecioZonaEventoSerializer, PrecioZonaEventoListSerializer, PrecioZonaEventoCreateSerializer, PrecioZonaEventoUpdateSerializer, PrecioZonaEventoDetailSerializer)
from rest_framework.response import Response

class PrecioZonaEventoViewSet(viewsets.ViewSet):
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
        serializer = self.get_serializer_class()(precio_zona_evento, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            precio_zona_evento = crear_precio_zona_evento(**serializer.validated_data)
            return Response(PrecioZonaEventoSerializer(precio_zona_evento).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        precio_zona_evento = buscar_precio_zona_evento_por_id(pk)
        if not precio_zona_evento:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            precio_zona_evento_actualizado = actualizar_precio_zona_evento(precio_zona_evento[0], **serializer.validated_data)
            return Response(PrecioZonaEventoSerializer(precio_zona_evento_actualizado).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        precio_zona_evento = buscar_precio_zona_evento_por_id(pk)
        if not precio_zona_evento:
            return Response(status=status.HTTP_404_NOT_FOUND)
        eliminar_precio_zona_evento(precio_zona_evento[0])
        return Response(status=status.HTTP_204_NO_CONTENT)