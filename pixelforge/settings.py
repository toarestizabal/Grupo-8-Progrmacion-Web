"""Configuración de Django para PixelForge Games."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(nombre, valor_predeterminado=False):
    """Convierte una variable de entorno habitual a un booleano."""
    valor = os.getenv(nombre, str(valor_predeterminado))
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("Falta DJANGO_SECRET_KEY en el archivo .env")

DEBUG = env_bool("DJANGO_DEBUG")
PRODUCTION = env_bool("DJANGO_PRODUCTION")
if PRODUCTION and DEBUG:
    raise RuntimeError("DJANGO_DEBUG debe ser False cuando DJANGO_PRODUCTION=True")
if PRODUCTION and (
    len(SECRET_KEY) < 50 or SECRET_KEY.lower().startswith("reemplazar")
):
    raise RuntimeError("DJANGO_SECRET_KEY debe ser larga y aleatoria en producción")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "tienda.apps.TiendaConfig",
    "rest_api.apps.RestApiConfig",
    "rest_framework",
    "rest_framework.authtoken",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pixelforge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tienda.context_processors.resumen_carrito",
            ],
        },
    },
]

WSGI_APPLICATION = "pixelforge.wsgi.application"
ASGI_APPLICATION = "pixelforge.asgi.application"

# La aplicación utiliza exclusivamente Oracle. No existe una alternativa SQLite.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.oracle",
        "NAME": os.getenv("ORACLE_DSN", "localhost:1521/orclpdb"),
        "USER": os.getenv("ORACLE_USER", "PIXELFORGE_APP"),
        "PASSWORD": os.getenv("ORACLE_PASSWORD", ""),
        "HOST": "",
        "PORT": "",
        "CONN_MAX_AGE": 60,
        "TEST": {
            # El esquema de pruebas se crea una sola vez con
            # database/create_test_user.sql. Nunca se prueba sobre PIXELFORGE_APP.
            "USER": os.getenv("ORACLE_TEST_USER", "PIXELFORGE_TEST"),
            "PASSWORD": os.getenv("ORACLE_TEST_PASSWORD")
            or os.getenv("ORACLE_PASSWORD", ""),
            "CREATE_DB": False,
            "CREATE_USER": False,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "tienda.validators.ComplexityValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "tienda.Usuario"
LOGIN_URL = "tienda:login"
LOGIN_REDIRECT_URL = "tienda:inicio"
LOGOUT_REDIRECT_URL = "tienda:inicio"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-responder@pixelforge.cl"

API_TOKEN_TTL_HOURS = int(os.getenv("API_TOKEN_TTL_HOURS", "24"))

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origen.strip()
]

# Estas medidas se activan al desplegar detrás de un proxy HTTPS (por ejemplo, Azure).
SECURE_SSL_REDIRECT = PRODUCTION
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
SECURE_HSTS_SECONDS = (
    int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "3600")) if PRODUCTION else 0
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = PRODUCTION
SECURE_HSTS_PRELOAD = PRODUCTION
SECURE_REFERRER_POLICY = "same-origin"
if PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_api.authentication.TokenAuthenticationConExpiracion",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/minute",
    },
}
