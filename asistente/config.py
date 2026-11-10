"""Carga de la configuración (config.yaml), fuera del código."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CONFIG_POR_DEFECTO = RAIZ_PROYECTO / "config.yaml"


def cargar_config(ruta: str | Path | None = None) -> dict[str, Any]:
    ruta = Path(ruta) if ruta else CONFIG_POR_DEFECTO
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encuentra el fichero de configuración: {ruta}")
    with ruta.open(encoding="utf-8") as f:
        datos = yaml.safe_load(f) or {}
    if not isinstance(datos, dict):
        raise ValueError(f"{ruta} debe contener un diccionario YAML")
    return datos


def ruta_proyecto(relativa: str | Path) -> Path:
    """Convierte una ruta relativa de la configuración en absoluta respecto al proyecto."""
    ruta = Path(relativa)
    return ruta if ruta.is_absolute() else RAIZ_PROYECTO / ruta
