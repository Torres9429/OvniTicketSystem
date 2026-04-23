import logging

import stripe
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .stripe_service import (
    crear_sesion_checkout,
    completar_compra_stripe,
    obtener_orden_por_sesion,
)

logger = logging.getLogger(__name__)


class CrearSesionPagoView(APIView):
    """
    POST /api/pagos/crear-sesion/

    Creates a Stripe Checkout Session for the authenticated user.

    Body
    ----
    {
        "id_evento": <int>,
        "ids_grid_cell": [<int>, ...],            // opcional
        "asientos_layout": [{row,col,zone_id}],   // opcional
        "operation_id": "<uuid>"   // optional idempotency key
    }

    Success → 200
    {
        "session_url": "<stripe-checkout-url>",
        "session_id": "<cs_...>"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        id_evento = request.data.get("id_evento")
        ids_grid_cell = request.data.get("ids_grid_cell")
        asientos_layout = request.data.get("asientos_layout")
        operation_id = request.data.get("operation_id")

        if not id_evento:
            return Response(
                {"error": "Se requiere 'id_evento'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ids_grid_cell is None and asientos_layout is None:
            return Response(
                {
                    "error": (
                        "Debes enviar 'ids_grid_cell' o 'asientos_layout' "
                        "con al menos un asiento."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ids_grid_cell is not None and (
            not isinstance(ids_grid_cell, list) or len(ids_grid_cell) == 0
        ):
            return Response(
                {"error": "'ids_grid_cell' debe ser una lista no vacía."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if asientos_layout is not None and (
            not isinstance(asientos_layout, list) or len(asientos_layout) == 0
        ):
            return Response(
                {"error": "'asientos_layout' debe ser una lista no vacía."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if operation_id is not None and (
            not isinstance(operation_id, str) or len(operation_id) > 64
        ):
            return Response(
                {"error": "'operation_id' debe ser una cadena de hasta 64 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = crear_sesion_checkout(
                id_evento=id_evento,
                ids_grid_cell=ids_grid_cell,
                asientos_layout=asientos_layout,
                usuario=request.user,
                operation_id=operation_id,
            )
            return Response(
                {
                    "session_url": session.url,
                    "checkout_url": session.url,
                    "session_id": session.id,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(
                "POST /api/pagos/crear-sesion/ — error: %s", exc, exc_info=True
            )
            return Response(
                {"error": "No se pudo crear la sesión de pago."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    POST /api/pagos/webhook/

    Stripe sends signed events here. No authentication — signature validated
    with STRIPE_WEBHOOK_SECRET instead.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            logger.warning("Stripe webhook: invalid payload")
            return Response(
                {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook: invalid signature")
            return Response(
                {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        event_type = event.get("type")
        logger.info("Stripe webhook received: type=%s", event_type)

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            try:
                completar_compra_stripe(session)
            except Exception as exc:
                logger.error(
                    "Stripe webhook: error processing checkout.session.completed "
                    "session=%s — %s",
                    session.get("id"),
                    exc,
                    exc_info=True,
                )
                return Response(
                    {"error": "Error interno al procesar el pago."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class OrdenPorSesionView(APIView):
    """
    GET /api/pagos/orden-por-sesion/?session_id=<cs_...>

    Polls for the order created by the webhook after a successful Stripe payment.
    Returns 202 while the webhook hasn't fired yet so the frontend can retry.

    Success → 200  { "id_orden": <int> }
    Pending → 202  { "status": "pending" }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get("session_id", "").strip()
        if not session_id:
            return Response(
                {"error": "Se requiere el parámetro 'session_id'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            orden = obtener_orden_por_sesion(session_id)

            # Fallback resiliente para entornos donde el webhook no llega.
            # Si la sesión ya está pagada en Stripe, finalizamos la compra aquí.
            if orden is None:
                stripe_session = stripe.checkout.Session.retrieve(
                    session_id,
                    api_key=settings.STRIPE_SECRET_KEY,
                )

                metadata = getattr(stripe_session, "metadata", {}) or {}
                metadata_user_id = metadata.get("id_usuario")

                # Seguridad: el usuario autenticado solo puede resolver su propia sesión.
                if metadata_user_id and str(metadata_user_id) != str(request.user.pk):
                    return Response(
                        {"error": "La sesión de pago no pertenece al usuario autenticado."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if getattr(stripe_session, "payment_status", "") == "paid":
                    orden = completar_compra_stripe(stripe_session)
        except Exception as exc:
            logger.error(
                "GET /api/pagos/orden-por-sesion/ — error: %s", exc, exc_info=True
            )
            return Response(
                {"error": "Error al buscar la orden."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if orden is None:
            return Response({"status": "pending"}, status=status.HTTP_202_ACCEPTED)

        return Response({"id_orden": orden.pk}, status=status.HTTP_200_OK)
