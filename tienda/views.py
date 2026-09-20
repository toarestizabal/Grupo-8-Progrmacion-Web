from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import administrador_requerido, cliente_requerido
from .forms import (
    EstadoPedidoForm,
    InventarioForm,
    LoginForm,
    PagoSimuladoForm,
    PerfilForm,
    ProductoForm,
    RegistroForm,
    UsuarioAdminCreacionForm,
    UsuarioAdminForm,
)
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


def inicio(request):
    categorias = Categoria.objects.filter(activa=True).order_by("nombre")
    destacados = (
        Producto.objects.filter(activo=True, inventario__stock__gt=0)
        .select_related("categoria", "inventario")
        .order_by("-creado")[:6]
    )
    return render(request, "tienda/inicio.html", {"categorias": categorias, "destacados": destacados})


def catalogo(request, slug=None):
    categoria = None
    productos = Producto.objects.filter(activo=True).select_related("categoria", "inventario")
    if slug:
        categoria = get_object_or_404(Categoria, slug=slug, activa=True)
        productos = productos.filter(categoria=categoria)
    consulta = request.GET.get("q", "").strip()
    if consulta:
        productos = productos.filter(Q(nombre__icontains=consulta) | Q(descripcion__icontains=consulta))
    return render(
        request,
        "tienda/catalogo.html",
        {
            "productos": productos.order_by("nombre"),
            "categoria_actual": categoria,
            "consulta": consulta,
        },
    )


def registro(request):
    if request.user.is_authenticated:
        return redirect("tienda:inicio")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cuenta creada correctamente. Ya puedes iniciar sesión.")
        return redirect("tienda:login")
    return render(request, "tienda/registro.html", {"form": form})


def iniciar_sesion(request):
    if request.user.is_authenticated:
        destino = "tienda:admin_dashboard" if request.user.es_administrador else "tienda:inicio"
        return redirect(destino)

    form = LoginForm(request.POST or None)
    siguiente = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST" and form.is_valid():
        identificador = form.cleaned_data["identificador"].strip()
        password = form.cleaned_data["password"]
        candidato = Usuario.objects.filter(
            Q(username__iexact=identificador) | Q(email__iexact=identificador)
        ).first()
        username = candidato.username if candidato else identificador
        usuario = authenticate(request, username=username, password=password)
        if usuario:
            login(request, usuario)
            messages.success(request, f"Bienvenido, {usuario.nombre_completo or usuario.username}.")
            if siguiente and url_has_allowed_host_and_scheme(siguiente, {request.get_host()}):
                return redirect(siguiente)
            if usuario.es_administrador:
                return redirect("tienda:admin_dashboard")
            return redirect("tienda:inicio")
        if candidato and not candidato.is_active:
            form.add_error(None, "Esta cuenta está desactivada. Contacta a administración.")
        else:
            form.add_error(None, "El correo/usuario o la contraseña no son correctos.")
    return render(request, "tienda/login.html", {"form": form, "next": siguiente})


@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("tienda:inicio")


@login_required
def perfil(request):
    form = PerfilForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        cambio_clave = bool(form.cleaned_data.get("clave_nueva1"))
        usuario = form.save()
        if cambio_clave:
            update_session_auth_hash(request, usuario)
        messages.success(request, "Tu perfil fue actualizado correctamente.")
        return redirect("tienda:perfil")
    return render(request, "tienda/perfil.html", {"form": form})


@cliente_requerido
def carrito(request):
    carro, _ = Carrito.objects.get_or_create(usuario=request.user)
    items = carro.items.select_related("producto", "producto__inventario")
    return render(request, "tienda/carrito.html", {"carrito": carro, "items": items})


@cliente_requerido
@require_POST
def agregar_carrito(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related("inventario"), pk=producto_id, activo=True
    )
    if producto.inventario.stock < 1:
        messages.warning(request, "Este producto no tiene stock disponible.")
        return redirect(request.POST.get("next") or "tienda:catalogo")
    carro, _ = Carrito.objects.get_or_create(usuario=request.user)
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carro, producto=producto, defaults={"cantidad": 1}
    )
    if not creado:
        if item.cantidad >= producto.inventario.stock:
            messages.warning(request, "No hay más unidades disponibles.")
            return redirect(request.POST.get("next") or "tienda:carrito")
        item.cantidad += 1
        item.save(update_fields=("cantidad",))
    messages.success(request, f"{producto.nombre} fue agregado al carrito.")
    destino = request.POST.get("next")
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}):
        return redirect(destino)
    return redirect("tienda:carrito")


@cliente_requerido
@require_POST
def actualizar_item_carrito(request, item_id):
    item = get_object_or_404(
        ItemCarrito.objects.select_related("producto__inventario"),
        pk=item_id,
        carrito__usuario=request.user,
    )
    try:
        cantidad = int(request.POST.get("cantidad", "1"))
    except ValueError:
        return HttpResponseBadRequest("Cantidad inválida")
    if cantidad < 1 or cantidad > item.producto.inventario.stock:
        messages.error(request, "La cantidad solicitada no corresponde al stock disponible.")
    else:
        item.cantidad = cantidad
        item.save(update_fields=("cantidad",))
        messages.success(request, "Cantidad actualizada.")
    return redirect("tienda:carrito")


@cliente_requerido
@require_POST
def eliminar_item_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, pk=item_id, carrito__usuario=request.user)
    item.delete()
    messages.success(request, "Producto eliminado del carrito.")
    return redirect("tienda:carrito")


@cliente_requerido
def pago(request):
    carro, _ = Carrito.objects.get_or_create(usuario=request.user)
    items = list(carro.items.select_related("producto", "producto__inventario"))
    if not items:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("tienda:carrito")

    form = PagoSimuladoForm(request.POST or None, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                inventarios = {
                    inv.producto_id: inv
                    for inv in Inventario.objects.select_for_update().filter(
                        producto_id__in=[item.producto_id for item in items]
                    )
                }
                for item in items:
                    inventario = inventarios[item.producto_id]
                    if not item.producto.activo or item.cantidad > inventario.stock:
                        raise ValueError(f"Stock insuficiente para {item.producto.nombre}.")

                total = sum((item.subtotal for item in items), Decimal("0"))
                pedido = Pedido.objects.create(
                    usuario=request.user,
                    total=total,
                    direccion_despacho=form.cleaned_data["direccion_despacho"],
                    ultimos_digitos=form.cleaned_data["numero_tarjeta"][-4:],
                )
                DetallePedido.objects.bulk_create(
                    [
                        DetallePedido(
                            pedido=pedido,
                            producto=item.producto,
                            nombre_producto=item.producto.nombre,
                            precio_unitario=item.producto.precio,
                            cantidad=item.cantidad,
                        )
                        for item in items
                    ]
                )
                for item in items:
                    inventario = inventarios[item.producto_id]
                    inventario.stock -= item.cantidad
                    inventario.save(update_fields=("stock", "actualizado"))
                carro.items.all().delete()
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("tienda:carrito")

        messages.success(request, f"Pago simulado correctamente. Pedido #{pedido.pk} creado.")
        return redirect("tienda:mis_compras")

    return render(request, "tienda/pago.html", {"form": form, "carrito": carro, "items": items})


@cliente_requerido
def mis_compras(request):
    pedidos = request.user.pedidos.prefetch_related("detalles").all()
    return render(request, "tienda/mis_compras.html", {"pedidos": pedidos})


@administrador_requerido
def admin_dashboard(request):
    contexto = {
        "productos": Producto.objects.count(),
        "clientes": Usuario.objects.filter(rol__codigo=Rol.CLIENTE).count(),
        "pedidos": Pedido.objects.count(),
        "ventas": Pedido.objects.aggregate(total=Sum("total"))["total"] or Decimal("0"),
        "stock_bajo": Inventario.objects.filter(stock__lt=5).select_related("producto")[:5],
        "ultimos_pedidos": Pedido.objects.select_related("usuario")[:5],
    }
    return render(request, "tienda/admin/dashboard.html", contexto)


@administrador_requerido
def admin_productos(request):
    productos = Producto.objects.select_related("categoria", "inventario").all()
    return render(request, "tienda/admin/productos.html", {"productos": productos})


@administrador_requerido
def admin_producto_crear(request):
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("tienda:admin_productos")
    return render(request, "tienda/admin/producto_form.html", {"form": form, "titulo": "Registrar producto"})


@administrador_requerido
def admin_producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("tienda:admin_productos")
    return render(request, "tienda/admin/producto_form.html", {"form": form, "titulo": "Editar producto"})


@administrador_requerido
def admin_producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == "POST":
        producto.delete()
        messages.success(request, "Producto eliminado correctamente.")
        return redirect("tienda:admin_productos")
    return render(request, "tienda/admin/confirmar_eliminar.html", {"objeto": producto, "tipo": "producto"})


@administrador_requerido
def admin_inventario(request):
    inventarios = Inventario.objects.select_related("producto", "producto__categoria").order_by("producto__nombre")
    if request.method == "POST":
        inventario = get_object_or_404(Inventario, pk=request.POST.get("inventario_id"))
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Stock de {inventario.producto.nombre} actualizado.")
        else:
            messages.error(request, "El stock debe ser un número entero mayor o igual a cero.")
        return redirect("tienda:admin_inventario")
    return render(request, "tienda/admin/inventario.html", {"inventarios": inventarios})


@administrador_requerido
def admin_usuarios(request):
    usuarios = Usuario.objects.select_related("rol").order_by("username")
    return render(request, "tienda/admin/usuarios.html", {"usuarios": usuarios})


@administrador_requerido
def admin_usuario_crear(request):
    form = UsuarioAdminCreacionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario creado correctamente.")
        return redirect("tienda:admin_usuarios")
    return render(request, "tienda/admin/usuario_form.html", {"form": form, "titulo": "Crear usuario"})


@administrador_requerido
def admin_usuario_editar(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    form = UsuarioAdminForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        editado = form.save(commit=False)
        if editado.pk == request.user.pk:
            editado.rol = Rol.objects.get(codigo=Rol.ADMINISTRADOR)
            editado.is_active = True
        editado.save()
        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("tienda:admin_usuarios")
    return render(request, "tienda/admin/usuario_form.html", {"form": form, "titulo": "Editar usuario"})


@administrador_requerido
def admin_usuario_eliminar(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes eliminar tu propia cuenta administrativa.")
        return redirect("tienda:admin_usuarios")
    if request.method == "POST":
        try:
            usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
        except ProtectedError:
            usuario.is_active = False
            usuario.save(update_fields=("is_active",))
            messages.warning(request, "El usuario tiene pedidos asociados; se desactivó para conservar el historial.")
        return redirect("tienda:admin_usuarios")
    return render(request, "tienda/admin/confirmar_eliminar.html", {"objeto": usuario, "tipo": "usuario"})


@administrador_requerido
def admin_pedidos(request):
    pedidos = Pedido.objects.select_related("usuario").prefetch_related("detalles")
    return render(request, "tienda/admin/pedidos.html", {"pedidos": pedidos, "estados": Pedido.ESTADOS})


@administrador_requerido
@require_POST
def admin_pedido_estado(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    form = EstadoPedidoForm(request.POST, instance=pedido)
    if form.is_valid():
        form.save()
        messages.success(request, f"Estado del pedido #{pedido.pk} actualizado.")
    else:
        messages.error(request, "El estado seleccionado no es válido.")
    return redirect("tienda:admin_pedidos")


def error_403(request, exception=None):
    return render(request, "tienda/error.html", {"codigo": 403, "mensaje": "No tienes permiso para ver esta página."}, status=403)


def error_404(request, exception=None):
    return render(request, "tienda/error.html", {"codigo": 404, "mensaje": "La página solicitada no existe."}, status=404)
