from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Inventario, Producto, Rol


@receiver(post_migrate)
def crear_roles_iniciales(sender, **kwargs):
    if sender.name != "tienda":
        return
    Rol.objects.update_or_create(
        codigo=Rol.CLIENTE,
        defaults={"nombre": "Cliente", "descripcion": "Compra productos y consulta sus pedidos."},
    )
    Rol.objects.update_or_create(
        codigo=Rol.ADMINISTRADOR,
        defaults={"nombre": "Administrador", "descripcion": "Gestiona la tienda y sus usuarios."},
    )


@receiver(post_save, sender=Producto)
def crear_inventario_producto(sender, instance, created, **kwargs):
    if created:
        Inventario.objects.get_or_create(producto=instance)

