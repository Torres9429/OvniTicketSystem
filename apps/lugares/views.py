import logging
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.utils import timezone
from .services import crear_lugar, actualizar_lugar, activar_lugar, desactivar_lugar
from .serializers import (LugaresListSerializer, LugaresDetailSerializer, LugaresCreateSerializer, LugaresUpdateSerializer)
from .models import Lugares
from .selectors import get_lugares_disponibles, get_all_lugares

logger = logging.getLogger(__name__)

class LugaresViewSet(viewsets.ModelViewSet):
    queryset = Lugares.objects.all()

    def get_queryset(self):
        if self.action == "list":
            return get_lugares_disponibles()
        return Lugares.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return LugaresListSerializer
        if self.action == "retrieve":
            return LugaresDetailSerializer
        if self.action == "create":
            return LugaresCreateSerializer
        if self.action == "update":
            return LugaresUpdateSerializer
        return LugaresDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /lugares/ — listando lugares disponibles")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /lugares/ — {len(response.data)} lugares retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /lugares/{pk}/ — buscando lugar")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /lugares/{pk}/ — lugar encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /lugares/{pk}/ — lugar no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /lugares/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /lugares/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            lugar = crear_lugar(**serializer.validated_data, request=request)
            output = LugaresDetailSerializer(lugar)
            logger.info(f"POST /lugares/ — lugar creado con id={lugar.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /lugares/ — error al crear lugar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el lugar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /lugares/{pk}/ — payload: {request.data}")
        try:
            lugar = Lugares.objects.get(pk=pk)
        except Lugares.DoesNotExist:
            logger.warning(f"PUT /lugares/{pk}/ — lugar no encontrado")
            return Response({"error": "Lugar no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(lugar, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /lugares/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            lugar = actualizar_lugar(lugar, **serializer.validated_data, request=request)
            output = LugaresDetailSerializer(lugar)
            logger.info(f"PUT /lugares/{pk}/ — lugar actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /lugares/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el lugar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /lugares/{pk}/ — payload: {request.data}")
        try:
            lugar = Lugares.objects.get(pk=pk)
        except Lugares.DoesNotExist:
            logger.warning(f"PATCH /lugares/{pk}/ — lugar no encontrado")
            return Response({"error": "Lugar no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(lugar, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /lugares/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            lugar = actualizar_lugar(lugar, **serializer.validated_data, request=request)
            output = LugaresDetailSerializer(lugar)
            logger.info(f"PATCH /lugares/{pk}/ — lugar actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /lugares/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el lugar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /lugares/{pk}/ — solicitud recibida")
        try:
            lugar = Lugares.objects.get(pk=pk)
        except Lugares.DoesNotExist:
            logger.warning(f"DELETE /lugares/{pk}/ — lugar no encontrado")
            return Response({"error": "Lugar no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["patch"])
    def deactivate(self, request, pk=None):
        try:
            lugar = self.get_object()
            desactivar_lugar(lugar=lugar, id_usuario=request.user, request=request)
            logger.info(f"DELETE /lugares/{pk}/ — lugar desactivado")
            return Response({"message": "Lugar desactivado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"DELETE /lugares/{pk}/ — error al desactivar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al desactivar el lugar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["patch"])
    def reactivate(self, request, pk=None):
        lugar = self.get_object()
        try:
            activar_lugar(lugar=lugar, id_usuario=request.user, request=request)
            return Response(
                {"message": "Lugar reactivado correctamente."},
                status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "Error interno al reactivar el lugar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def all(self, request):
        try:
            lugares = get_all_lugares()
            serializer = LugaresListSerializer(lugares, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Error al obtener lugares"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
