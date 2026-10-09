import os
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from tienda.models import Categoria, Inventario, Producto, Rol, Usuario


CATEGORIAS = [
    ("Acción", "accion", "Combate intenso, estrategia rápida y adrenalina.", "accion.svg"),
    ("Aventura", "aventura", "Explora mundos, resuelve misterios y vive grandes historias.", "aventura.svg"),
    ("Deportes", "deportes", "Competencia deportiva para jugar solo o con amigos.", "deportes.svg"),
    ("RPG", "rpg", "Personajes, decisiones y progresión en mundos inolvidables.", "rpg.svg"),
    ("Combate", "combate", "Domina técnicas y enfréntate a rivales legendarios.", "combate.svg"),
]

PRODUCTOS = [
    ("Halo: Campaign Evolved", "accion", "Una campaña de ciencia ficción completamente renovada.", "49990", 12, "Halo Campaign Evolved.jpg", 2806050, "", "5KhzCSeZxAU"),
    ("Ghost of Yōtei", "accion", "Acción samurái en un territorio salvaje y espectacular.", "69990", 8, "Ghost of Yōtei.jpg", None, "Q130360297", "7z7kqwuf0a8"),
    ("Big Walk", "aventura", "Una aventura cooperativa relajada llena de descubrimientos.", "19990", 20, "Big Walk.jpg", 1478500, "", "vyQPc1i4Rpo"),
    ("007 First Light", "aventura", "Los orígenes de un agente en una misión cinematográfica.", "69990", 6, "007 First Light.jpg", 3768760, "", "i-fgtpwEMPM"),
    ("eBaseball: PRO SPIRIT 2026", "deportes", "Béisbol profesional con estadios y plantillas actualizadas.", "59990", 10, "eBaseball PRO SPIRIT 2026.jpg", 4150530, "", "MSdtPWXUCIk"),
    ("Streetdog BMX", "deportes", "Trucos, velocidad y libertad sobre dos ruedas.", "19990", 15, "Streetdog BMX.jpg", 2707870, "", "rPODn3M3o-s"),
    ("Beast of Reincarnation", "rpg", "Un RPG de acción ambientado en una tierra misteriosa.", "59990", 7, "Beast of Reincarnation.jpg", 2001760, "", "H0r-Kap8kWI"),
    ("Nioh 3", "rpg", "Combates exigentes contra guerreros y criaturas sobrenaturales.", "69990", 9, "Nioh 3.jpg", 3681010, "", "30C75tjO3ms"),
    ("MARVEL Tōkon: Fighting Souls", "combate", "Héroes y villanos se enfrentan en equipos espectaculares.", "59990", 11, "MARVEL Tōkon Fighting Souls.jpg", 3787240, "", "hzoWfRb2ZYI"),
    ("Avatar Legends: The Fighting Game", "combate", "Domina los elementos en combates competitivos.", "29990", 14, "Avatar Legends The Fighting Game.jpg", 2424420, "", "nboz6eLKoaQ"),
]


class Command(BaseCommand):
    help = "Carga roles, categorías, productos, inventario y cuentas de demostración."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Restablece también las contraseñas de las cuentas de demostración.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rol_cliente, _ = Rol.objects.update_or_create(
            codigo=Rol.CLIENTE,
            defaults={"nombre": "Cliente", "descripcion": "Compra productos y revisa sus pedidos."},
        )
        rol_admin, _ = Rol.objects.update_or_create(
            codigo=Rol.ADMINISTRADOR,
            defaults={"nombre": "Administrador", "descripcion": "Gestiona productos, inventario, usuarios y pedidos."},
        )

        categorias = {}
        for nombre, slug, descripcion, imagen in CATEGORIAS:
            categoria, _ = Categoria.objects.update_or_create(
                slug=slug,
                defaults={"nombre": nombre, "descripcion": descripcion, "imagen": imagen, "activa": True},
            )
            categorias[slug] = categoria

        for (
            nombre,
            slug,
            descripcion,
            precio,
            stock,
            imagen,
            steam_app_id,
            wikidata_id,
            youtube_video_id,
        ) in PRODUCTOS:
            producto, _ = Producto.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "categoria": categorias[slug],
                    "descripcion": descripcion,
                    "precio": Decimal(precio),
                    "imagen": imagen,
                    "steam_app_id": steam_app_id,
                    "wikidata_id": wikidata_id,
                    "youtube_video_id": youtube_video_id,
                    "activo": True,
                },
            )
            Inventario.objects.update_or_create(producto=producto, defaults={"stock": stock})

        cuentas = [
            {
                "username": "admin",
                "email": "admin@pixelforge.cl",
                "nombre_completo": "Administrador PixelForge",
                "fecha_nacimiento": date(1992, 3, 15),
                "direccion": "Av. Libertador Bernardo O'Higgins 1449, Santiago",
                "rol": rol_admin,
                "password": os.getenv("SEED_ADMIN_PASSWORD", "Admin123!"),
            },
            {
                "username": "cliente",
                "email": "cliente@pixelforge.cl",
                "nombre_completo": "Cliente de prueba",
                "fecha_nacimiento": date(1998, 7, 27),
                "direccion": "Av. Providencia 1234, Providencia, Santiago",
                "rol": rol_cliente,
                "password": os.getenv("SEED_CLIENT_PASSWORD", "Cliente123!"),
            },
        ]
        for datos in cuentas:
            password = datos.pop("password")
            usuario, creado = Usuario.objects.update_or_create(
                username=datos["username"],
                defaults={**datos, "is_active": True},
            )
            if creado or options["reset_passwords"]:
                usuario.set_password(password)
                usuario.save()

        self.stdout.write(self.style.SUCCESS("Datos iniciales de PixelForge cargados correctamente."))
