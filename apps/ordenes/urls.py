from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ComprarView, OrdenesViewSet

router = DefaultRouter()
router.register(r'ordenes', OrdenesViewSet, basename='ordenes')

urlpatterns = [
    path('ordenes/comprar/', ComprarView.as_view(), name='ordenes-comprar'),
] + router.urls
