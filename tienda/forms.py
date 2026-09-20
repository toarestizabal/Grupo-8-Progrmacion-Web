from datetime import date

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Inventario, Pedido, Producto, Rol, Usuario


class BootstrapFormMixin:
    def aplicar_estilos(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)


class RegistroForm(BootstrapFormMixin, UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Entre 8 y 18 caracteres, con mayúscula, minúscula, número y símbolo.",
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = (
            "nombre_completo",
            "username",
            "email",
            "password1",
            "password2",
            "fecha_nacimiento",
            "direccion",
        )
        labels = {
            "nombre_completo": "Nombre completo",
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
            "fecha_nacimiento": "Fecha de nacimiento",
            "direccion": "Dirección de despacho (opcional)",
        }
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()
        self.fields["username"].help_text = "Usa letras, números y los símbolos @/./+/-/_ únicamente."

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_fecha_nacimiento(self):
        nacimiento = self.cleaned_data.get("fecha_nacimiento")
        if not nacimiento:
            raise ValidationError("La fecha de nacimiento es obligatoria.")
        hoy = date.today()
        edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        if nacimiento > hoy:
            raise ValidationError("La fecha de nacimiento no puede estar en el futuro.")
        if edad < 13:
            raise ValidationError("Debes tener al menos 13 años para registrarte.")
        return nacimiento

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol, _ = Rol.objects.get_or_create(
            codigo=Rol.CLIENTE,
            defaults={"nombre": "Cliente"},
        )
        if commit:
            usuario.save()
        return usuario


class LoginForm(BootstrapFormMixin, forms.Form):
    identificador = forms.CharField(
        label="Correo o nombre de usuario",
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()


class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    clave_nueva1 = forms.CharField(
        label="Nueva contraseña (opcional)",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Déjala vacía para conservar la contraseña actual.",
    )
    clave_nueva2 = forms.CharField(
        label="Repetir nueva contraseña",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ("nombre_completo", "username", "email", "fecha_nacimiento", "direccion")
        labels = {
            "nombre_completo": "Nombre completo",
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
            "fecha_nacimiento": "Fecha de nacimiento",
            "direccion": "Dirección de despacho",
        }
        widgets = {"fecha_nacimiento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe otra cuenta con este correo.")
        return email

    def clean(self):
        cleaned = super().clean()
        clave1 = cleaned.get("clave_nueva1")
        clave2 = cleaned.get("clave_nueva2")
        if clave1 or clave2:
            if clave1 != clave2:
                self.add_error("clave_nueva2", "Las contraseñas no coinciden.")
            elif clave1:
                try:
                    password_validation.validate_password(clave1, self.instance)
                except ValidationError as error:
                    self.add_error("clave_nueva1", error)
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("clave_nueva1"):
            usuario.set_password(self.cleaned_data["clave_nueva1"])
        if commit:
            usuario.save()
        return usuario


class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    stock = forms.IntegerField(label="Stock", min_value=0, required=False, initial=0)

    class Meta:
        model = Producto
        fields = ("nombre", "categoria", "descripcion", "precio", "imagen", "activo")
        labels = {
            "categoria": "Categoría",
            "descripcion": "Descripción",
            "precio": "Precio (CLP)",
            "imagen": "Archivo de imagen",
            "activo": "Visible en el catálogo",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "precio": forms.NumberInput(attrs={"min": "1", "step": "1"}),
            "imagen": forms.TextInput(attrs={"placeholder": "Halo Campaign Evolved.jpg"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance, "inventario"):
            self.fields["stock"].initial = self.instance.inventario.stock
        self.aplicar_estilos()

    def clean_imagen(self):
        imagen = self.cleaned_data["imagen"].strip().replace("\\", "/")
        return imagen.rsplit("/", 1)[-1]

    def save(self, commit=True):
        producto = super().save(commit=commit)
        if commit:
            inventario, _ = Inventario.objects.get_or_create(producto=producto)
            stock = self.cleaned_data.get("stock")
            if stock is not None:
                inventario.stock = stock
                inventario.save(update_fields=("stock", "actualizado"))
        return producto


class InventarioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ("stock",)
        widgets = {"stock": forms.NumberInput(attrs={"min": 0, "class": "form-control stock-admin"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()


class UsuarioAdminCreacionForm(RegistroForm):
    rol = forms.ModelChoiceField(queryset=Rol.objects.none(), label="Rol")

    class Meta(RegistroForm.Meta):
        fields = RegistroForm.Meta.fields + ("rol",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].queryset = Rol.objects.all()
        self.aplicar_estilos()

    def save(self, commit=True):
        usuario = UserCreationForm.save(self, commit=False)
        usuario.rol = self.cleaned_data["rol"]
        if commit:
            usuario.save()
        return usuario


class UsuarioAdminForm(BootstrapFormMixin, forms.ModelForm):
    nueva_clave = forms.CharField(
        label="Nueva contraseña (opcional)",
        required=False,
        strip=False,
        widget=forms.PasswordInput(),
    )

    class Meta:
        model = Usuario
        fields = (
            "nombre_completo",
            "username",
            "email",
            "fecha_nacimiento",
            "direccion",
            "rol",
            "is_active",
        )
        labels = {"is_active": "Cuenta activa", "rol": "Rol"}
        widgets = {"fecha_nacimiento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe otra cuenta con este correo.")
        return email

    def clean_nueva_clave(self):
        clave = self.cleaned_data.get("nueva_clave")
        if clave:
            password_validation.validate_password(clave, self.instance)
        return clave

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("nueva_clave"):
            usuario.set_password(self.cleaned_data["nueva_clave"])
        if commit:
            usuario.save()
        return usuario


class EstadoPedidoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ("estado",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()


class PagoSimuladoForm(BootstrapFormMixin, forms.Form):
    direccion_despacho = forms.CharField(label="Dirección de despacho", max_length=250)
    titular = forms.CharField(label="Nombre del titular", max_length=120)
    numero_tarjeta = forms.CharField(
        label="Número de tarjeta",
        min_length=13,
        max_length=19,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-number"}),
    )
    vencimiento = forms.CharField(
        label="Vencimiento (MM/AA)",
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "placeholder": "MM/AA",
                "autocomplete": "cc-exp",
                "inputmode": "numeric",
                "data-expiry": "true",
            }
        ),
    )
    cvv = forms.CharField(
        label="CVV",
        min_length=3,
        max_length=4,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "cc-csc"}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario and not self.is_bound:
            self.initial["direccion_despacho"] = usuario.direccion
        self.aplicar_estilos()

    def clean_numero_tarjeta(self):
        numero = "".join(filter(str.isdigit, self.cleaned_data["numero_tarjeta"]))
        if not 13 <= len(numero) <= 19:
            raise ValidationError("Ingresa un número de tarjeta válido para la simulación.")
        return numero

    def clean_vencimiento(self):
        valor = self.cleaned_data["vencimiento"].strip()
        if len(valor) == 4 and valor.isdigit():
            mes, anio = int(valor[:2]), int(valor[2:])
        elif len(valor) == 5 and valor[2] == "/" and valor[:2].isdigit() and valor[3:].isdigit():
            mes, anio = int(valor[:2]), int(valor[3:])
        else:
            raise ValidationError("Usa el formato MM/AA.")
        if mes < 1 or mes > 12:
            raise ValidationError("El mes de vencimiento no es válido.")
        hoy = date.today()
        if (2000 + anio, mes) < (hoy.year, hoy.month):
            raise ValidationError("La tarjeta simulada está vencida.")
        return f"{mes:02d}/{anio:02d}"

    def clean_cvv(self):
        cvv = self.cleaned_data["cvv"]
        if not cvv.isdigit():
            raise ValidationError("El CVV debe contener solamente números.")
        return cvv
