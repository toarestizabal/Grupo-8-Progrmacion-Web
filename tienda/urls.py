from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("categoria/<slug:slug>/", views.catalogo, name="catalogo_categoria"),
    path("cuenta/registro/", views.registro, name="registro"),
    path("cuenta/login/", views.iniciar_sesion, name="login"),
    path("cuenta/logout/", views.cerrar_sesion, name="logout"),
    path("cuenta/perfil/", views.perfil, name="perfil"),
    path(
        "cuenta/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("tienda:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "cuenta/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "cuenta/recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("tienda:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "cuenta/recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/agregar/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),
    path("carrito/actualizar/<int:item_id>/", views.actualizar_item_carrito, name="actualizar_item_carrito"),
    path("carrito/eliminar/<int:item_id>/", views.eliminar_item_carrito, name="eliminar_item_carrito"),
    path("pago/", views.pago, name="pago"),
    path("mis-compras/", views.mis_compras, name="mis_compras"),
    path("administracion/", views.admin_dashboard, name="admin_dashboard"),
    path("administracion/productos/", views.admin_productos, name="admin_productos"),
    path("administracion/productos/nuevo/", views.admin_producto_crear, name="admin_producto_crear"),
    path("administracion/productos/<int:producto_id>/editar/", views.admin_producto_editar, name="admin_producto_editar"),
    path("administracion/productos/<int:producto_id>/eliminar/", views.admin_producto_eliminar, name="admin_producto_eliminar"),
    path("administracion/inventario/", views.admin_inventario, name="admin_inventario"),
    path("administracion/usuarios/", views.admin_usuarios, name="admin_usuarios"),
    path("administracion/usuarios/nuevo/", views.admin_usuario_crear, name="admin_usuario_crear"),
    path("administracion/usuarios/<int:usuario_id>/editar/", views.admin_usuario_editar, name="admin_usuario_editar"),
    path("administracion/usuarios/<int:usuario_id>/eliminar/", views.admin_usuario_eliminar, name="admin_usuario_eliminar"),
    path("administracion/pedidos/", views.admin_pedidos, name="admin_pedidos"),
    path("administracion/pedidos/<int:pedido_id>/estado/", views.admin_pedido_estado, name="admin_pedido_estado"),
]

