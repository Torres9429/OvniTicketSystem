from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Permite acceso solo a usuarios con rol 'admin'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.id_rol.nombre == "admin")


class IsOrganizador(BasePermission):
    """Permite acceso a usuarios con rol 'admin' u 'organizador'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.id_rol.nombre in ("admin", "organizador"))
