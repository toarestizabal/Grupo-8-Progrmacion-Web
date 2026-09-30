from rest_framework import serializers

from tienda.models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nombre", "slug", "descripcion", "imagen", "activa")
        read_only_fields = ("id",)

    def validate_nombre(self, value):
        return value.strip()

    def validate_descripcion(self, value):
        return value.strip()

    def validate_imagen(self, value):
        return value.strip().replace("\\", "/").rsplit("/", 1)[-1]


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    stock = serializers.IntegerField(source="inventario.stock", read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "categoria",
            "categoria_nombre",
            "nombre",
            "descripcion",
            "precio",
            "imagen",
            "activo",
            "stock",
            "creado",
            "actualizado",
        )
        read_only_fields = ("id", "categoria_nombre", "stock", "creado", "actualizado")

    def validate_nombre(self, value):
        return value.strip()

    def validate_descripcion(self, value):
        return value.strip()

    def validate_imagen(self, value):
        return value.strip().replace("\\", "/").rsplit("/", 1)[-1]
