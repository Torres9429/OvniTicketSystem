import logging
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from apps.common.permissions import IsOrganizador
from .services import crear_layout, actualizar_layout, activar_layout, desactivar_layout
from .serializers import (LayoutsListSerializer, LayoutsDetailSerializer, LayoutsCreateSerializer, LayoutsUpdateSerializer)
from .models import Layouts
from .selectors import get_layouts_disponibles, get_all_layouts, get_ultima_version_layout_por_lugar

logger = logging.getLogger(__name__)
ERROR_LAYOUT_NO_ENCONTRADO = "Layout no encontrado"

class LayoutsViewSet(viewsets.ModelViewSet):
    queryset = Layouts.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsOrganizador()]

    def get_queryset(self):
        if self.action == "list":
            return get_layouts_disponibles()
        return Layouts.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return LayoutsListSerializer
        if self.action == "retrieve":
            return LayoutsDetailSerializer
        if self.action == "create":
            return LayoutsCreateSerializer
        if self.action == "update":
            return LayoutsUpdateSerializer
        return LayoutsDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /layouts/ — listando layouts disponibles")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /layouts/ — {len(response.data)} layouts retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /layouts/{pk}/ — buscando layout")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /layouts/{pk}/ — layout encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /layouts/{pk}/ — layout no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /layouts/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /layouts/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = crear_layout(**serializer.validated_data, request=request)
            output = LayoutsDetailSerializer(layout)
            logger.info(f"POST /layouts/ — layout creado con id={layout.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /layouts/ — error al crear layout: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /layouts/{pk}/ — payload: {request.data}")
        try:
            layout = Layouts.objects.get(pk=pk)
        except Layouts.DoesNotExist:
            logger.warning(f"PUT /layouts/{pk}/ — layout no encontrado")
            return Response({"error": ERROR_LAYOUT_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(layout, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /layouts/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = actualizar_layout(layout, **serializer.validated_data, request=request)
            output = LayoutsDetailSerializer(layout)
            logger.info(f"PUT /layouts/{pk}/ — layout actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /layouts/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /layouts/{pk}/ — payload: {request.data}")
        try:
            layout = Layouts.objects.get(pk=pk)
        except Layouts.DoesNotExist:
            logger.warning(f"PATCH /layouts/{pk}/ — layout no encontrado")
            return Response({"error": ERROR_LAYOUT_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(layout, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /layouts/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = actualizar_layout(layout, **serializer.validated_data, request=request)
            output = LayoutsDetailSerializer(layout)
            logger.info(f"PATCH /layouts/{pk}/ — layout actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /layouts/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /layouts/{pk}/ — solicitud recibida")
        try:
            Layouts.objects.get(pk=pk)
        except Layouts.DoesNotExist:
            logger.warning(f"DELETE /layouts/{pk}/ — layout no encontrado")
            return Response({"error": ERROR_LAYOUT_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["patch"])
    def deactivate(self, request, pk=None):
        try:
            layout = self.get_object()
            desactivar_layout(layout=layout, id_usuario=request.user, request=request)
            logger.info(f"DELETE /layouts/{pk}/ — layout desactivado")
            return Response({"message": "Layout desactivado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"DELETE /layouts/{pk}/ — error al desactivar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al desactivar el layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["patch"])
    def reactivate(self, request, pk=None):
        layout = self.get_object()
        try:
            activar_layout(layout=layout, id_usuario=request.user, request=request)
            return Response(
                {"message": "Layout reactivado correctamente."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"PATCH /layouts/{pk}/reactivate — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al reactivar el layout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def all(self, request):
        try:
            layouts = get_all_layouts()
            serializer = LayoutsListSerializer(layouts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /layouts/all — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener layouts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["patch"])
    def save_snapshot(self, request, pk=None):
        layout = self.get_object()
        serializer = LayoutsUpdateSerializer(layout, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        layout = actualizar_layout(layout, **serializer.validated_data, request=request)
        output = LayoutsDetailSerializer(layout)
        return Response(output.data, status=status.HTTP_200_OK)


class LayoutUltimaVersionView(APIView):
    def get(self, request, *args, **kwargs):
        id_lugar = request.query_params.get('id_lugar')
        if not id_lugar:
            return Response(
                {"error": "El parámetro id_lugar es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        include_drafts = request.query_params.get('include_drafts', 'false').lower() == 'true'
        layout = get_ultima_version_layout_por_lugar(id_lugar, include_drafts=include_drafts)
        if not layout:
            return Response(
                {"error": "No se encontró un layout para el lugar indicado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "id_layout": layout.id_layout,
                "version": layout.version,
                "estatus": layout.estatus,
                "id_lugar": layout.id_lugar_id,
                "layout": LayoutsDetailSerializer(layout).data,
            },
            status=status.HTTP_200_OK,
        )