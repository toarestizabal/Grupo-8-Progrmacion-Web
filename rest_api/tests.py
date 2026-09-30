from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from tienda.models import Categoria, Producto, Rol, Usuario


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
        cls.producto = Producto.objects.create(
            categoria=cls.categoria,
            nombre="Videojuego API",
            descripcion="Producto para probar la segunda API.",
            precio=Decimal("29990"),
            imagen="accion.svg",
        )
        cls.producto.inventario.stock = 4
        cls.producto.inventario.save()

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

    def test_token_informa_vencimiento(self):
        respuesta = self.client.post(
            reverse("rest_api:token"),
            {"username": "api_cliente", "password": "Cliente123!"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("expira_en", respuesta.data)

    def test_token_vencido_se_rechaza_y_puede_renovarse(self):
        token_anterior = self.obtener_token("api_cliente", "Cliente123!")
        Token.objects.filter(key=token_anterior).update(
            created=timezone.now() - timedelta(hours=25)
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_anterior}")
        respuesta = self.client.get(reverse("rest_api:producto-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Token.objects.filter(key=token_anterior).exists())

        self.client.credentials()
        token_nuevo = self.obtener_token("api_cliente", "Cliente123!")
        self.assertNotEqual(token_nuevo, token_anterior)

    def test_usuario_puede_revocar_su_token(self):
        token = self.obtener_token("api_cliente", "Cliente123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        respuesta = self.client.post(reverse("rest_api:revocar_token"), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        for ruta in ("rest_api:categoria-list", "rest_api:producto-list"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(ruta))
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

    def test_api_productos_rechaza_solicitudes_sin_token(self):
        respuesta = self.client.get(reverse("rest_api:producto-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cliente_autenticado_consulta_productos_y_stock(self):
        token = self.obtener_token("api_cliente", "Cliente123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        respuesta = self.client.get(
            reverse("rest_api:producto-list"),
            {"buscar": "Videojuego", "categoria": "categoria-api", "en_stock": "true"},
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["count"], 1)
        self.assertEqual(respuesta.data["results"][0]["stock"], 4)

    def test_cliente_no_puede_modificar_productos(self):
        token = self.obtener_token("api_cliente", "Cliente123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        respuesta = self.client.patch(
            reverse("rest_api:producto-detail", args=(self.producto.pk,)),
            {"precio": "39990"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_realiza_crud_de_productos(self):
        token = self.obtener_token("api_admin", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        crear = self.client.post(
            reverse("rest_api:producto-list"),
            {
                "categoria": self.categoria.pk,
                "nombre": "Nuevo videojuego API",
                "descripcion": "Creado desde la API REST.",
                "precio": "45990",
                "imagen": "aventura.svg",
                "activo": True,
            },
            format="json",
        )
        self.assertEqual(crear.status_code, status.HTTP_201_CREATED)
        detalle = reverse("rest_api:producto-detail", args=(crear.data["id"],))

        actualizar = self.client.patch(detalle, {"precio": "49990"}, format="json")
        self.assertEqual(actualizar.status_code, status.HTTP_200_OK)
        self.assertEqual(actualizar.data["precio"], "49990.00")

        eliminar = self.client.delete(detalle)
        self.assertEqual(eliminar.status_code, status.HTTP_204_NO_CONTENT)
