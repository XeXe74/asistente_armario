"""Vocabulario común de tipos y colores de prenda.

Lo comparten el catálogo, el intérprete de voz, el recomendador y (en el
futuro) los prompts zero-shot de CLIP, para que todos usen las mismas
etiquetas. Las claves están normalizadas: minúsculas y sin tildes.
"""

from __future__ import annotations

import re
import unicodedata

from .modelos import Zona

# Tipo canónico -> zona
TIPOS: dict[str, Zona] = {
    "camiseta": Zona.SUPERIOR,
    "camisa": Zona.SUPERIOR,
    "polo": Zona.SUPERIOR,
    "sudadera": Zona.SUPERIOR,
    "jersey": Zona.SUPERIOR,
    "chaqueta": Zona.SUPERIOR,
    "vaquero": Zona.INFERIOR,
    "chino": Zona.INFERIOR,
    "pantalon de traje": Zona.INFERIOR,
    "chandal": Zona.INFERIOR,
    "pantalon corto": Zona.INFERIOR,
    "falda": Zona.INFERIOR,
}

# Formas que puede usar el usuario -> tipo canónico
SINONIMOS_TIPO: dict[str, str] = {
    **{t: t for t in TIPOS},
    "camisetas": "camiseta",
    "camisas": "camisa",
    "polos": "polo",
    "sudaderas": "sudadera",
    "jerseis": "jersey",
    "jersei": "jersey",
    "sueter": "jersey",
    "chaquetas": "chaqueta",
    "vaqueros": "vaquero",
    "tejano": "vaquero",
    "tejanos": "vaquero",
    "jeans": "vaquero",
    "chinos": "chino",
    "pantalones de traje": "pantalon de traje",
    "pantalon de vestir": "pantalon de traje",
    "pantalones de vestir": "pantalon de traje",
    "pantalones cortos": "pantalon corto",
    "bermudas": "pantalon corto",
    "shorts": "pantalon corto",
    "faldas": "falda",
}

# Palabras que indican solo la zona, sin tipo concreto
ZONAS_GENERICAS: dict[str, Zona] = {
    "pantalon": Zona.INFERIOR,
    "pantalones": Zona.INFERIOR,
    "parte de abajo": Zona.INFERIOR,
    "algo de abajo": Zona.INFERIOR,
    "parte de arriba": Zona.SUPERIOR,
    "algo de arriba": Zona.SUPERIOR,
    "prenda de arriba": Zona.SUPERIOR,
    "prenda de abajo": Zona.INFERIOR,
}

COLORES: set[str] = {
    "negro", "blanco", "gris", "beige", "marino", "azul", "rojo", "verde",
    "amarillo", "marron", "rosa", "morado", "naranja",
}

SINONIMOS_COLOR: dict[str, str] = {
    **{c: c for c in COLORES},
    "negra": "negro", "negros": "negro", "negras": "negro",
    "blanca": "blanco", "blancos": "blanco", "blancas": "blanco",
    "grises": "gris",
    "crema": "beige", "caqui": "beige",
    "azul marino": "marino", "azul oscuro": "marino",
    "azules": "azul", "azul claro": "azul",
    "roja": "rojo", "rojos": "rojo", "rojas": "rojo", "granate": "rojo",
    "verdes": "verde",
    "amarilla": "amarillo", "amarillos": "amarillo", "amarillas": "amarillo",
    "marrones": "marron",
    "rosas": "rosa",
    "morada": "morado", "morados": "morado", "moradas": "morado", "lila": "morado",
    "naranjas": "naranja",
}

NOMBRES_FORMALIDAD = {1: "informal", 2: "intermedio", 3: "formal"}

# Cómo se muestran al usuario las etiquetas normalizadas
_VISIBLE: dict[str, str] = {
    "pantalon de traje": "pantalón de traje",
    "pantalon corto": "pantalón corto",
    "chandal": "chándal",
    "marino": "azul marino",
    "marron": "marrón",
}


def visible(etiqueta: str) -> str:
    return _VISIBLE.get(etiqueta, etiqueta)


def describir(tipo: str, color: str | None) -> str:
    """'camiseta de color rojo' (evita problemas de concordancia de género)."""
    return f"{visible(tipo)} de color {visible(color)}" if color else visible(tipo)


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin signos de puntuación y espacios simples."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-zñ0-9 ]", " ", sin_tildes)).strip()


def buscar_frase(texto_normalizado: str, opciones: dict[str, object]) -> object | None:
    """Devuelve el valor de la clave más larga que aparezca como frase completa."""
    relleno = f" {texto_normalizado} "
    for clave in sorted(opciones, key=len, reverse=True):
        if f" {clave} " in relleno:
            return opciones[clave]
    return None


def contiene(texto_normalizado: str, frases: tuple[str, ...] | set[str]) -> bool:
    relleno = f" {texto_normalizado} "
    return any(f" {f} " in relleno for f in frases)
