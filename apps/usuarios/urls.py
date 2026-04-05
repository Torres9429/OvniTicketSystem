from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UsuariosViewSet, LoginView, RegistroUsuarioView, RegistroOrganizadorView

router = DefaultRouter()
router.register(r'usuarios', UsuariosViewSet, basename='usuarios')

urlpatterns = router.urls + [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/registro/usuario/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('auth/registro/cliente/', RegistroOrganizadorView.as_view(), name='registro_cliente'),
]
