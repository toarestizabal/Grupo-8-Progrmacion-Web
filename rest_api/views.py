from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from tienda.models import Categoria

from .permissions import EsAdministradorOSoloLectura
from .serializers import CategoriaSerializer


class ObtenerTokenView(ObtainAuthToken):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response(
            {
                "token": token.key,
                "usuario": usuario.username,
                "rol": usuario.rol.codigo if usuario.rol_id else None,
            }
        )


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
