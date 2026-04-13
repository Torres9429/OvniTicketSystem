from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZonasViewSet

router = DefaultRouter()
router.register(r'zonas', ZonasViewSet, basename='zonas')

urlpatterns = router.urls