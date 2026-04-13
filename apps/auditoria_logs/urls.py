from django.urls import path
from .views import AuditoriaLogsViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'auditoria', AuditoriaLogsViewSet, basename='auditoria')

urlpatterns = router.urls