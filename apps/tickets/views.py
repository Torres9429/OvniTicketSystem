import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Tickets
from .serializers import (
    TicketsListSerializer, TicketsDetailSerializer,
    TicketsCreateSerializer, TicketsUpdateSerializer,
)
from .services import crear_ticket, actualizar_ticket, eliminar_ticket
from .selectors import get_all_tickets, get_tickets_por_orden, get_tickets_por_evento

logger = logging.getLogger(__name__)
ERROR_TICKET_NO_ENCONTRADO = "Ticket no encontrado"


class TicketsViewSet(viewsets.ModelViewSet):
    queryset = Tickets.objects.all()

    def get_queryset(self):
        return Tickets.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return TicketsListSerializer
        if self.action == "retrieve":
            return TicketsDetailSerializer
        if self.action == "create":
            return TicketsCreateSerializer
        if self.action in ("update", "partial_update"):
            return TicketsUpdateSerializer
        return TicketsDetailSerializer

    def list(self, request, *args, **kwargs):
        logger.debug("GET /tickets/ — listando tickets")
        response = super().list(request, *args, **kwargs)
        logger.info(f"GET /tickets/ — {len(response.data)} tickets retornados")
        return response

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET /tickets/{pk}/ — buscando ticket")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET /tickets/{pk}/ — ticket encontrado")
            return response
        except Exception as e:
            logger.warning(f"GET /tickets/{pk}/ — ticket no encontrado: {e}")
            raise

    def create(self, request, *args, **kwargs):
        logger.debug(f"POST /tickets/ — payload: {request.data}")
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"POST /tickets/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = crear_ticket(**serializer.validated_data, id_usuario=request.user, request=request)
            output = TicketsDetailSerializer(ticket)
            logger.info(f"POST /tickets/ — ticket creado con id={ticket.pk}")
            return Response(output.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"POST /tickets/ — error al crear ticket: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al crear el ticket"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PUT /tickets/{pk}/ — payload: {request.data}")
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            logger.warning(f"PUT /tickets/{pk}/ — ticket no encontrado")
            return Response({"error": ERROR_TICKET_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(ticket, data=request.data)

        if not serializer.is_valid():
            logger.warning(f"PUT /tickets/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = actualizar_ticket(ticket, **serializer.validated_data, id_usuario=request.user, request=request)
            output = TicketsDetailSerializer(ticket)
            logger.info(f"PUT /tickets/{pk}/ — ticket actualizado correctamente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PUT /tickets/{pk}/ — error al actualizar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el ticket"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        logger.debug(f"PATCH /tickets/{pk}/ — payload: {request.data}")
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            logger.warning(f"PATCH /tickets/{pk}/ — ticket no encontrado")
            return Response({"error": ERROR_TICKET_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(ticket, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"PATCH /tickets/{pk}/ — validación fallida: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = actualizar_ticket(ticket, **serializer.validated_data)
            output = TicketsDetailSerializer(ticket)
            logger.info(f"PATCH /tickets/{pk}/ — ticket actualizado parcialmente")
            return Response(output.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"PATCH /tickets/{pk}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al actualizar el ticket"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.debug(f"DELETE /tickets/{pk}/ — solicitud recibida")
        try:
            ticket = Tickets.objects.get(pk=pk)
        except Tickets.DoesNotExist:
            logger.warning(f"DELETE /tickets/{pk}/ — ticket no encontrado")
            return Response({"error": ERROR_TICKET_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

        try:
            eliminar_ticket(ticket, id_usuario=request.user, request=request)
            logger.info(f"DELETE /tickets/{pk}/ — ticket eliminado")
            return Response(
                {"message": "Ticket eliminado correctamente"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"DELETE /tickets/{pk}/ — error al eliminar: {e}", exc_info=True)
            return Response(
                {"error": "Error interno al eliminar el ticket"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="por-orden/(?P<id_orden>[^/.]+)")
    def por_orden(self, request, id_orden=None):
        logger.debug(f"GET /tickets/por-orden/{id_orden}/")
        try:
            tickets = get_tickets_por_orden(id_orden=id_orden)
            serializer = TicketsListSerializer(tickets, many=True)
            logger.info(f"GET /tickets/por-orden/{id_orden}/ — {tickets.count()} tickets")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /tickets/por-orden/{id_orden}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener tickets de la orden"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="por-evento/(?P<id_evento>[^/.]+)")
    def por_evento(self, request, id_evento=None):
        logger.debug(f"GET /tickets/por-evento/{id_evento}/")
        try:
            tickets = get_tickets_por_evento(id_evento=id_evento)
            serializer = TicketsListSerializer(tickets, many=True)
            logger.info(f"GET /tickets/por-evento/{id_evento}/ — {tickets.count()} tickets")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GET /tickets/por-evento/{id_evento}/ — error: {e}", exc_info=True)
            return Response(
                {"error": "Error al obtener tickets del evento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
