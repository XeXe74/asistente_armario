from __future__ import annotations

from typing import Protocol

from ..modelos import Sugerencia


class Salida(Protocol):
    def decir(self, texto: str) -> None:
        """Mensaje principal al usuario: se muestra y, si hay TTS, se lee en voz alta."""
        ...

    def aviso(self, texto: str) -> None:
        """Información secundaria (estado, confianza): solo se muestra."""
        ...

    def mostrar_sugerencia(self, sugerencia: Sugerencia) -> None: ...
