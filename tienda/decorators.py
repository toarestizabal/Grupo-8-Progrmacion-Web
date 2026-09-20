from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def cliente_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.es_cliente:
            messages.warning(request, "Esta sección corresponde a cuentas de cliente.")
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def administrador_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.es_administrador:
            messages.error(request, "No tienes permisos para acceder a administración.")
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper

