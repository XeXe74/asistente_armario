"""Política explícita de fusión visión-voz.

- Visión con confianza < umbral_confirmacion  -> se pide confirmación.
- La voz contradice a la visión:
    * confianza visual >= umbral_vision_gana -> gana la visión (se avisa).
      Si el usuario insiste una segunda vez, se le hace caso.
    * confianza intermedia                    -> se pide aclaración.
- Lo que el usuario ya confirmó o corrigió (fuente USUARIO) no se discute.
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum, auto

from ..modelos import Fuente, Intencion, ObservacionVisual, Zona
from ..vocabulario import TIPOS


class ResultadoFusion(Enum):
    SIN_CONFLICTO = auto()
    ACEPTAR_USUARIO = auto()
    GANA_VISION = auto()
    PEDIR_ACLARACION = auto()


def necesita_confirmacion(obs: ObservacionVisual, umbral_confirmacion: float) -> bool:
    return obs.fuente is Fuente.VISION and obs.confianza < umbral_confirmacion


def contradice(obs: ObservacionVisual, intencion: Intencion) -> bool:
    tipo, color = intencion.prenda_puesta_tipo, intencion.prenda_puesta_color
    return bool((tipo and tipo != obs.tipo) or (color and obs.color and color != obs.color))


def evaluar_correccion(
    obs: ObservacionVisual | None,
    intencion: Intencion,
    umbral_vision_gana: float,
    insistencias: int,
) -> ResultadoFusion:
    if obs is None or obs.fuente is Fuente.USUARIO:
        return ResultadoFusion.ACEPTAR_USUARIO
    if not contradice(obs, intencion):
        return ResultadoFusion.SIN_CONFLICTO
    if obs.confianza >= umbral_vision_gana:
        return ResultadoFusion.ACEPTAR_USUARIO if insistencias > 0 else ResultadoFusion.GANA_VISION
    return ResultadoFusion.PEDIR_ACLARACION


def aplicar_correccion(
    obs: ObservacionVisual | None, intencion: Intencion
) -> ObservacionVisual | None:
    """Prenda puesta resultante de lo que dice el usuario (completando con la visión)."""
    tipo = intencion.prenda_puesta_tipo or (obs.tipo if obs else None)
    if tipo is None:
        return None
    color = intencion.prenda_puesta_color or (obs.color if obs else None)
    zona = TIPOS.get(tipo, obs.zona if obs else Zona.SUPERIOR)
    return ObservacionVisual(zona=zona, tipo=tipo, color=color, confianza=1.0, fuente=Fuente.USUARIO)


def confirmar(obs: ObservacionVisual) -> ObservacionVisual:
    return replace(obs, confianza=1.0, fuente=Fuente.USUARIO)
