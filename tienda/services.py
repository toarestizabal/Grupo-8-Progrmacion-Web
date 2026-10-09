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


def _valor_localizado(valores):
    for idioma in ("es", "en", "mul"):
        valor = valores.get(idioma, {}).get("value", "")
        if valor:
            return valor
    return ""


def _ids_de_propiedad(entidad, propiedad):
    ids = []
    for declaracion in entidad.get("claims", {}).get(propiedad, []):
        valor = declaracion.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        identificador = valor.get("id") if isinstance(valor, dict) else ""
        if identificador:
            ids.append(identificador)
    return ids


def _obtener_ficha_wikidata(entidad_id, titulo_predeterminado=""):
    parametros = urlencode(
        {
            "action": "wbgetentities",
            "ids": entidad_id,
            "format": "json",
            "props": "labels|descriptions|claims",
            "languages": "es|en|mul",
        }
    )
    respuesta = _solicitar_json(
        f"https://www.wikidata.org/w/api.php?{parametros}",
        "Wikidata no está disponible en este momento.",
    )
    entidad = respuesta.get("entities", {}).get(entidad_id, {})
    if not entidad or entidad.get("missing") is not None:
        raise ServicioExternoError("Wikidata no entregó información del videojuego.")

    propiedades = {
        "desarrollador": "P178",
        "editor": "P123",
        "plataformas": "P400",
        "generos": "P136",
    }
    ids_por_campo = {
        campo: _ids_de_propiedad(entidad, propiedad)
        for campo, propiedad in propiedades.items()
    }
    ids_relacionados = sorted(
        {identificador for ids in ids_por_campo.values() for identificador in ids}
    )
    etiquetas = {}
    if ids_relacionados:
        parametros_etiquetas = urlencode(
            {
                "action": "wbgetentities",
                "ids": "|".join(ids_relacionados),
                "format": "json",
                "props": "labels",
                "languages": "es|en|mul",
            }
        )
        respuesta_etiquetas = _solicitar_json(
            f"https://www.wikidata.org/w/api.php?{parametros_etiquetas}",
            "Wikidata no está disponible en este momento.",
        )
        etiquetas = {
            identificador: _valor_localizado(datos.get("labels", {}))
            for identificador, datos in respuesta_etiquetas.get("entities", {}).items()
        }

    fecha = ""
    declaraciones_fecha = entidad.get("claims", {}).get("P577", [])
    if declaraciones_fecha:
        valor_fecha = (
            declaraciones_fecha[0]
            .get("mainsnak", {})
            .get("datavalue", {})
            .get("value", {})
        )
        fecha = valor_fecha.get("time", "") if isinstance(valor_fecha, dict) else ""
    if fecha:
        try:
            fecha = datetime.fromisoformat(fecha.lstrip("+").replace("Z", "+00:00")).strftime(
                "%d-%m-%Y"
            )
        except ValueError:
            fecha = fecha.lstrip("+")[:10]

    campos = {
        campo: _unir_valores(etiquetas.get(identificador, identificador) for identificador in ids)
        for campo, ids in ids_por_campo.items()
    }
    return {
        "titulo": _valor_localizado(entidad.get("labels", {}))
        or titulo_predeterminado
        or entidad_id,
        "resumen": _valor_localizado(entidad.get("descriptions", {}))
        or "Videojuego de acción y aventura.",
        **campos,
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


def obtener_informacion_producto(producto):
    if not producto.tiene_servicios_externos:
        raise ServicioExternoError("Este producto no tiene servicios externos configurados.")

    identidad = (
        f"{producto.pk}:{producto.steam_app_id or ''}:"
        f"{producto.wikidata_id}:{producto.youtube_video_id}"
    )
    identificador_cache = sha256(identidad.encode("utf-8")).hexdigest()[:16]
    clave_cache = f"pixelforge:producto_externo:{identificador_cache}"
    almacenada = cache.get(clave_cache)
    if almacenada is not None:
        return almacenada

    if producto.steam_app_id:
        ficha = _obtener_ficha_steam(producto.steam_app_id)
    else:
        ficha = _obtener_ficha_wikidata(producto.wikidata_id, producto.nombre)
    trailer = _obtener_trailer_youtube(producto.youtube_video_id)

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
