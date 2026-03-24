from rest_framework.routers import DefaultRouter
from .views import UsuariosViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuariosViewSet, basename='usuarios')

urlpatterns = router.urls
