from __future__ import annotations

from typing import Protocol

from ..modelos import Intencion


class EntradaVoz(Protocol):
    """Captura una frase del usuario (push-to-talk) y devuelve su transcripción."""

    def escuchar(self) -> str | None:
        """Texto transcrito, o None si no se captó nada (silencio, ruido)."""
        ...


class Interprete(Protocol):
    """Convierte una transcripción en una intención estructurada."""

    def interpretar(self, texto: str) -> Intencion: ...
