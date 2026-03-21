from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GridCellsViewSet

router = DefaultRouter()
router.register(r'grid-cells', GridCellsViewSet, basename='grid-cells')

urlpatterns = router.urls
