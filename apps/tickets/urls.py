from rest_framework.routers import DefaultRouter
from .views import TicketsViewSet

router = DefaultRouter()
router.register(r'tickets', TicketsViewSet, basename='tickets')

urlpatterns = router.urls
