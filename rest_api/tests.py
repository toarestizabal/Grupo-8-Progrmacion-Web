from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tienda.models import Categoria, Rol, Usuario


class CategoriaApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        rol_cliente, _ = Rol.objects.get_or_create(codigo=Rol.CLIENTE, defaults={"nombre": "Cliente"})
        rol_admin, _ = Rol.objects.get_or_create(
            codigo=Rol.ADMINISTRADOR,
            defaults={"nombre": "Administrador"},
        )
        cls.cliente = Usuario.objects.create_user(
            username="api_cliente",
            email="api_cliente@pixelforge.cl",
            password="Cliente123!",
            nombre_completo="Cliente API",
            fecha_nacimiento=date(1995, 1, 1),
            rol=rol_cliente,
        )
        cls.admin = Usuario.objects.create_user(
            username="api_admin",
            email="api_admin@pixelforge.cl",
            password="Admin123!",
            nombre_completo="Administrador API",
            fecha_nacimiento=date(1990, 1, 1),
            rol=rol_admin,
        )
        cls.categoria = Categoria.objects.create(
            nombre="Categoría API",
            slug="categoria-api",
            descripcion="Categoría para pruebas",
        )

    def obtener_token(self, username, password):
        respuesta = self.client.post(
            reverse("rest_api:token"),
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return respuesta.data["token"]

    def test_api_rechaza_solicitudes_sin_token(self):
        respuesta = self.client.get(reverse("rest_api:categoria-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cliente_autenticado_puede_leer_y_filtrar(self):
        token = self.obtener_token("api_cliente", "Cliente123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        respuesta = self.client.get(reverse("rest_api:categoria-list"), {"buscar": "API"})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["count"], 1)

    def test_cliente_no_puede_modificar_categorias(self):
        token = self.obtener_token("api_cliente", "Cliente123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        respuesta = self.client.post(
            reverse("rest_api:categoria-list"),
            {"nombre": "Sin permiso", "slug": "sin-permiso", "activa": True},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_realiza_crud_de_categorias(self):
        token = self.obtener_token("api_admin", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        crear = self.client.post(
            reverse("rest_api:categoria-list"),
            {
                "nombre": "Simulación",
                "slug": "simulacion",
                "descripcion": "Juegos de simulación",
                "imagen": "simulacion.svg",
                "activa": True,
            },
            format="json",
        )
        self.assertEqual(crear.status_code, status.HTTP_201_CREATED)
        detalle = reverse("rest_api:categoria-detail", args=(crear.data["id"],))

        actualizar = self.client.put(
            detalle,
            {
                "nombre": "Simulación actualizada",
                "slug": "simulacion-actualizada",
                "descripcion": "Descripción actualizada",
                "imagen": "simulacion.svg",
                "activa": True,
            },
            format="json",
        )
        self.assertEqual(actualizar.status_code, status.HTTP_200_OK)

        eliminar = self.client.delete(detalle)
        self.assertEqual(eliminar.status_code, status.HTTP_204_NO_CONTENT)
