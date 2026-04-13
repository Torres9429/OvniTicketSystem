from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UsuariosViewSet, LoginView, RegistroUsuarioView, RegistroOrganizadorView, CustomTokenRefreshView

router = DefaultRouter()
router.register(r'usuarios', UsuariosViewSet, basename='usuarios')

urlpatterns = router.urls + [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/registro/usuario/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('auth/registro/cliente/', RegistroOrganizadorView.as_view(), name='registro_cliente'),
]
