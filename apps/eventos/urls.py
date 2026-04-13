from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventosViewSet

router = DefaultRouter()
router.register(r'eventos', EventosViewSet, basename='eventos')

urlpatterns = [
    path('eventos/by-cliente', EventosViewSet.as_view({'get': 'por_cliente'}), name='eventos-by-cliente'),
] + router.urls