from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    AsientosViewSet,
    DisponibilidadAsientosView,
    RetenerAsientosView,
    LiberarAsientosView,
    ConfirmarCompraView,
    HoldStatusView,
)

router = DefaultRouter()
router.register(r'asientos', AsientosViewSet, basename='asientos')

# Manual paths BEFORE router urls so they don't get captured by asientos/<pk>/
urlpatterns = [
    path('asientos/disponibilidad/<int:id_evento>/', DisponibilidadAsientosView.as_view(), name='asientos-disponibilidad'),
    path('asientos/retener/', RetenerAsientosView.as_view(), name='asientos-retener'),
    path('asientos/liberar/', LiberarAsientosView.as_view(), name='asientos-liberar'),
    path('asientos/confirmar/', ConfirmarCompraView.as_view(), name='asientos-confirmar'),
    path('asientos/hold-status/<int:id_evento>/', HoldStatusView.as_view(), name='asientos-hold-status'),
] + router.urls