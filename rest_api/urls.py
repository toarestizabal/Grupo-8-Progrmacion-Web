from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, ObtenerTokenView, ProductoViewSet, RevocarTokenView

app_name = "rest_api"

router = DefaultRouter()
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("productos", ProductoViewSet, basename="producto")

urlpatterns = [
    path("token/", ObtenerTokenView.as_view(), name="token"),
    path("token/revocar/", RevocarTokenView.as_view(), name="revocar_token"),
    path("", include(router.urls)),
]
