import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.asientos.services import SeatUnavailableError
from apps.common.permissions import IsAdmin

from .models import Ordenes
from .purchase import EventPricingError, PaymentFailedError, ejecutar_compra
from .selectors import (
    get_all_ordenes,
    get_dashboard_ventas_por_organizador,
    get_ordenes_por_evento,
    get_ordenes_por_usuario,
)
from .serializers import (
    OrdenesCreateSerializer,
    OrdenesDetailSerializer,
    OrdenesListSerializer,
    OrdenesUpdateSerializer,
)
from .services import DuplicateOrderError, actualizar_orden, crear_orden, eliminar_orden

logger = logging.getLogger(__name__)
ERROR_ORDEN_NO_ENCONTRADA = "Orden no encontrada"


class ComprarView(APIView):
    """
    POST /api/ordenes/comprar/

    Body
    ----
    {
        "id_evento": <int>,
        "ids_grid_cell": [<int>, ...],
        "metodo_pago": "mock"          // optional, defaults to "mock"
        "token": "<str>"               // optional gateway token
    }

    Success → 201
    {
        "orden": {
            "id_orden": <int>,
            "total": <float>,
            "estatus": "pagado",
            "fecha_creacion": "<iso8601>"
        },
        "tickets": [
            {
                "id_ticket": <int>,
                "precio": <float>,
                "id_grid_cell": <int>,
                "id_evento": <int>
            },
            ...
        ],
        "transaction_id": "<str>"
    }

    Failure (seat no longer held) → 409
    Failure (payment declined)    → 402
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        id_evento = data.get("id_evento")
        ids_grid_cell = data.get("ids_grid_cell")
        metodo_pago = data.get("metodo_pago", "mock")
        token = data.get("token", None)
        operation_id = data.get("operation_id", None)

        if operation_id is not None:
            if not isinstance(operation_id, str) or len(operation_id) > 64:
                return Response(
                    {"error": "'operation_id' debe ser una cadena de hasta 64 caracteres."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not id_evento or not ids_grid_cell:
            return Response(
                {"error": "Se requieren 'id_evento' e 'ids_grid_cell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(ids_grid_cell, list) or len(ids_grid_cell) == 0:
            return Response(
                {"error": "'ids_grid_cell' debe ser una lista no vacía."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.debug(
            "POST /api/ordenes/comprar/ — usuario=%s evento=%s cells=%s",
            request.user.pk, id_evento, ids_grid_cell,
        )

        try:
            result = ejecutar_compra(
                id_evento=id_evento,
                ids_grid_cell=ids_grid_cell,
                usuario=request.user,
                metodo_pago=metodo_pago,
                token=token,
                operation_id=operation_id,
                request=request,
            )
        except EventPricingError as exc:
            logger.warning(
                "POST /api/ordenes/comprar/ — event pricing error: %s (zonas=%s)",
                exc, exc.zonas_sin_precio,
            )
            return Response(
                {
                    "error": str(exc),
                    "codigo": "EVENT_PRICING_MISSING",
                    "zonas_sin_precio": exc.zonas_sin_precio,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except SeatUnavailableError as exc:
            logger.warning(
                "POST /api/ordenes/comprar/ — seat unavailable: %s", exc
            )
            return Response(
                {"error": str(exc), "codigo": "SEAT_UNAVAILABLE"},
                status=status.HTTP_409_CONFLICT,
            )
        except PaymentFailedError as exc:
            logger.warning(
                "POST /api/ordenes/comprar/ — payment failed: %s (gateway: %s)",
                exc, exc.gateway_error,
            )
            return Response(
                {"error": str(exc), "detalle": exc.gateway_error},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except Exception as exc:
            logger.error(
                "POST /api/ordenes/comprar/ — unexpected error: %s",
                exc, exc_info=True,
            )
            return Response(
                {"error": "Error interno al procesar la compra."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        orden = result["orden"]
        tickets = result["tickets"]
        transaction_id = result.get("transaction_id", "")

        logger.info(
            "POST /api/ordenes/comprar/ — orden=%s tickets=%s usuario=%s",
            orden.pk, [t.pk for t in tickets], request.user.pk,
        )

        return Response(
            {
                "orden": {
                    "id_orden": orden.pk,
                    "total": orden.total,
                    "estatus": orden.estatus,
                    "fecha_creacion": orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                },
                "tickets": [
                    {
                        "id_ticket": t.pk,
                        "precio": t.precio,
                        "id_grid_cell": t.id_grid_cell_id,
                        "id_evento": t.id_evento_id,
                    }
                    for t in tickets
                ],
                "transaction_id": transaction_id,
            },
            status=status.HTTP_201_CREATED,
        )



class OrdenesViewSet(viewsets.ModelViewSet):
    queryset = Ordenes.objects.all()

    def get_permissions(self):
        if self.action in (
            'create', 'list', 'retrieve',
            'detalle', 'por_usuario', 'mis_ventas',
        ):
            return [IsAuthenticated()]
        return [IsAdmin()]

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
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /ordenes/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            orden = crear_orden(**serializer.validated_data, id_usuario=request.user, request=request)
            output = OrdenesDetailSerializer(orden)
            logger.info(f"POST /ordenes/ — orden creada con id={orden.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except DuplicateOrderError as e:
            logger.warning(f"POST /ordenes/ — intento de duplicidad: {e}")
            return Response(
                {"error": str(e), "codigo": "ORDEN_DUPLICADA"},
                status=status.HTTP_409_CONFLICT,
            )
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
            orden = actualizar_orden(orden, **serializer.validated_data, id_usuario=request.user, request=request)
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
            orden = actualizar_orden(orden, **serializer.validated_data, id_usuario=request.user, request=request)
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
            eliminar_orden(orden, id_usuario=request.user, request=request)
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

    def _es_admin(self, user):
        rol = getattr(user, "id_rol", None)
        rol_nombre = str(getattr(rol, "nombre", "")).lower()
        return bool(getattr(user, "id_rol_id", None) and rol_nombre == "admin")

    def _obtener_contexto_ventas(self, usuario):
        from django.db.models import Sum, Count
        from apps.eventos.models import Eventos
        from apps.tickets.models import Tickets

        eventos_qs = Eventos.objects.filter(
            id_lugar__id_dueno=usuario
        ).order_by('-fecha_inicio')
        evento_ids = list(eventos_qs.values_list('id_evento', flat=True))

        ordenes_pagadas = Ordenes.objects.filter(
            id_evento__in=evento_ids,
            estatus=Ordenes.ESTATUS_PAGADO,
        )
        ordenes_pendientes_count = Ordenes.objects.filter(
            id_evento__in=evento_ids,
            estatus=Ordenes.ESTATUS_PENDIENTE,
        ).count()

        agregados = ordenes_pagadas.aggregate(
            total_vendido=Sum('total'),
            ordenes_count=Count('id_orden'),
        )

        total_vendido = float(agregados['total_vendido'] or 0)
        ordenes_pagadas_count = int(agregados['ordenes_count'] or 0)
        boletos_vendidos = Tickets.objects.filter(id_orden__in=ordenes_pagadas).count()

        return (
            eventos_qs,
            ordenes_pagadas,
            total_vendido,
            ordenes_pagadas_count,
            ordenes_pendientes_count,
            boletos_vendidos,
        )

    def _construir_eventos_payload(self, eventos_qs, ordenes_pagadas):
        from django.db.models import Sum
        from apps.tickets.models import Tickets
        from apps.grid_cells.models import GridCells

        eventos_payload = []
        for ev in eventos_qs:
            ev_ordenes_pagadas = ordenes_pagadas.filter(id_evento=ev)
            ev_revenue = float(
                ev_ordenes_pagadas.aggregate(total=Sum('total'))['total'] or 0
            )
            ev_tickets = Tickets.objects.filter(
                id_orden__in=ev_ordenes_pagadas
            ).count()

            capacidad = GridCells.objects.filter(
                id_layout=ev.id_version_id, tipo='ZONA DE ASIENTOS'
            ).count()
            ocupacion = round((ev_tickets / capacidad) * 100, 1) if capacidad else 0.0

            eventos_payload.append({
                "id_evento": ev.pk,
                "nombre": ev.nombre,
                "fecha_inicio": ev.fecha_inicio.isoformat() if ev.fecha_inicio else None,
                "estatus": ev.estatus,
                "boletos_vendidos": ev_tickets,
                "asientos_totales": capacidad,
                "ocupacion_pct": ocupacion,
                "revenue": ev_revenue,
            })

        return eventos_payload

    def _obtener_comprador(self, orden):
        if not orden.id_usuario_id:
            return None
        try:
            return orden.id_usuario.correo
        except Exception:
            return None

    def _construir_ordenes_recientes_payload(self, eventos_qs, ordenes_pagadas):
        eventos_nombre_map = {e.pk: e.nombre for e in eventos_qs}
        recientes = list(ordenes_pagadas.order_by('-fecha_creacion')[:10])
        payload = []

        for o in recientes:
            payload.append({
                "id_orden": o.pk,
                "fecha_creacion": o.fecha_creacion.isoformat() if o.fecha_creacion else None,
                "id_evento": o.id_evento_id,
                "nombre_evento": eventos_nombre_map.get(
                    o.id_evento_id, f"Evento #{o.id_evento_id}"
                ),
                "total": float(o.total or 0),
                "estatus": o.estatus,
                "comprador": self._obtener_comprador(o),
            })

        return payload

    def _obtener_grid_cells_y_zonas(self, tickets):
        from apps.zonas.models import Zonas
        from apps.grid_cells.models import GridCells

        grid_cell_ids = [t.id_grid_cell_id for t in tickets if t.id_grid_cell_id]
        grid_cells_by_id = {}
        zonas_by_id = {}

        if not grid_cell_ids:
            return grid_cells_by_id, zonas_by_id

        for gc in GridCells.objects.filter(id_grid_cells__in=grid_cell_ids):
            grid_cells_by_id[gc.id_grid_cells] = gc

        zona_ids = {gc.id_zona_id for gc in grid_cells_by_id.values() if gc.id_zona_id}
        if zona_ids:
            for z in Zonas.objects.filter(pk__in=zona_ids):
                zonas_by_id[z.pk] = z

        return grid_cells_by_id, zonas_by_id

    def _construir_tickets_payload(self, tickets):
        grid_cells_by_id, zonas_by_id = self._obtener_grid_cells_y_zonas(tickets)
        payload = []

        for t in tickets:
            gc = grid_cells_by_id.get(t.id_grid_cell_id)
            zona = zonas_by_id.get(gc.id_zona_id) if gc else None

            label = None
            if gc is not None and gc.row is not None and gc.col is not None:
                label = f"F{gc.row + 1}-C{gc.col + 1}"

            payload.append(
                {
                    "id_ticket": t.pk,
                    "precio": float(t.precio) if t.precio is not None else 0.0,
                    "id_grid_cell": t.id_grid_cell_id,
                    "id_evento": t.id_evento_id,
                    "label": label,
                    "zona": zona.nombre if zona else None,
                }
            )

        return payload

    def _obtener_evento_payload(self, id_evento):
        from apps.eventos.models import Eventos

        try:
            ev = Eventos.objects.get(pk=id_evento)
        except Eventos.DoesNotExist:
            return None

        return {
            "id_evento": ev.pk,
            "nombre": ev.nombre,
            "descripcion": ev.descripcion,
            "fecha_inicio": ev.fecha_inicio.isoformat() if ev.fecha_inicio else None,
            "fecha_fin": ev.fecha_fin.isoformat() if ev.fecha_fin else None,
            "estatus": ev.estatus,
        }

    @action(detail=False, methods=["get"], url_path="mis-ventas")
    def mis_ventas(self, request):
        """GET /api/ordenes/mis-ventas/
        Sales dashboard for the authenticated organizer. Aggregates all orders
        and tickets across events whose venue is owned by request.user.

        Response:
        {
          "resumen": {
            "total_vendido": float,
            "boletos_vendidos": int,
            "ordenes_pagadas": int,
            "ordenes_pendientes": int,
            "eventos_totales": int,
            "eventos_con_ventas": int,
          },
          "eventos": [
            {
              "id_evento", "nombre", "fecha_inicio", "estatus",
              "boletos_vendidos", "asientos_totales", "ocupacion_pct", "revenue"
            }, ...
          ],
          "ordenes_recientes": [
            {
              "id_orden", "fecha_creacion", "id_evento", "nombre_evento",
              "total", "estatus", "comprador"
            }, ...10 máx
          ]
        }
        """
        payload = get_dashboard_ventas_por_organizador(request.user.pk)

        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="detalle")
    def detalle(self, request, pk=None):
        """GET /api/ordenes/<id>/detalle/ — returns full order with tickets + event.
        This is the authoritative source for the confirmation/receipt page
        instead of relying on navigation state that can get corrupted."""
        from apps.tickets.models import Tickets

        try:
            orden = Ordenes.objects.get(pk=pk)
        except Ordenes.DoesNotExist:
            return Response(
                {"error": ERROR_ORDEN_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_admin = self._es_admin(request.user)
        if not is_admin and orden.id_usuario_id != request.user.pk:
            return Response(
                {"error": "No tienes permiso para ver esta orden."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tickets = list(Tickets.objects.filter(id_orden=orden))
        tickets_payload = self._construir_tickets_payload(tickets)
        evento_payload = self._obtener_evento_payload(orden.id_evento_id)

        return Response(
            {
                "orden": {
                    "id_orden": orden.pk,
                    "total": float(orden.total) if orden.total is not None else 0.0,
                    "estatus": orden.estatus,
                    "fecha_creacion": orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                    "operation_id": orden.operation_id,
                },
                "tickets": tickets_payload,
                "evento": evento_payload,
            },
            status=status.HTTP_200_OK,
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