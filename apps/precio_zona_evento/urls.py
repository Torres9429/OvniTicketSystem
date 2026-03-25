from django.urls import path, include  
from rest_framework.routers import DefaultRouter
from .views import PrecioZonaEventoViewSet

router = DefaultRouter()
router.register(r'precio-zona-evento', PrecioZonaEventoViewSet, basename='precio-zona-evento')

urlpatterns = router.urls