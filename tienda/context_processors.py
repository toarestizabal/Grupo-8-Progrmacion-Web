def resumen_carrito(request):
    cantidad = 0
    if request.user.is_authenticated and getattr(request.user, "es_cliente", False):
        carrito = getattr(request.user, "carrito", None)
        if carrito:
            cantidad = sum(carrito.items.values_list("cantidad", flat=True))
    return {"cantidad_carrito": cantidad}

