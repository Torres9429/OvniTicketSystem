import logging
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from apps.common.permissions import IsAdmin
from .models import AuditoriaLogs
from .serializers import AuditoriaLogsSerializer

logger = logging.getLogger(__name__)

class AuditoriaLogsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditoriaLogs.objects.all()
    serializer_class = AuditoriaLogsSerializer

    def get_permissions(self):
        return [IsAdmin()]
    
    def get_queryset(self):
        queryset = AuditoriaLogs.objects.all()
        entidad = self.request.query_params.get('entidad')
        id_usuario = self.request.query_params.get('id_usuario')
        accion = self.request.query_params.get('accion')
        if entidad:
            queryset = queryset.filter(entidad=entidad)
        if id_usuario:
            queryset = queryset.filter(id_usuario=id_usuario)
        if accion:
            queryset = queryset.filter(accion=accion)
        return queryset
    
    def list(self, request, *args, **kwargs):
        logger.debug("GET/auditoria/ - listando logs")
        response = super().list(request, *args, **kwargs)
        logger.debug(f"GET/auditoria/ - logs listados: {len(response.data)}")
        return response
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.debug(f"GET/auditoria/{pk}/ - obteniendo log")
        try:
            response = super().retrieve(request, pk=pk, *args, **kwargs)
            logger.info(f"GET/auditoria/{pk}/ - log obtenido")
            return response
        except Exception as e:
            logger.warning(f"GET/auditoria/{pk}/ - log no encontrado: {str(e)}")
            return Response({"error": "Log no encontrado"}, status=status.HTTP_404_NOT_FOUND)