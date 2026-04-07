import logging
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.utils import timezone
from .services import crear_evento, actualizar_evento, activar_evento, desactivar_evento, eliminar_evento
from .serializers import (EventosListSerializer, EventosDetailSerializer, EventosCreateSerializer, EventosUpdateSerializer)
from .models import Eventos
from .selectors import get_eventos_disponibles, get_all_eventos

logger = logging.getLogger(__name__)

class EventosViewSet(viewsets.ModelViewSet):
    queryset = Eventos.objects.all()

    def get_queryset(self):
        if self.action == "list":
            return get_eventos_disponibles()
        return Eventos.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return EventosListSerializer
        if self.action == "retrieve":
            return EventosDetailSerializer
        if self.action == "create":
            return EventosCreateSerializer
        if self.action == "update":
            return EventosUpdateSerializer
        return EventosDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /eventos/ — listando eventos disponibles")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /eventos/ — {len(response.data)} eventos retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /eventos/{pk}/ — buscando evento")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /eventos/{pk}/ — evento encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /eventos/{pk}/ — evento no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /eventos/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /eventos/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            evento = crear_evento(**serializer.validated_data, id_usuario=request.user, request=request)
            output = EventosDetailSerializer(evento)
            logger.info(f"POST /eventos/ — evento creado con id={evento.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /eventos/ — error al crear evento: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /eventos/{pk}/ — payload: {request.data}")
        try:
            evento = Eventos.objects.get(pk=pk)
        except Eventos.DoesNotExist:
            logger.warning(f"PUT /eventos/{pk}/ — evento no encontrado")
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(evento, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /eventos/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            evento = actualizar_evento(evento, **serializer.validated_data, id_usuario=request.user, request=request)
            output = EventosDetailSerializer(evento)
            logger.info(f"PUT /eventos/{pk}/ — evento actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /eventos/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /eventos/{pk}/ — payload: {request.data}")
        try:
            evento = Eventos.objects.get(pk=pk)
            logger.info("Evento encontrado en bd")
        except Eventos.DoesNotExist:
            logger.warning(f"PATCH /eventos/{pk}/ — evento no encontrado")
            return Response({"error": "El Evento no fue encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(evento, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /eventos/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            evento = actualizar_evento(evento, **serializer.validated_data, id_usuario=request.user, request=request)
            output = EventosDetailSerializer(evento)
            logger.info(f"PATCH /eventos/{pk}/ — evento actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /eventos/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /eventos/{pk}/ — solicitud recibida")
        try:
            evento = Eventos.objects.get(pk=pk)
            logger.info(f"Evento encontrado: {evento}")
        except Eventos.DoesNotExist:
            logger.warning(f"DELETE /eventos/{pk}/ — evento no encontrado")
            return Response({"error": "No se encontró el evento"}, status=status.HTTP_404_NOT_FOUND)
        try:
            eliminar_evento(evento=evento, id_usuario=request.user, request=request)
            logger.info(f"DELETE /eventos/{pk}/ — evento eliminado correctamente")
            return Response({"message": "Evento eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"DELETE /eventos/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



    @action(detail=True, methods=["patch"])
    def deactivate(self, request, pk=None):
        try:
            evento = self.get_object()
            desactivar_evento(evento=evento, id_usuario=request.user, request=request)
            logger.info(f"DELETE /eventos/{pk}/ — evento desactivado")
            return Response({"message": "Evento desactivado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"DELETE /eventos/{pk}/ — error al desactivar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al desactivar el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["patch"])
    def reactivate(self, request, pk=None):
        evento = self.get_object()
        try: 
            activar_evento(evento=evento, id_usuario=request.user, request=request)
            return Response(
                {"message": "Evento reactivado correctamente."},
                status=status.HTTP_200_OK
            )
        except Exception as e: 
            logger.error(f"PATCH /eventos/{pk}/ — error al reactivar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al reactivar el evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def all(self, request):
        try:
            eventos = get_all_eventos()
            serializer = EventosListSerializer(eventos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /eventos/ — error al listar: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener eventos"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )