"""Visión real (PENDIENTE): YOLO (DeepFashion2) + CLIP zero-shot + k-means.

Debe cumplir la interfaz `FuenteVision` (iniciar / detener / observacion_actual).
"""

from __future__ import annotations

from ..modelos import ObservacionVisual


class VisionYoloClip:
    def __init__(self, **_config):
        raise NotImplementedError(
            "La visión real todavía no está implementada. "
            "Usa vision.modo: simulada en config.yaml."
        )

    def iniciar(self) -> None: ...

    def detener(self) -> None: ...

    def observacion_actual(self) -> ObservacionVisual | None: ...
