from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LugaresViewSet

router = DefaultRouter()
router.register(r'lugares', LugaresViewSet, basename='lugares')

urlpatterns = router.urls
