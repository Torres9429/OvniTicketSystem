import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Ordenes
from .serializers import (
    OrdenesListSerializer, OrdenesDetailSerializer,
    OrdenesCreateSerializer, OrdenesUpdateSerializer,
)
from .services import crear_orden, actualizar_orden, eliminar_orden
from .selectors import get_all_ordenes, get_ordenes_por_evento, get_ordenes_por_usuario

logger = logging.getLogger(__name__)
ERROR_ORDEN_NO_ENCONTRADA = "Orden no encontrada"


class OrdenesViewSet(viewsets.ModelViewSet):
    queryset = Ordenes.objects.all()

    def get_queryset(self):
        return Ordenes.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return OrdenesListSerializer
        if self.action == "retrieve":
            return OrdenesDetailSerializer
        if self.action == "create":
            return OrdenesCreateSerializer
        if self.action in ("update", "partial_update"):
            return OrdenesUpdateSerializer
        return OrdenesDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /ordenes/ — listando órdenes")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /ordenes/ — {len(response.data)} órdenes retornadas")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /ordenes/{pk}/ — buscando orden")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /ordenes/{pk}/ — orden encontrada")
            return response
        except Exception as e:
            logger.warning(f"GET /ordenes/{pk}/ — orden no encontrada: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /ordenes/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /ordenes/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            orden = crear_orden(**serializer.validated_data)
            output = OrdenesDetailSerializer(orden)
            logger.info(f"POST /ordenes/ — orden creada con id={orden.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /ordenes/ — error al crear orden: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear la orden"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /ordenes/{pk}/ — payload: {request.data}")
        try:
            orden = Ordenes.objects.get(pk=pk)
        except Ordenes.DoesNotExist:
            logger.warning(f"PUT /ordenes/{pk}/ — orden no encontrada")
            return Response({"error": ERROR_ORDEN_NO_ENCONTRADA}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(orden, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /ordenes/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            orden = actualizar_orden(orden, **serializer.validated_data)
            output = OrdenesDetailSerializer(orden)
            logger.info(f"PUT /ordenes/{pk}/ — orden actualizada correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /ordenes/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar la orden"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /ordenes/{pk}/ — payload: {request.data}")
        try:
            orden = Ordenes.objects.get(pk=pk)
        except Ordenes.DoesNotExist:
            logger.warning(f"PATCH /ordenes/{pk}/ — orden no encontrada")
            return Response({"error": ERROR_ORDEN_NO_ENCONTRADA}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(orden, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /ordenes/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            orden = actualizar_orden(orden, **serializer.validated_data)
            output = OrdenesDetailSerializer(orden)
            logger.info(f"PATCH /ordenes/{pk}/ — orden actualizada parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /ordenes/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar la orden"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /ordenes/{pk}/ — solicitud recibida")
        try:
            orden = Ordenes.objects.get(pk=pk)
        except Ordenes.DoesNotExist:
            logger.warning(f"DELETE /ordenes/{pk}/ — orden no encontrada")
            return Response({"error": ERROR_ORDEN_NO_ENCONTRADA}, status=status.HTTP_404_NOT_FOUND)

        try:
            eliminar_orden(orden)
            logger.info(f"DELETE /ordenes/{pk}/ — orden eliminada")
            return Response(
                {"message": "Orden eliminada correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"DELETE /ordenes/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar la orden"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="por-evento/(?P<id_evento>[^/.]+)")
    def por_evento(self, request, id_evento=None):
        logger.debug(f"GET /ordenes/por-evento/{id_evento}/")
        try:
            ordenes = get_ordenes_por_evento(id_evento=id_evento)
            serializer = OrdenesListSerializer(ordenes, many=True)
            logger.info(f"GET /ordenes/por-evento/{id_evento}/ — {ordenes.count()} órdenes")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /ordenes/por-evento/{id_evento}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener órdenes del evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="por-usuario/(?P<id_usuario>[^/.]+)")
    def por_usuario(self, request, id_usuario=None):
        logger.debug(f"GET /ordenes/por-usuario/{id_usuario}/")
        try:
            ordenes = get_ordenes_por_usuario(id_usuario=id_usuario)
            serializer = OrdenesListSerializer(ordenes, many=True)
            logger.info(f"GET /ordenes/por-usuario/{id_usuario}/ — {ordenes.count()} órdenes")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /ordenes/por-usuario/{id_usuario}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener órdenes del usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
