"""Reglas de negocio para convertir un carrito en un pedido."""

from decimal import Decimal

from django.db import transaction

from .models import Carrito, DetallePedido, Inventario, ItemCarrito, Pedido, Producto


class CompraError(Exception):
    """Error de negocio controlado durante la creación de un pedido."""


@transaction.atomic
def crear_pedido_desde_carrito(usuario, direccion_despacho, numero_tarjeta):
    """Crea un pedido y descuenta stock de forma atómica y protegida por bloqueos."""
    try:
        # get() evita LIMIT/OFFSET, que Oracle no admite junto a FOR UPDATE.
        carrito = Carrito.objects.select_for_update().get(usuario=usuario)
    except Carrito.DoesNotExist:
        raise CompraError("Tu carrito está vacío.")

    items = list(
        ItemCarrito.objects.select_for_update()
        .filter(carrito=carrito)
        .order_by("pk")
    )
    if not items:
        raise CompraError("Tu carrito está vacío.")

    productos = {
        producto.pk: producto
        for producto in Producto.objects.filter(
            pk__in=[item.producto_id for item in items]
        )
    }
    inventarios = {
        inventario.producto_id: inventario
        for inventario in Inventario.objects.select_for_update().filter(
            producto_id__in=productos
        )
    }

    for item in items:
        producto = productos.get(item.producto_id)
        inventario = inventarios.get(item.producto_id)
        if (
            producto is None
            or inventario is None
            or not producto.activo
            or item.cantidad > inventario.stock
        ):
            nombre = producto.nombre if producto else "el producto solicitado"
            raise CompraError(f"Stock insuficiente para {nombre}.")

    total = sum(
        (productos[item.producto_id].precio * item.cantidad for item in items),
        Decimal("0"),
    )
    pedido = Pedido.objects.create(
        usuario=usuario,
        total=total,
        direccion_despacho=direccion_despacho,
        ultimos_digitos=numero_tarjeta[-4:],
    )
    DetallePedido.objects.bulk_create(
        [
            DetallePedido(
                pedido=pedido,
                producto=productos[item.producto_id],
                nombre_producto=productos[item.producto_id].nombre,
                precio_unitario=productos[item.producto_id].precio,
                cantidad=item.cantidad,
            )
            for item in items
        ]
    )

    for item in items:
        inventario = inventarios[item.producto_id]
        inventario.stock -= item.cantidad
        inventario.save(update_fields=("stock", "actualizado"))

    ItemCarrito.objects.filter(pk__in=[item.pk for item in items]).delete()
    return pedido
