from rest_framework.routers import DefaultRouter
from .views import AsientosViewSet

router = DefaultRouter()
router.register(r'asientos', AsientosViewSet, basename='asientos')

urlpatterns = router.urls