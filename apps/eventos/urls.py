from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventosViewSet

# Creamos el router y registramos nuestro ViewSet
router = DefaultRouter()
router.register(r'eventos', EventosViewSet, basename='eventos')

urlpatterns = router.urls