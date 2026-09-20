from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Rol(models.Model):
    CLIENTE = "CLIENTE"
    ADMINISTRADOR = "ADMINISTRADOR"
    CODIGOS = ((CLIENTE, "Cliente"), (ADMINISTRADOR, "Administrador"))

    codigo = models.CharField(max_length=20, choices=CODIGOS, unique=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "PF_ROLES"
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    email = models.EmailField("correo electrónico", unique=True)
    nombre_completo = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "PF_USUARIOS"
        ordering = ("username",)

    @property
    def es_administrador(self):
        return self.is_superuser or (self.rol_id and self.rol.codigo == Rol.ADMINISTRADOR)

    @property
    def es_cliente(self):
        return bool(self.rol_id and self.rol.codigo == Rol.CLIENTE)

    def save(self, *args, **kwargs):
        if self.is_superuser or (self.rol_id and self.rol.codigo == Rol.ADMINISTRADOR):
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.email})"


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    descripcion = models.CharField(max_length=250, blank=True)
    imagen = models.CharField(max_length=200, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "PF_CATEGORIAS"
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("tienda:catalogo_categoria", kwargs={"slug": self.slug})


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1"))],
    )
    imagen = models.CharField(
        max_length=200,
        help_text="Nombre del archivo ubicado en tienda/static/tienda/images/",
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "PF_PRODUCTOS"
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre


class Inventario(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name="inventario")
    stock = models.PositiveIntegerField(default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "PF_INVENTARIO"

    def __str__(self):
        return f"{self.producto.nombre}: {self.stock} unidades"


class Carrito(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="carrito")
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "PF_CARRITOS"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.select_related("producto")), Decimal("0"))

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="items_carrito")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        db_table = "PF_ITEMS_CARRITO"
        constraints = [
            models.UniqueConstraint(fields=("carrito", "producto"), name="PF_UQ_CARRITO_PRODUCTO")
        ]

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} × {self.producto.nombre}"


class Pedido(models.Model):
    PAGADO = "PAGADO"
    PREPARANDO = "PREPARANDO"
    ENVIADO = "ENVIADO"
    ENTREGADO = "ENTREGADO"
    ESTADOS = (
        (PAGADO, "Pagado"),
        (PREPARANDO, "Preparando"),
        (ENVIADO, "Enviado"),
        (ENTREGADO, "Entregado"),
    )

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default=PAGADO)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    direccion_despacho = models.CharField(max_length=250)
    ultimos_digitos = models.CharField(max_length=4, blank=True)

    class Meta:
        db_table = "PF_PEDIDOS"
        ordering = ("-fecha",)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario.username}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        related_name="detalles_pedido",
        null=True,
        blank=True,
    )
    nombre_producto = models.CharField(max_length=150)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "PF_DETALLES_PEDIDO"
        constraints = [
            models.UniqueConstraint(fields=("pedido", "producto"), name="PF_UQ_PEDIDO_PRODUCTO")
        ]

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f"{self.cantidad} × {self.nombre_producto}"
