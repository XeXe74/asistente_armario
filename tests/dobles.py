"""Dobles de prueba: voz con guion y salida que registra lo que se dice."""

from __future__ import annotations

from asistente.catalogo import cargar_catalogo
from asistente.config import ruta_proyecto
from asistente.nucleo import ConfigNucleo, MaquinaEstados
from asistente.recomendador import RecomendadorReglas
from asistente.vision.simulada import VisionSimulada
from asistente.voz.interprete_reglas import InterpreteReglas


class VozGuion:
    """Devuelve las frases del guion en orden; al acabarse, dice «salir»."""

    def __init__(self, frases: list[str | None]):
        self._frases = list(frases)

    def escuchar(self) -> str | None:
        return self._frases.pop(0) if self._frases else "salir"


class SalidaRegistro:
    def __init__(self):
        self.dichos: list[str] = []
        self.sugerencias = []

    def decir(self, texto: str) -> None:
        self.dichos.append(texto)

    def aviso(self, texto: str) -> None:
        pass

    def mostrar_sugerencia(self, sugerencia) -> None:
        self.sugerencias.append(sugerencia)

    def todo(self) -> str:
        return "\n".join(self.dichos)


def crear_maquina(
    frases: list[str | None],
    tipo: str | None = "camiseta",
    color: str | None = "rojo",
    confianza: float = 0.9,
    teclado: list[str] | None = None,
) -> tuple[MaquinaEstados, SalidaRegistro]:
    salida = SalidaRegistro()
    pendientes_teclado = list(teclado or [])
    maquina = MaquinaEstados(
        vision=VisionSimulada("superior", tipo, color, confianza),
        voz=VozGuion(frases),
        interprete=InterpreteReglas(),
        recomendador=RecomendadorReglas(cargar_catalogo(ruta_proyecto("data/catalogo.json"))),
        salida=salida,
        config=ConfigNucleo(intentos_captura=1, espera_captura_s=0),
        teclado=lambda _prompt: pendientes_teclado.pop(0) if pendientes_teclado else "salir",
    )
    return maquina, salida
