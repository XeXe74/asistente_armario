"""Voz real (PENDIENTE): push-to-talk + faster-whisper en local.


Debe cumplir la interfaz `EntradaVoz` (escuchar).
"""

from __future__ import annotations


class VozWhisper:
    def __init__(self, **_config):
        raise NotImplementedError(
            "La voz real todavía no está implementada. Usa voz.modo: teclado en config.yaml."
        )

    def escuchar(self) -> str | None: ...
