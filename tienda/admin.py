from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "descripcion")
    search_fields = ("codigo", "nombre")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "nombre_completo", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("username", "email", "nombre_completo")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Datos PixelForge",
            {"fields": ("nombre_completo", "fecha_nacimiento", "direccion", "rol")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Datos PixelForge",
            {"fields": ("email", "nombre_completo", "fecha_nacimiento", "direccion", "rol")},
        ),
    )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa")
    list_editable = ("activa",)
    prepopulated_fields = {"slug": ("nombre",)}


class InventarioInline(admin.StackedInline):
    model = Inventario
    extra = 0
    max_num = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "stock", "activo")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "descripcion")
    inlines = (InventarioInline,)

    @admin.display(description="Stock")
    def stock(self, obj):
        return obj.inventario.stock


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ("producto", "nombre_producto", "precio_unitario", "cantidad")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha", "estado", "total")
    list_filter = ("estado", "fecha")
    search_fields = ("usuario__username", "usuario__email")
    inlines = (DetallePedidoInline,)


admin.site.register(Carrito)
admin.site.register(ItemCarrito)

