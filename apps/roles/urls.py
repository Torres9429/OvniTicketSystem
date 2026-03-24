from rest_framework.routers import DefaultRouter
from .views import RolesViewSet

router = DefaultRouter()
router.register(r'roles', RolesViewSet, basename='roles')

urlpatterns = router.urls
