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
            "steam_app_id",
            "wikidata_id",
            "youtube_video_id",
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

    def validate(self, attrs):
        instancia = self.instance
        steam_app_id = attrs.get(
            "steam_app_id", getattr(instancia, "steam_app_id", None)
        )
        wikidata_id = attrs.get(
            "wikidata_id", getattr(instancia, "wikidata_id", "")
        )
        youtube_video_id = attrs.get(
            "youtube_video_id", getattr(instancia, "youtube_video_id", "")
        )

        if steam_app_id and wikidata_id:
            raise serializers.ValidationError(
                "Configura una ficha de Steam o Wikidata, no ambas."
            )
        if bool(steam_app_id or wikidata_id) != bool(youtube_video_id):
            raise serializers.ValidationError(
                "La ficha externa y el video de YouTube deben configurarse juntos."
            )
        return attrs
