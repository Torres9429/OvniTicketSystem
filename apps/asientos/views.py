from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.response import Response
from .selectors import get_all_asientos, get_asiento_by_id
from .services import create_asiento, update_asiento, delete_asiento
from .serializers import (
    AsientosListSerializer,
    AsientosDetailSerializer,
    AsientosCreateSerializer,
    AsientosUpdateSerializer
)


class AsientosViewSet(viewsets.ViewSet):

    def get_serializer_class(self):
        if self.action == 'list':
            return AsientosListSerializer
        elif self.action == 'retrieve':
            return AsientosDetailSerializer
        elif self.action == 'create':
            return AsientosCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AsientosUpdateSerializer
        return AsientosDetailSerializer

    def list(self, request):
        asientos = get_all_asientos()
        serializer = self.get_serializer_class()(asientos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        asiento = get_asiento_by_id(pk)
        if not asiento:
            return Response({'error': 'El asiento no fue encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(asiento)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        asiento = create_asiento(serializer.validated_data)
        return Response(AsientosDetailSerializer(asiento).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        asiento = get_asiento_by_id(pk)
        if not asiento:
            return Response({'error': 'Asiento no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        asiento = update_asiento(asiento, serializer.validated_data)
        return Response(AsientosDetailSerializer(asiento).data)

    def destroy(self, request, pk=None):
        asiento = get_asiento_by_id(pk)
        if not asiento:
            return Response({'error': 'No se pudo encontrar el asiento'}, status=status.HTTP_404_NOT_FOUND)
        delete_asiento(asiento)
        return Response(status=status.HTTP_204_NO_CONTENT)