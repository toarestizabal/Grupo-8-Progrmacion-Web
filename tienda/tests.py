from datetime import date
from decimal import Decimal
import re

from django.core import mail
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import (
    Carrito,
    Categoria,
    DetallePedido,
    Inventario,
    ItemCarrito,
    Pedido,
    Producto,
    Rol,
    Usuario,
)


class PixelForgeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rol_cliente, _ = Rol.objects.get_or_create(codigo=Rol.CLIENTE, defaults={"nombre": "Cliente"})
        cls.rol_admin, _ = Rol.objects.get_or_create(
            codigo=Rol.ADMINISTRADOR, defaults={"nombre": "Administrador"}
        )
        cls.cliente = Usuario.objects.create_user(
            username="cliente_test",
            email="cliente_test@pixelforge.cl",
            password="Cliente123!",
            nombre_completo="Cliente Pruebas",
            fecha_nacimiento=date(1995, 5, 10),
            rol=cls.rol_cliente,
        )
        cls.admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin_test@pixelforge.cl",
            password="Admin123!",
            nombre_completo="Administrador Pruebas",
            fecha_nacimiento=date(1990, 1, 1),
            rol=cls.rol_admin,
        )
        cls.categoria = Categoria.objects.create(nombre="Acción", slug="accion", activa=True)
        cls.producto = Producto.objects.create(
            categoria=cls.categoria,
            nombre="Juego de prueba",
            descripcion="Producto utilizado por la suite de pruebas.",
            precio=Decimal("25000"),
            imagen="accion.svg",
            activo=True,
        )
        cls.producto.inventario.stock = 5
        cls.producto.inventario.save()

    def test_catalogo_lee_productos_desde_modelos(self):
        respuesta = self.client.get(reverse("tienda:catalogo"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Juego de prueba")

    def test_registro_crea_cliente_y_cifra_contrasena(self):
        respuesta = self.client.post(
            reverse("tienda:registro"),
            {
                "nombre_completo": "Nueva Cliente",
                "username": "nueva_cliente",
                "email": "nueva@pixelforge.cl",
                "password1": "Segura123!",
                "password2": "Segura123!",
                "fecha_nacimiento": "1998-08-20",
                "direccion": "Santiago",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:login"))
        usuario = Usuario.objects.get(username="nueva_cliente")
        self.assertEqual(usuario.rol.codigo, Rol.CLIENTE)
        self.assertTrue(usuario.check_password("Segura123!"))
        self.assertNotEqual(usuario.password, "Segura123!")

    def test_login_acepta_correo(self):
        respuesta = self.client.post(
            reverse("tienda:login"),
            {"identificador": self.cliente.email, "password": "Cliente123!"},
        )
        self.assertRedirects(respuesta, reverse("tienda:inicio"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.cliente.pk)

    def test_recuperacion_completa_cambia_clave_y_permite_login(self):
        respuesta = self.client.post(
            reverse("tienda:password_reset"),
            {"email": self.cliente.email},
        )
        self.assertRedirects(respuesta, reverse("tienda:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/cuenta/recuperar/", mail.outbox[0].body)

        coincidencia = re.search(
            r"https?://[^/]+(?P<ruta>/cuenta/recuperar/\S+)",
            mail.outbox[0].body,
        )
        self.assertIsNotNone(coincidencia)
        abrir_enlace = self.client.get(coincidencia.group("ruta"))
        self.assertEqual(abrir_enlace.status_code, 302)

        nueva_clave = "NuevaClave456!"
        cambiar = self.client.post(
            abrir_enlace.url,
            {"new_password1": nueva_clave, "new_password2": nueva_clave},
        )
        self.assertRedirects(cambiar, reverse("tienda:password_reset_complete"))

        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.check_password(nueva_clave))
        iniciar = self.client.post(
            reverse("tienda:login"),
            {"identificador": self.cliente.email, "password": nueva_clave},
        )
        self.assertRedirects(iniciar, reverse("tienda:inicio"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.cliente.pk)

    def test_rutas_internas_exigen_autenticacion(self):
        for nombre in ("tienda:perfil", "tienda:carrito", "tienda:mis_compras", "tienda:admin_dashboard"):
            with self.subTest(url=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(reverse("tienda:login"), respuesta.url)

    def test_roles_impiden_acceso_cruzado(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("tienda:admin_dashboard")).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("tienda:carrito")).status_code, 403)

    def test_cliente_modifica_su_perfil(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse("tienda:perfil"),
            {
                "nombre_completo": "Nombre Actualizado",
                "username": self.cliente.username,
                "email": self.cliente.email,
                "fecha_nacimiento": "1995-05-10",
                "direccion": "Nueva dirección",
                "clave_nueva1": "",
                "clave_nueva2": "",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:perfil"))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre_completo, "Nombre Actualizado")

    def test_perfil_rechaza_fecha_futura(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse("tienda:perfil"),
            {
                "nombre_completo": self.cliente.nombre_completo,
                "username": self.cliente.username,
                "email": self.cliente.email,
                "fecha_nacimiento": "2999-01-01",
                "direccion": self.cliente.direccion,
                "clave_nueva1": "",
                "clave_nueva2": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "La fecha de nacimiento no puede estar en el futuro.")
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.fecha_nacimiento, date(1995, 5, 10))

    def test_perfil_rechaza_usuario_menor_de_13(self):
        self.client.force_login(self.cliente)
        hoy = date.today()
        respuesta = self.client.post(
            reverse("tienda:perfil"),
            {
                "nombre_completo": self.cliente.nombre_completo,
                "username": self.cliente.username,
                "email": self.cliente.email,
                "fecha_nacimiento": f"{hoy.year - 10:04d}-{hoy.month:02d}-{hoy.day:02d}",
                "direccion": self.cliente.direccion,
                "clave_nueva1": "",
                "clave_nueva2": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debes tener al menos 13 años.")
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.fecha_nacimiento, date(1995, 5, 10))

    def test_administrador_realiza_crud_de_productos(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("tienda:admin_producto_crear"),
            {
                "nombre": "Producto CRUD",
                "categoria": self.categoria.pk,
                "descripcion": "Creado desde la interfaz.",
                "precio": "39990",
                "imagen": "accion.svg",
                "activo": "on",
                "stock": "7",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:admin_productos"))
        producto = Producto.objects.get(nombre="Producto CRUD")
        self.assertEqual(producto.inventario.stock, 7)

        respuesta = self.client.post(
            reverse("tienda:admin_producto_editar", args=(producto.pk,)),
            {
                "nombre": "Producto CRUD actualizado",
                "categoria": self.categoria.pk,
                "descripcion": "Actualizado.",
                "precio": "40000",
                "imagen": "accion.svg",
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:admin_productos"))
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Producto CRUD actualizado")

        self.client.post(reverse("tienda:admin_producto_eliminar", args=(producto.pk,)))
        self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())

    def test_administrador_modifica_inventario(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("tienda:admin_inventario"),
            {"inventario_id": self.producto.inventario.pk, "stock": 18},
        )
        self.assertRedirects(respuesta, reverse("tienda:admin_inventario"))
        self.producto.inventario.refresh_from_db()
        self.assertEqual(self.producto.inventario.stock, 18)

    def test_carrito_y_pago_generan_pedido_y_reducen_stock(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("tienda:agregar_carrito", args=(self.producto.pk,)))
        carrito = Carrito.objects.get(usuario=self.cliente)
        item = ItemCarrito.objects.get(carrito=carrito, producto=self.producto)
        item.cantidad = 2
        item.save()

        respuesta = self.client.post(
            reverse("tienda:pago"),
            {
                "direccion_despacho": "Av. Pruebas 123",
                "titular": "Cliente Pruebas",
                "numero_tarjeta": "4111111111111111",
                "vencimiento": "12/99",
                "cvv": "123",
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:mis_compras"))
        pedido = Pedido.objects.get(usuario=self.cliente)
        self.assertEqual(pedido.total, Decimal("50000"))
        self.assertEqual(DetallePedido.objects.get(pedido=pedido).cantidad, 2)
        self.producto.inventario.refresh_from_db()
        self.assertEqual(self.producto.inventario.stock, 3)
        self.assertFalse(carrito.items.exists())

    def test_administrador_crea_y_elimina_usuario(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("tienda:admin_usuario_crear"),
            {
                "nombre_completo": "Usuario Administrado",
                "username": "administrado",
                "email": "administrado@pixelforge.cl",
                "password1": "Segura123!",
                "password2": "Segura123!",
                "fecha_nacimiento": "1994-04-12",
                "direccion": "Santiago",
                "rol": self.rol_cliente.pk,
            },
        )
        self.assertRedirects(respuesta, reverse("tienda:admin_usuarios"))
        usuario = Usuario.objects.get(username="administrado")
        self.client.post(reverse("tienda:admin_usuario_eliminar", args=(usuario.pk,)))
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())


class ConsumoServicioExternoTests(SimpleTestCase):
    @patch("tienda.views.obtener_juegos_externos")
    def test_endpoint_publico_entrega_juegos_en_json(self, obtener_juegos):
        obtener_juegos.return_value = [
            {
                "id": 1,
                "titulo": "Juego externo",
                "descripcion": "Obtenido desde un servicio público.",
                "genero": "Acción",
                "plataforma": "PC",
                "editor": "Estudio",
                "imagen": "https://example.com/juego.jpg",
                "enlace": "https://www.freetogame.com/juego-externo",
            }
        ]
        respuesta = self.client.get(reverse("tienda:juegos_externos"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["resultados"][0]["titulo"], "Juego externo")

    def test_pagina_explorador_incluye_endpoint_para_fetch(self):
        respuesta = self.client.get(reverse("tienda:explorar_juegos"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, reverse("tienda:juegos_externos"))
