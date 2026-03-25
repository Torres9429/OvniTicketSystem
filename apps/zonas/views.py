from rest_framework import viewsets
from .services import crear_zona, actualizar_zona, eliminar_zona
from .selectors import get_all_zonas, buscar_zona_por_id, buscar_zona_por_nombre, buscar_zona_por_color, buscar_zona_por_fecha_creacion, buscar_zona_por_layout
from .serializers import (ZonasSerializer, ZonasListSerializer, ZonasCreateSerializer, ZonasUpdateSerializer, ZonasDetailSerializer)
from rest_framework.response import Response
from rest_framework import status

class ZonasViewSet(viewsets.ViewSet):
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
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            zona = crear_zona(serializer.validated_data)
            return Response(ZonasSerializer(zona).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        zona = buscar_zona_por_id(pk)
        if not zona:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            zona_actualizada = actualizar_zona(zona, **serializer.validated_data)
            return Response(ZonasSerializer(zona_actualizada).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)