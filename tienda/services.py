import json
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.core.cache import cache

FREETOGAME_URL = "https://www.freetogame.com/api/games?sort-by=popularity"
CACHE_KEY = "pixelforge:juegos_externos"


class ServicioExternoError(Exception):
    pass


def _url_https(valor):
    partes = urlsplit(str(valor or ""))
    return str(valor) if partes.scheme == "https" and partes.netloc else ""


def obtener_juegos_externos():
    almacenados = cache.get(CACHE_KEY)
    if almacenados is not None:
        return almacenados

    solicitud = Request(
        FREETOGAME_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "PixelForge-Academic/1.0",
        },
    )
    try:
        with urlopen(solicitud, timeout=8) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, JSONDecodeError, UnicodeDecodeError) as error:
        raise ServicioExternoError("El catálogo externo no está disponible en este momento.") from error

    if not isinstance(datos, list):
        raise ServicioExternoError("El servicio externo entregó una respuesta inesperada.")

    juegos = []
    for juego in datos[:12]:
        if not isinstance(juego, dict):
            continue
        titulo = str(juego.get("title", "")).strip()
        if not titulo:
            continue
        juegos.append(
            {
                "id": juego.get("id"),
                "titulo": titulo,
                "descripcion": str(juego.get("short_description", "")).strip(),
                "genero": str(juego.get("genre", "")).strip(),
                "plataforma": str(juego.get("platform", "")).strip(),
                "editor": str(juego.get("publisher", "")).strip(),
                "imagen": _url_https(juego.get("thumbnail")),
                "enlace": _url_https(juego.get("freetogame_profile_url")),
            }
        )

    if not juegos:
        raise ServicioExternoError("El servicio externo no entregó juegos para mostrar.")

    cache.set(CACHE_KEY, juegos, timeout=900)
    return juegos
