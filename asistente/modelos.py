"""Contratos de datos compartidos entre módulos.

Los módulos (visión, voz, recomendador, presentación) solo se comunican a
través de estas estructuras. Así cada uno se puede desarrollar y probar por
separado sustituyendo a los demás por versiones simuladas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Zona(str, Enum):
    """Parte del cuerpo que cubre una prenda."""

    SUPERIOR = "superior"
    INFERIOR = "inferior"

    def complementaria(self) -> "Zona":
        return Zona.INFERIOR if self is Zona.SUPERIOR else Zona.SUPERIOR


class Fuente(str, Enum):
    """De dónde viene lo que sabemos de la prenda que lleva puesta el usuario."""

    VISION = "vision"
    USUARIO = "usuario"  # confirmada o corregida por voz/teclado


@dataclass(frozen=True)
class ObservacionVisual:
    """Lo que el sistema cree que lleva puesto el usuario.

    `confianza` ya viene suavizada a lo largo de varios fotogramas.
    """

    zona: Zona
    tipo: str
    color: str | None
    confianza: float
    fuente: Fuente = Fuente.VISION


class Accion(str, Enum):
    """Qué quiere hacer el usuario con lo que acaba de decir."""

    PEDIR = "pedir"            # petición nueva: "¿qué pantalón va con esto?"
    MATIZAR = "matizar"        # ajuste de la petición actual: "algo más informal"
    OTRA = "otra"              # "otra", "dame otra"
    CONFIRMAR = "confirmar"    # "sí", "vale", "me lo quedo"
    NEGAR = "negar"            # "no"
    CORREGIR = "corregir"      # "llevo una camisa blanca"
    SALIR = "salir"
    DESCONOCIDA = "desconocida"


@dataclass(frozen=True)
class Intencion:
    """Interpretación estructurada de una frase del usuario.

    La produce el intérprete (reglas o LLM). Nunca contiene prendas concretas
    del armario: solo restricciones que luego aplica el recomendador.
    """

    accion: Accion
    texto: str = ""
    # Restricciones sobre la prenda que se pide
    zona: Zona | None = None
    tipo: str | None = None
    color: str | None = None
    formalidad: int | None = None       # 1 informal, 2 intermedio, 3 formal
    ajuste_formalidad: int = 0          # -1 "más informal", +1 "más formal"
    # Lo que el usuario dice que lleva puesto (para CORREGIR)
    prenda_puesta_tipo: str | None = None
    prenda_puesta_color: str | None = None


@dataclass
class Peticion:
    """Restricciones acumuladas de lo que el usuario está buscando ahora.

    Una petición nueva (PEDIR) la reinicia; los matices la van modificando.
    """

    zona: Zona | None = None
    tipo: str | None = None
    color: str | None = None
    formalidad: int | None = None


@dataclass(frozen=True)
class Prenda:
    """Una prenda del armario catalogado."""

    id: str
    zona: Zona
    tipo: str
    color: str
    formalidad: int  # 1 informal, 2 intermedio, 3 formal
    imagen: str      # ruta relativa a la carpeta de imágenes del catálogo


@dataclass(frozen=True)
class Sugerencia:
    """Resultado del recomendador: una prenda y el porqué."""

    prenda: Prenda
    motivo: str
    restricciones_relajadas: tuple[str, ...] = field(default_factory=tuple)
