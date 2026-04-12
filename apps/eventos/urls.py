from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventosViewSet

# Creamos el router y registramos nuestro ViewSet
router = DefaultRouter()
router.register(r'eventos', EventosViewSet, basename='eventos')

#urlpatterns = router.urls
urlpatterns = [
    path('eventos/by-cliente', EventosViewSet.as_view({'get': 'por_cliente'}), name='eventos-by-cliente'),
] + router.urls