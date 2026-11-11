"""Síntesis de voz local con pyttsx3 (SAPI5 en Windows)."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def crear_motor_tts(velocidad: int | None = None):
    """Devuelve un motor pyttsx3 con voz en español si la hay, o None si no hay TTS."""
    try:
        import pyttsx3

        motor = pyttsx3.init()
    except Exception as e:  # sin drivers de voz, sin pyttsx3...
        log.warning("TTS no disponible (%s): solo se mostrará texto.", e)
        return None

    for voz in motor.getProperty("voices"):
        nombre = (voz.name or "").lower()
        idiomas = [str(i).lower() for i in (getattr(voz, "languages", None) or [])]
        if "spanish" in nombre or "español" in nombre or any(i.startswith("es") for i in idiomas):
            motor.setProperty("voice", voz.id)
            break
    else:
        log.warning("No hay ninguna voz en español instalada; se usa la voz por defecto.")

    if velocidad:
        motor.setProperty("rate", velocidad)
    return motor
