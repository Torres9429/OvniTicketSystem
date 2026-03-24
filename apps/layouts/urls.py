from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutsViewSet

# Creamos el router y registramos nuestro ViewSet
router = DefaultRouter()
router.register(r'layouts', LayoutsViewSet, basename='layouts')

urlpatterns = router.urls
