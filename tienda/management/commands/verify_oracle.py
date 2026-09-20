from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from tienda.models import (
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


class Command(BaseCommand):
    help = "Comprueba la conexión real con Oracle y muestra las tablas funcionales."

    def handle(self, *args, **options):
        if connection.vendor != "oracle":
            raise CommandError(f"Se esperaba Oracle, pero Django usa {connection.vendor!r}.")

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT SYS_CONTEXT('USERENV','CURRENT_SCHEMA'), "
                    "SYS_CONTEXT('USERENV','SERVICE_NAME') FROM DUAL"
                )
                esquema, servicio = cursor.fetchone()
        except Exception as error:
            raise CommandError(f"No fue posible conectar con Oracle: {error}") from error

        self.stdout.write(self.style.SUCCESS("Conexión Oracle comprobada correctamente."))
        self.stdout.write(f"Esquema activo : {esquema}")
        self.stdout.write(f"Servicio Oracle: {servicio}")
        self.stdout.write("Tablas funcionales:")
        modelos = (Rol, Usuario, Categoria, Producto, Inventario, Carrito, ItemCarrito, Pedido, DetallePedido)
        for modelo in modelos:
            self.stdout.write(f"  {modelo._meta.db_table:<24} {modelo.objects.count():>5} filas")

