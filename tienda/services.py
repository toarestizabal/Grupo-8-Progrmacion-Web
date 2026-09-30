import json
import re
from hashlib import sha256
from datetime import datetime
from html import unescape
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from django.core.cache import cache

FREETOGAME_URL = "https://www.freetogame.com/api/games?sort-by=popularity"
CACHE_KEY = "pixelforge:juegos_externos"

PRODUCTOS_EXTERNOS = {
    "Halo: Campaign Evolved": {"steam": 2806050, "youtube": "5KhzCSeZxAU"},
    "Ghost of Yōtei": {"wikidata": "Q130360297", "youtube": "7z7kqwuf0a8"},
    "Big Walk": {"steam": 1478500, "youtube": "vyQPc1i4Rpo"},
    "007 First Light": {"steam": 3768760, "youtube": "i-fgtpwEMPM"},
    "eBaseball: PRO SPIRIT 2026": {"steam": 4150530, "youtube": "MSdtPWXUCIk"},
    "Streetdog BMX": {"steam": 2707870, "youtube": "rPODn3M3o-s"},
    "Beast of Reincarnation": {"steam": 2001760, "youtube": "H0r-Kap8kWI"},
    "Nioh 3": {"steam": 3681010, "youtube": "30C75tjO3ms"},
    "MARVEL Tōkon: Fighting Souls": {"steam": 3787240, "youtube": "hzoWfRb2ZYI"},
    "Avatar Legends: The Fighting Game": {"steam": 2424420, "youtube": "nboz6eLKoaQ"},
}


class ServicioExternoError(Exception):
    pass


def _solicitar_json(url, mensaje):
    solicitud = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PixelForge-Academic/1.0",
        },
    )
    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, JSONDecodeError, UnicodeDecodeError) as error:
        raise ServicioExternoError(mensaje) from error


def _texto_sin_html(valor):
    texto = re.sub(r"<[^>]+>", " ", str(valor or ""))
    return " ".join(unescape(texto).split())


def _unir_valores(valores):
    limpios = []
    for valor in valores:
        texto = str(valor or "").strip()
        if texto and texto not in limpios:
            limpios.append(texto)
    return ", ".join(limpios)


def _obtener_ficha_steam(app_id):
    parametros = urlencode({"appids": app_id, "cc": "cl", "l": "spanish"})
    respuesta = _solicitar_json(
        f"https://store.steampowered.com/api/appdetails?{parametros}",
        "Steam Store no está disponible en este momento.",
    )
    entrada = respuesta.get(str(app_id), {})
    datos = entrada.get("data") if entrada.get("success") else None
    if not isinstance(datos, dict):
        raise ServicioExternoError("Steam Store no entregó información del videojuego.")

    plataformas = []
    disponibles = datos.get("platforms") or {}
    if disponibles.get("windows"):
        plataformas.append("Windows")
    if disponibles.get("mac"):
        plataformas.append("macOS")
    if disponibles.get("linux"):
        plataformas.append("Linux")

    lanzamiento = datos.get("release_date") or {}
    fecha = str(lanzamiento.get("date") or "").strip()
    if not fecha:
        fecha = "Próximamente" if lanzamiento.get("coming_soon") else "Disponible"

    return {
        "titulo": str(datos.get("name") or "").strip(),
        "resumen": _texto_sin_html(datos.get("short_description")),
        "desarrollador": _unir_valores(datos.get("developers") or []),
        "editor": _unir_valores(datos.get("publishers") or []),
        "plataformas": _unir_valores(plataformas),
        "generos": _unir_valores(
            genero.get("description") for genero in datos.get("genres") or []
        ),
        "lanzamiento": fecha,
        "servicio": "Steam Store",
    }


def _obtener_ficha_wikidata(entidad_id):
    consulta = f"""
PREFIX schema: <http://schema.org/>
SELECT ?item ?itemLabel ?date ?developerLabel ?publisherLabel ?platformLabel
       ?genreLabel ?description WHERE {{
  VALUES ?item {{ wd:{entidad_id} }}
  OPTIONAL {{ ?item wdt:P577 ?date. }}
  OPTIONAL {{ ?item wdt:P178 ?developer. }}
  OPTIONAL {{ ?item wdt:P123 ?publisher. }}
  OPTIONAL {{ ?item wdt:P400 ?platform. }}
  OPTIONAL {{ ?item wdt:P136 ?genre. }}
  OPTIONAL {{
    ?item schema:description ?description.
    FILTER(LANG(?description) = "es" || LANG(?description) = "en")
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en,mul". }}
}}
"""
    parametros = urlencode({"query": consulta, "format": "json"})
    respuesta = _solicitar_json(
        f"https://query.wikidata.org/sparql?{parametros}",
        "Wikidata no está disponible en este momento.",
    )
    filas = respuesta.get("results", {}).get("bindings", [])
    if not filas:
        raise ServicioExternoError("Wikidata no entregó información del videojuego.")

    def valores(campo):
        return [fila.get(campo, {}).get("value", "") for fila in filas]

    fecha = next((valor for valor in valores("date") if valor), "")
    if fecha:
        try:
            fecha = datetime.fromisoformat(fecha.replace("Z", "+00:00")).strftime("%d-%m-%Y")
        except ValueError:
            fecha = fecha[:10]

    descripciones = [
        (
            fila.get("description", {}).get("xml:lang", ""),
            fila.get("description", {}).get("value", ""),
        )
        for fila in filas
        if fila.get("description", {}).get("value")
    ]
    descripciones.sort(key=lambda item: item[0] != "es")

    return {
        "titulo": next((valor for valor in valores("itemLabel") if valor), entidad_id),
        "resumen": descripciones[0][1] if descripciones else "Videojuego de acción y aventura.",
        "desarrollador": _unir_valores(valores("developerLabel")),
        "editor": _unir_valores(valores("publisherLabel")),
        "plataformas": _unir_valores(valores("platformLabel")),
        "generos": _unir_valores(valores("genreLabel")),
        "lanzamiento": fecha or "Disponible",
        "servicio": "Wikidata",
    }


def _obtener_trailer_youtube(video_id):
    url_video = f"https://www.youtube.com/watch?v={video_id}"
    parametros = urlencode({"url": url_video, "format": "json"})
    datos = _solicitar_json(
        f"https://www.youtube.com/oembed?{parametros}",
        "YouTube no está disponible en este momento.",
    )
    titulo = str(datos.get("title") or "").strip()
    if not titulo:
        raise ServicioExternoError("YouTube no entregó información del tráiler.")
    return {
        "titulo": titulo,
        "canal": str(datos.get("author_name") or "").strip(),
        "miniatura": _url_https(datos.get("thumbnail_url")),
        "video": f"https://www.youtube-nocookie.com/embed/{video_id}",
        "servicio": "YouTube oEmbed",
    }


def obtener_informacion_producto(nombre):
    configuracion = PRODUCTOS_EXTERNOS.get(nombre)
    if not configuracion:
        raise ServicioExternoError("Este producto no tiene servicios externos configurados.")

    identificador_cache = sha256(nombre.encode("utf-8")).hexdigest()[:16]
    clave_cache = f"pixelforge:producto_externo:{identificador_cache}"
    almacenada = cache.get(clave_cache)
    if almacenada is not None:
        return almacenada

    if "steam" in configuracion:
        ficha = _obtener_ficha_steam(configuracion["steam"])
    else:
        ficha = _obtener_ficha_wikidata(configuracion["wikidata"])
    trailer = _obtener_trailer_youtube(configuracion["youtube"])

    campos_ficha = (
        "titulo",
        "resumen",
        "desarrollador",
        "editor",
        "plataformas",
        "generos",
        "lanzamiento",
    )
    if any(not ficha.get(campo) for campo in campos_ficha):
        raise ServicioExternoError("La ficha externa del videojuego está incompleta.")
    if any(not trailer.get(campo) for campo in ("titulo", "canal", "video")):
        raise ServicioExternoError("La información externa del tráiler está incompleta.")

    resultado = {"ficha": ficha, "trailer": trailer}
    cache.set(clave_cache, resultado, timeout=21600)
    return resultado


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
