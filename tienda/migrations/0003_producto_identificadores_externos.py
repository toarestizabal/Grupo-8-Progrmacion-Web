from django.db import migrations, models
import django.core.validators


PRODUCTOS_EXTERNOS = {
    "Halo: Campaign Evolved": (2806050, "", "5KhzCSeZxAU"),
    "Ghost of Yōtei": (None, "Q130360297", "7z7kqwuf0a8"),
    "Big Walk": (1478500, "", "vyQPc1i4Rpo"),
    "007 First Light": (3768760, "", "i-fgtpwEMPM"),
    "eBaseball: PRO SPIRIT 2026": (4150530, "", "MSdtPWXUCIk"),
    "Streetdog BMX": (2707870, "", "rPODn3M3o-s"),
    "Beast of Reincarnation": (2001760, "", "H0r-Kap8kWI"),
    "Nioh 3": (3681010, "", "30C75tjO3ms"),
    "MARVEL Tōkon: Fighting Souls": (3787240, "", "hzoWfRb2ZYI"),
    "Avatar Legends: The Fighting Game": (2424420, "", "nboz6eLKoaQ"),
}


def cargar_identificadores(apps, schema_editor):
    Producto = apps.get_model("tienda", "Producto")
    for nombre, (steam_id, wikidata_id, youtube_id) in PRODUCTOS_EXTERNOS.items():
        Producto.objects.filter(nombre=nombre).update(
            steam_app_id=steam_id,
            wikidata_id=wikidata_id,
            youtube_video_id=youtube_id,
        )


def limpiar_identificadores(apps, schema_editor):
    Producto = apps.get_model("tienda", "Producto")
    Producto.objects.filter(nombre__in=PRODUCTOS_EXTERNOS).update(
        steam_app_id=None,
        wikidata_id="",
        youtube_video_id="",
    )


class Migration(migrations.Migration):
    dependencies = [("tienda", "0002_alter_producto_precio")]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="steam_app_id",
            field=models.PositiveBigIntegerField(
                blank=True,
                help_text="Completa Steam o Wikidata, no ambos.",
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="ID de aplicación en Steam",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="wikidata_id",
            field=models.CharField(
                blank=True,
                help_text="Ejemplo: Q130360297.",
                max_length=20,
                verbose_name="ID de entidad en Wikidata",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="youtube_video_id",
            field=models.CharField(
                blank=True,
                help_text="Solo el identificador ubicado después de v= en la URL.",
                max_length=20,
                verbose_name="ID del video en YouTube",
            ),
        ),
        migrations.RunPython(cargar_identificadores, limpiar_identificadores),
    ]
