from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutsViewSet, LayoutUltimaVersionView

router = DefaultRouter()
router.register(r'layouts', LayoutsViewSet, basename='layouts')

urlpatterns = [
    path('layouts/ultima-version/', LayoutUltimaVersionView.as_view(), name='layout-ultima-version'),
] + router.urls
