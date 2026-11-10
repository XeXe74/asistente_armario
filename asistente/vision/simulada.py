"""Visión simulada: devuelve siempre la observación fijada en config.yaml.

Sirve para desarrollar el resto del sistema sin cámara y para forzar los
caminos alternativos (p. ej. confianza baja -> pedir confirmación).
"""

from __future__ import annotations

from ..modelos import ObservacionVisual, Zona


class VisionSimulada:
    def __init__(self, zona: str, tipo: str | None, color: str | None, confianza: float):
        self._observacion = (
            None if tipo is None
            else ObservacionVisual(zona=Zona(zona), tipo=tipo, color=color, confianza=confianza)
        )

    def iniciar(self) -> None:
        pass

    def detener(self) -> None:
        pass

    def observacion_actual(self) -> ObservacionVisual | None:
        return self._observacion
