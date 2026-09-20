from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def clp(valor):
    """Formatea un valor numérico como pesos chilenos sin decimales."""
    try:
        entero = int(Decimal(valor))
    except (InvalidOperation, TypeError, ValueError):
        return "$0"
    return "$" + f"{entero:,}".replace(",", ".")

