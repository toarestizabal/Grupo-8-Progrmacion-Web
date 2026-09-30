from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


def token_esta_vencido(token):
    duracion = timedelta(hours=settings.API_TOKEN_TTL_HOURS)
    return token.created <= timezone.now() - duracion


class TokenAuthenticationConExpiracion(TokenAuthentication):
    """Autenticación por token con vencimiento configurable."""

    def authenticate_credentials(self, key):
        usuario, token = super().authenticate_credentials(key)
        if token_esta_vencido(token):
            token.delete()
            raise AuthenticationFailed(
                "El token venció. Solicita uno nuevo en /api/token/."
            )
        return usuario, token
