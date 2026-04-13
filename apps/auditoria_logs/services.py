from .models import AuditoriaLogs
from ipware import get_client_ip as ipware_get_client_ip
from typing import Any, Optional

def get_ip(request: Any):
    if request is None:
        return None
    ip, _ = ipware_get_client_ip(request)
    return ip

def registrar_auditoria(
    entidad: str,
    accion: str,
    id_usuario,
    valores_antes: Optional[dict[str, Any]] = None,
    valores_despues: Optional[dict[str, Any]] = None,
    ip: Any = None,
):
    AuditoriaLogs.objects.create(
        entidad=entidad,
        accion=accion,
        valores_antes=valores_antes,
        valores_despues=valores_despues,
        id_usuario=id_usuario,
        ip=get_ip(ip)
    )
