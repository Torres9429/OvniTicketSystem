import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOrganizador
from .selectors import get_all_asientos, get_asiento_by_id
from .models import EstadoAsientoEvento
from .services import (
    create_asiento, update_asiento, delete_asiento,
    obtener_disponibilidad_evento, inicializar_estado_asientos,
    retener_asientos, confirmar_compra, liberar_asientos_usuario,
    SeatUnavailableError, _liberar_expirados,
    resolve_layout_seat_refs_to_grid_cells,
    build_layout_seat_key,
    obtener_recomendacion_asientos,
)
from .serializers import (
    AsientosListSerializer,
    AsientosDetailSerializer,
    AsientosCreateSerializer,
    AsientosUpdateSerializer,
)

logger = logging.getLogger(__name__)


class AsientosViewSet(viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsOrganizador()]

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
        asiento = create_asiento(serializer.validated_data, id_usuario=request.user, request=request)
        return Response(AsientosDetailSerializer(asiento).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        asiento = get_asiento_by_id(pk)
        if not asiento:
            return Response({'error': 'Asiento no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        asiento = update_asiento(asiento, serializer.validated_data, id_usuario=request.user, request=request)
        return Response(AsientosDetailSerializer(asiento).data)

    def destroy(self, request, pk=None):
        asiento = get_asiento_by_id(pk)
        if not asiento:
            return Response({'error': 'No se pudo encontrar el asiento'}, status=status.HTTP_404_NOT_FOUND)
        delete_asiento(asiento, id_usuario=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class DisponibilidadAsientosView(APIView):
    """GET /api/asientos/disponibilidad/<id_evento>/
    Returns seat states for an event. Auto-initialises state rows if needed."""
    permission_classes = [AllowAny]

    def get(self, request, id_evento):
        from apps.eventos.models import Eventos
        try:
            evento = Eventos.objects.get(pk=id_evento)
        except Eventos.DoesNotExist:
            return Response({'error': 'Evento no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        inicializar_estado_asientos(id_evento, evento.id_version_id)

        disponibilidad_raw = list(obtener_disponibilidad_evento(id_evento))
        disponibilidad = [
            {
                'id_grid_cell': item['id_grid_cell'],
                'estado': item['estado'],
                'row': item['id_grid_cell__row'],
                'col': item['id_grid_cell__col'],
                'zone_id': item['id_grid_cell__id_zona_id'],
                'seat_key': build_layout_seat_key(
                    item['id_grid_cell__row'],
                    item['id_grid_cell__col'],
                    item['id_grid_cell__id_zona_id'],
                ),
            }
            for item in disponibilidad_raw
        ]
        return Response(disponibilidad, status=status.HTTP_200_OK)


class RetenerAsientosView(APIView):
    """POST /api/asientos/retener/
    Body: { id_evento, ids_grid_cell: [int, ...] }"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.eventos.models import Eventos

        id_evento = request.data.get('id_evento')
        ids_grid_cell = request.data.get('ids_grid_cell', [])
        asientos_layout = request.data.get('asientos_layout', [])

        try:
            evento = Eventos.objects.get(pk=id_evento)
            inicializar_estado_asientos(id_evento, evento.id_version_id)
        except Eventos.DoesNotExist:
            return Response({'error': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not ids_grid_cell and asientos_layout:
            try:
                ids_grid_cell = resolve_layout_seat_refs_to_grid_cells(
                    id_evento,
                    asientos_layout,
                )
            except SeatUnavailableError as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            except Exception:
                return Response(
                    {'error': 'No se pudieron resolver los asientos del layout.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not id_evento or not ids_grid_cell:
            return Response(
                {'error': 'id_evento y una lista de asientos son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = retener_asientos(id_evento, ids_grid_cell, request.user)
            return Response(
                {
                    'message': 'Asientos retenidos correctamente.',
                    'retenido_hasta': result['retenido_hasta'],
                    'ids_grid_cell': result['ids_grid_cell'],
                },
                status=status.HTTP_200_OK,
            )
        except SeatUnavailableError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)


class LiberarAsientosView(APIView):
    """POST /api/asientos/liberar/
    Body: { id_evento }"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_evento = request.data.get('id_evento')
        if not id_evento:
            return Response({'error': 'id_evento es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        count = liberar_asientos_usuario(id_evento, request.user)
        return Response({'message': f'{count} asiento(s) liberado(s).'}, status=status.HTTP_200_OK)


class ConfirmarCompraView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.eventos.models import Eventos

        id_evento = request.data.get('id_evento')
        ids_grid_cell = request.data.get('ids_grid_cell', [])
        asientos_layout = request.data.get('asientos_layout', [])

        try:
            evento = Eventos.objects.get(pk=id_evento)
            inicializar_estado_asientos(id_evento, evento.id_version_id)
        except Eventos.DoesNotExist:
            return Response({'error': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not ids_grid_cell and asientos_layout:
            try:
                ids_grid_cell = resolve_layout_seat_refs_to_grid_cells(
                    id_evento,
                    asientos_layout,
                )
            except SeatUnavailableError as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            except Exception:
                return Response(
                    {'error': 'No se pudieron resolver los asientos del layout.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not id_evento or not ids_grid_cell:
            return Response(
                {'error': 'id_evento y una lista de asientos son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            confirmar_compra(id_evento, ids_grid_cell, request.user)
            return Response({'message': 'Compra confirmada.'}, status=status.HTTP_200_OK)
        except SeatUnavailableError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)


class HoldStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_evento):
        _liberar_expirados(id_evento)

        holds = list(
            EstadoAsientoEvento.objects.filter(
                id_evento=id_evento,
                estado=EstadoAsientoEvento.RETENIDO,
                retenido_por=request.user,
            )
        )

        if not holds:
            return Response(
                {
                    'tiene_retencion': False,
                    'retenido_hasta': None,
                    'ids_grid_cell': [],
                },
                status=status.HTTP_200_OK,
            )

        max_expiry = max(h.retenido_hasta for h in holds)
        ids_grid_cell = [h.id_grid_cell_id for h in holds]
        asientos_layout = [
            {
                'row': h.id_grid_cell.row,
                'col': h.id_grid_cell.col,
                'zone_id': h.id_grid_cell.id_zona_id,
                'seat_key': build_layout_seat_key(
                    h.id_grid_cell.row,
                    h.id_grid_cell.col,
                    h.id_grid_cell.id_zona_id,
                ),
            }
            for h in holds
        ]

        return Response(
            {
                'tiene_retencion': True,
                'retenido_hasta': max_expiry.isoformat(),
                'ids_grid_cell': ids_grid_cell,
                'asientos_layout': asientos_layout,
            },
            status=status.HTTP_200_OK,
        )


class RecomendacionAsientosView(APIView):
    """GET /api/asientos/recomendacion/
    Returns recommended seat IDs (2-3 continuous seats close to stage).
    Query params: id_evento, id_layout
    """
    permission_classes = [AllowAny]

    def get(self, request):
        id_evento = request.query_params.get('id_evento')
        id_layout = request.query_params.get('id_layout')

        if not id_evento or not id_layout:
            return Response(
                {'error': 'id_evento y id_layout son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            id_evento = int(id_evento)
            id_layout = int(id_layout)
        except (TypeError, ValueError):
            return Response(
                {'error': 'id_evento e id_layout deben ser números.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommended_ids = obtener_recomendacion_asientos(id_evento, id_layout)

        return Response(
            {'asientos': recommended_ids},
            status=status.HTTP_200_OK
        )