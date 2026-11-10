"""Voz simulada: el usuario escribe lo que diría en voz alta."""

from __future__ import annotations


class VozTeclado:
    def __init__(self, prompt: str = "[voz] tú > "):
        self._prompt = prompt

    def escuchar(self) -> str | None:
        try:
            texto = input(self._prompt).strip()
        except EOFError:
            return "salir"
        return texto or None
