from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Permite acceso solo a usuarios con rol 'admin'."""

    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'id_rol'):
            return False
        return request.user.id_rol.nombre.lower() == "admin"


class IsOrganizador(BasePermission):
    """Permite acceso a usuarios con rol de gestión de venues/eventos.
    Acepta: admin, organizador, cliente (todos pueden gestionar lugares y eventos)."""

    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'id_rol'):
            return False
        rol = request.user.id_rol.nombre.lower()
        return rol in ("admin", "organizador", "cliente")


class ReadOnly(BasePermission):
    """Permite solo operaciones de lectura (GET, HEAD, OPTIONS)."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """Permite acceso al dueño del recurso o a admin.
    Requiere que el objeto tenga un campo id_dueno (FK a Usuarios)."""

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'id_rol') and request.user.id_rol.nombre == "admin":
            return True
        owner_id = getattr(obj, 'id_dueno_id', None) or getattr(obj, 'id_dueno', None)
        if owner_id is None:
            return False
        user_id = getattr(request.user, 'id_usuario', None) or getattr(request.user, 'pk', None)
        return str(owner_id) == str(user_id)
