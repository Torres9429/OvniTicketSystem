from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutsViewSet, LayoutUltimaVersionView

# Creamos el router y registramos nuestro ViewSet
router = DefaultRouter()
router.register(r'layouts', LayoutsViewSet, basename='layouts')

# Manual path BEFORE router urls so it doesn't get captured by layouts/<pk>/
urlpatterns = [
    path('layouts/ultima-version/', LayoutUltimaVersionView.as_view(), name='layout-ultima-version'),
] + router.urls
