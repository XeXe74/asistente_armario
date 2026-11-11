"""Salida por consola + voz. Provisional hasta tener la interfaz gráfica.

TODO: ventana (OpenCV o Tkinter) con la imagen de la cámara, la prenda
detectada con su confianza y la imagen de la prenda sugerida.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..modelos import Sugerencia
from ..vocabulario import NOMBRES_FORMALIDAD, describir

log = logging.getLogger(__name__)


class SalidaConsola:
    def __init__(self, motor_tts=None, carpeta_imagenes: Path | None = None):
        self._tts = motor_tts
        self._carpeta_imagenes = carpeta_imagenes

    def decir(self, texto: str) -> None:
        print(f"\nAsistente: {texto}", flush=True)
        if self._tts is not None:
            try:
                self._tts.say(texto)
                self._tts.runAndWait()
            except Exception as e:
                log.warning("Fallo del TTS (%s); se desactiva la voz.", e)
                self._tts = None

    def aviso(self, texto: str) -> None:
        print(f"  {texto}", flush=True)

    def mostrar_sugerencia(self, sugerencia: Sugerencia) -> None:
        p = sugerencia.prenda
        imagen = "(sin imagen)"
        if p.imagen and self._carpeta_imagenes is not None:
            ruta = self._carpeta_imagenes / p.imagen
            imagen = str(ruta) if ruta.is_file() else f"{p.imagen} (no encontrada)"
        print(
            "\n  +--------------------------- SUGERENCIA ---------------------------\n"
            f"  | {describir(p.tipo, p.color)}  [{p.id}]\n"
            f"  | estilo: {NOMBRES_FORMALIDAD[p.formalidad]}\n"
            f"  | imagen: {imagen}\n"
            "  +-------------------------------------------------------------------",
            flush=True,
        )
