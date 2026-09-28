from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, ObtenerTokenView

app_name = "rest_api"

router = DefaultRouter()
router.register("categorias", CategoriaViewSet, basename="categoria")

urlpatterns = [
    path("token/", ObtenerTokenView.as_view(), name="token"),
    path("", include(router.urls)),
]
