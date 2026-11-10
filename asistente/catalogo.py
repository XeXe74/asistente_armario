"""Lectura y validación del catálogo de prendas (JSON)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .modelos import Prenda, Zona
from .vocabulario import COLORES, TIPOS

log = logging.getLogger(__name__)


def cargar_catalogo(ruta: str | Path) -> list[Prenda]:
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encuentra el catálogo: {ruta}")
    with ruta.open(encoding="utf-8") as f:
        datos = json.load(f)

    prendas: list[Prenda] = []
    ids: set[str] = set()
    for i, d in enumerate(datos.get("prendas", [])):
        try:
            prenda = Prenda(
                id=str(d["id"]),
                zona=Zona(d["zona"]),
                tipo=d["tipo"],
                color=d["color"],
                formalidad=int(d["formalidad"]),
                imagen=d.get("imagen", ""),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Prenda {i} del catálogo mal formada ({e}): {d}") from e
        if prenda.id in ids:
            raise ValueError(f"Id de prenda repetido en el catálogo: {prenda.id}")
        if prenda.formalidad not in (1, 2, 3):
            raise ValueError(f"Formalidad fuera de rango (1-3) en {prenda.id}")
        if prenda.tipo not in TIPOS:
            log.warning("Tipo desconocido en %s: %s", prenda.id, prenda.tipo)
        if prenda.color not in COLORES:
            log.warning("Color desconocido en %s: %s", prenda.id, prenda.color)
        ids.add(prenda.id)
        prendas.append(prenda)

    if not prendas:
        raise ValueError(f"El catálogo {ruta} no contiene prendas")
    log.info("Catálogo cargado: %d prendas", len(prendas))
    return prendas
