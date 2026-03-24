from rest_framework.routers import DefaultRouter
from .views import OrdenesViewSet

router = DefaultRouter()
router.register(r'ordenes', OrdenesViewSet, basename='ordenes')

urlpatterns = router.urls
