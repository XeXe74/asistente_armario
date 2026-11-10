from __future__ import annotations

from typing import Protocol

from ..modelos import ObservacionVisual


class FuenteVision(Protocol):
    """Interfaz de cualquier módulo de visión.

    La implementación real corre la cámara en su propio hilo y va actualizando
    la última observación suavizada; el núcleo solo la consulta cuando la
    necesita (arquitectura por eventos, sin bloquear el diálogo).
    """

    def iniciar(self) -> None: ...

    def detener(self) -> None: ...

    def observacion_actual(self) -> ObservacionVisual | None:
        """Última observación estable, o None si no se detecta ninguna prenda."""
        ...
