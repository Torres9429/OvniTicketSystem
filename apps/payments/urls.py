from django.urls import path

from .views import CrearSesionPagoView, OrdenPorSesionView, StripeWebhookView

urlpatterns = [
    path("pagos/crear-sesion/", CrearSesionPagoView.as_view(), name="pagos-crear-sesion"),
    path("pagos/webhook/", StripeWebhookView.as_view(), name="pagos-webhook"),
    path("pagos/orden-por-sesion/", OrdenPorSesionView.as_view(), name="pagos-orden-por-sesion"),
]
