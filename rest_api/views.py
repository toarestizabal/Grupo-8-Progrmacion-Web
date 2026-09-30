from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from tienda.models import Categoria, Producto

from .permissions import EsAdministradorOSoloLectura
from .serializers import CategoriaSerializer, ProductoSerializer


class ObtenerTokenView(ObtainAuthToken):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["user"]
        Token.objects.filter(user=usuario).delete()
        token = Token.objects.create(user=usuario)
        return Response(
            {
                "token": token.key,
                "usuario": usuario.username,
                "rol": usuario.rol.codigo if usuario.rol_id else None,
                "expira_en": (
                    token.created + timedelta(hours=settings.API_TOKEN_TTL_HOURS)
                ).isoformat(),
            }
        )


class RevocarTokenView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if isinstance(request.auth, Token):
            request.auth.delete()
        return Response({"detalle": "Token revocado correctamente."})


class CategoriaViewSet(viewsets.ModelViewSet):
    """CRUD de categorías con filtros por estado y texto."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = (IsAuthenticated, EsAdministradorOSoloLectura)
    http_method_names = ("get", "post", "put", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        activa = self.request.query_params.get("activa", "").strip().lower()
        buscar = self.request.query_params.get("buscar", "").strip()

        if activa in {"true", "1", "si", "sí"}:
            queryset = queryset.filter(activa=True)
        elif activa in {"false", "0", "no"}:
            queryset = queryset.filter(activa=False)
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | Q(descripcion__icontains=buscar)
            )
        return queryset.order_by("nombre")

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detalle": "No se puede eliminar una categoría que tiene productos asociados."},
                status=status.HTTP_409_CONFLICT,
            )


class ProductoViewSet(viewsets.ModelViewSet):
    """CRUD de productos con búsqueda y filtros de catálogo e inventario."""

    queryset = Producto.objects.select_related("categoria", "inventario")
    serializer_class = ProductoSerializer
    permission_classes = (IsAuthenticated, EsAdministradorOSoloLectura)
    http_method_names = ("get", "post", "put", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo", "").strip().lower()
        categoria = self.request.query_params.get("categoria", "").strip()
        en_stock = self.request.query_params.get("en_stock", "").strip().lower()
        buscar = self.request.query_params.get("buscar", "").strip()

        if activo in {"true", "1", "si", "sí"}:
            queryset = queryset.filter(activo=True)
        elif activo in {"false", "0", "no"}:
            queryset = queryset.filter(activo=False)
        if categoria:
            queryset = queryset.filter(categoria__slug=categoria)
        if en_stock in {"true", "1", "si", "sí"}:
            queryset = queryset.filter(inventario__stock__gt=0)
        elif en_stock in {"false", "0", "no"}:
            queryset = queryset.filter(inventario__stock=0)
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | Q(descripcion__icontains=buscar)
            )
        return queryset.order_by("nombre")
