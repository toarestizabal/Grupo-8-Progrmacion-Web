from rest_framework.permissions import SAFE_METHODS, BasePermission


class EsAdministradorOSoloLectura(BasePermission):
    """Permite lectura a usuarios autenticados y escritura solo a administradores."""

    message = "Solo una cuenta administradora puede modificar este recurso."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.es_administrador
