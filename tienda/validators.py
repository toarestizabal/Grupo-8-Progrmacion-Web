import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexityValidator:
    """Exige las cuatro reglas de seguridad solicitadas por la actividad."""

    def validate(self, password, user=None):
        errores = []
        if len(password) > 18:
            errores.append(_("La contraseña no puede superar los 18 caracteres."))
        if not re.search(r"[A-ZÁÉÍÓÚÑ]", password):
            errores.append(_("La contraseña debe contener una letra mayúscula."))
        if not re.search(r"[a-záéíóúñ]", password):
            errores.append(_("La contraseña debe contener una letra minúscula."))
        if not re.search(r"\d", password):
            errores.append(_("La contraseña debe contener un número."))
        if not re.search(r"[^A-Za-zÁÉÍÓÚÑáéíóúñ0-9]", password):
            errores.append(_("La contraseña debe contener un símbolo."))
        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        return _(
            "Entre 8 y 18 caracteres, con mayúscula, minúscula, número y símbolo."
        )

