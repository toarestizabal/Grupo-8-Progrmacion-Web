from rest_framework import serializers

from tienda.models import Categoria


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
