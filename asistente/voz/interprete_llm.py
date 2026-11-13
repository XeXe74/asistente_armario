"""Intérprete con LLM local vía Ollama (PENDIENTE).

Plan de implementación:
  1. Las órdenes cortas ("sí", "no", "otra", "salir") se resuelven SIEMPRE con
     `InterpreteReglas`, sin llamar al LLM.
  2. El resto se envía a Ollama pidiendo un JSON con estructura fija
     (accion, zona, tipo, color, formalidad, ajuste_formalidad,
     prenda_puesta_tipo, prenda_puesta_color) usando `format=<json schema>`.
  3. Validar la respuesta contra `vocabulario` (tipos y colores conocidos).
     El LLM nunca elige prendas: solo extrae restricciones.
  4. Si Ollama no responde en `voz.llm.timeout_s` o el JSON no es válido,
     volver a `InterpreteReglas` (respaldo).

Debe cumplir la interfaz `Interprete` (interpretar).
"""

from __future__ import annotations

from ..modelos import Intencion


class InterpreteLLM:
    def __init__(self, **_config):
        raise NotImplementedError(
            "El intérprete con LLM todavía no está implementado. "
            "Usa voz.interprete: reglas en config.yaml."
        )

    def interpretar(self, texto: str) -> Intencion: ...
