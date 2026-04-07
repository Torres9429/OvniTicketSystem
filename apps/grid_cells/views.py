import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import GridCells
from .serializers import (GridCellsListSerializer, GridCellsDetailSerializer,  GridCellsCreateSerializer, GridCellsUpdateSerializer)
from .services import crear_grid_cell, actualizar_grid_cell, eliminar_grid_cell
from .selectors import get_all_grid_cells, get_grid_cells_por_layout

logger = logging.getLogger(__name__)


class GridCellsViewSet(viewsets.ModelViewSet):
    queryset = GridCells.objects.all()

    not_found_cell = "Celda no encontrada"

    def get_queryset(self):
        return GridCells.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return GridCellsListSerializer
        if self.action == "retrieve":
            return GridCellsDetailSerializer
        if self.action == "create":
            return GridCellsCreateSerializer
        if self.action in ("update", "partial_update"):
            return GridCellsUpdateSerializer
        return GridCellsDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /grid-cells/ — listando celdas")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /grid-cells/ — {len(response.data)} celdas retornadas")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /grid-cells/{pk}/ — buscando celda")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /grid-cells/{pk}/ — celda encontrada")
            return response
        except Exception as e:
            logger.warning(f"GET /grid-cells/{pk}/ — celda no encontrada: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /grid-cells/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /grid-cells/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            grid_cell = crear_grid_cell(**serializer.validated_data, id_usuario=request.user, request=request)
            output = GridCellsDetailSerializer(grid_cell)
            logger.info(f"POST /grid-cells/ — celda creada con id={grid_cell.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /grid-cells/ — error al crear: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear la celda"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /grid-cells/{pk}/ — payload: {request.data}")
        try:
            grid_cell = GridCells.objects.get(pk=pk)
        except GridCells.DoesNotExist:
            logger.warning(f"PUT /grid-cells/{pk}/ — celda no encontrada")
            return Response({"error": not_found_cell}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(grid_cell, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /grid-cells/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            grid_cell = actualizar_grid_cell(grid_cell, **serializer.validated_data, id_usuario=request.user, request=request)
            output = GridCellsDetailSerializer(grid_cell)
            logger.info(f"PUT /grid-cells/{pk}/ — celda actualizada")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /grid-cells/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar la celda"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /grid-cells/{pk}/ — payload: {request.data}")
        try:
            grid_cell = GridCells.objects.get(pk=pk)
        except GridCells.DoesNotExist:
            logger.warning(f"PATCH /grid-cells/{pk}/ — celda no encontrada")
            return Response({"error": not_found_cell}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(grid_cell, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /grid-cells/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            grid_cell = actualizar_grid_cell(grid_cell, **serializer.validated_data, id_usuario=request.user, request=request)
            output = GridCellsDetailSerializer(grid_cell)
            logger.info(f"PATCH /grid-cells/{pk}/ — celda actualizada parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /grid-cells/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar la celda"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /grid-cells/{pk}/ — solicitud recibida")
        try:
            grid_cell = GridCells.objects.get(pk=pk)
        except GridCells.DoesNotExist:
            logger.warning(f"DELETE /grid-cells/{pk}/ — celda no encontrada")
            return Response({"error": not_found_cell}, status=status.HTTP_404_NOT_FOUND)

        try:
            eliminar_grid_cell(grid_cell, id_usuario=request.user, request=request)
            logger.info(f"DELETE /grid-cells/{pk}/ — celda eliminada")
            return Response(
                {"message": "Celda eliminada correctamente"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"DELETE /grid-cells/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar la celda"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path="por-layout/(?P<id_layout>[^/.]+)")
    def por_layout(self, request, id_layout=None):
        logger.debug(f"GET /grid-cells/por-layout/{id_layout}/")
        try:
            celdas = get_grid_cells_por_layout(id_layout=id_layout)
            serializer = GridCellsListSerializer(celdas, many=True)
            logger.info(f"GET /grid-cells/por-layout/{id_layout}/ — {celdas.count()} celdas")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /grid-cells/por-layout/{id_layout}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener celdas del layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )