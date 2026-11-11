"""Recomendador híbrido: compatibilidad por reglas (explicable).

Reglas: zona complementaria, armonía de color y formalidad. Si ninguna prenda
cumple todas las restricciones se relajan de una en una, en el orden de
`ORDEN_RELAJACION`, y se informa de cuáles se han relajado.

CLIP se usará solo para puntuar el matiz pedido por voz frente a la imagen de
cada prenda (`_puntuar_matiz`), nunca para decidir compatibilidad.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..modelos import ObservacionVisual, Peticion, Prenda, Sugerencia
from ..vocabulario import NOMBRES_FORMALIDAD, describir, visible

NEUTROS = {"negro", "blanco", "gris", "beige", "marino"}

# Pares de colores no neutros que combinan bien
COMBINACIONES = {
    frozenset(par) for par in [
        ("azul", "beige"), ("azul", "marron"), ("azul", "rojo"), ("azul", "rosa"),
        ("azul", "amarillo"), ("azul", "naranja"), ("verde", "beige"), ("verde", "marron"),
        ("rosa", "gris"), ("morado", "gris"), ("rojo", "marron"),
    ]
}

ORDEN_RELAJACION = ("formalidad", "color", "tipo", "armonia")
NOMBRE_RESTRICCION = {
    "formalidad": "el estilo",
    "color": "el color",
    "tipo": "el tipo de prenda",
    "armonia": "la combinación de colores",
}


def armonia(color_puesta: str | None, prenda: Prenda) -> tuple[int, str]:
    """Calidad de la combinación (0 = no combina, 1 = correcta, 2 = buena) y explicación."""
    c1, c2 = color_puesta, prenda.color
    if c1 is None:
        return 1, f"el {visible(c2)} es una opción segura"
    if prenda.tipo == "vaquero":
        return 1, "un vaquero va con casi todo"
    if frozenset((c1, c2)) in COMBINACIONES:
        return 2, f"el {visible(c1)} y el {visible(c2)} combinan bien"
    if c1 in NEUTROS and c2 in NEUTROS:
        return 1, f"el {visible(c1)} y el {visible(c2)} son neutros y combinan sin problema"
    if c2 in NEUTROS:
        return 1, f"el {visible(c2)} es neutro y va bien con el {visible(c1)}"
    if c1 in NEUTROS:
        return 1, f"el {visible(c1)} es neutro y admite el {visible(c2)}"
    return 0, f"el {visible(c1)} y el {visible(c2)} no combinan demasiado"


class RecomendadorReglas:
    def __init__(self, catalogo: Iterable[Prenda]):
        self._catalogo = list(catalogo)

    def recomendar(
        self,
        puesta: ObservacionVisual,
        peticion: Peticion,
        excluir: Iterable[str] = (),
    ) -> Sugerencia | None:
        excluidas = set(excluir)
        zona = peticion.zona or puesta.zona.complementaria()
        candidatas = [p for p in self._catalogo if p.zona == zona and p.id not in excluidas]
        if not candidatas:
            return None

        relajadas: list[str] = []
        while True:
            activas = self._restricciones_activas(peticion, relajadas)
            validas = [p for p in candidatas if self._cumple(p, puesta, peticion, activas)]
            if validas:
                # max() se queda con la primera en caso de empate: orden del catálogo
                mejor = max(validas, key=lambda p: self._puntuar(p, puesta, peticion))
                return Sugerencia(
                    prenda=mejor,
                    motivo=self._motivo(mejor, puesta, peticion, activas),
                    restricciones_relajadas=tuple(NOMBRE_RESTRICCION[r] for r in relajadas),
                )
            siguiente = next((r for r in ORDEN_RELAJACION if r in activas), None)
            if siguiente is None:
                return None
            relajadas.append(siguiente)

    @staticmethod
    def _restricciones_activas(peticion: Peticion, relajadas: list[str]) -> set[str]:
        activas = {
            nombre for nombre, valor in (
                ("tipo", peticion.tipo),
                ("color", peticion.color),
                ("formalidad", peticion.formalidad),
            )
            if valor is not None and nombre not in relajadas
        }
        # Si el usuario pide un color explícito, manda su elección sobre la armonía
        if "color" not in activas and "armonia" not in relajadas:
            activas.add("armonia")
        return activas

    @staticmethod
    def _cumple(p: Prenda, puesta: ObservacionVisual, peticion: Peticion, activas: set[str]) -> bool:
        if "tipo" in activas and p.tipo != peticion.tipo:
            return False
        if "color" in activas and p.color != peticion.color:
            return False
        if "formalidad" in activas and p.formalidad != peticion.formalidad:
            return False
        if "armonia" in activas and armonia(puesta.color, p)[0] == 0:
            return False
        return True

    def _puntuar(self, p: Prenda, puesta: ObservacionVisual, peticion: Peticion) -> tuple:
        cercania = -abs(p.formalidad - peticion.formalidad) if peticion.formalidad else 0
        return (armonia(puesta.color, p)[0], cercania, self._puntuar_matiz(p, peticion))

    @staticmethod
    def _puntuar_matiz(p: Prenda, peticion: Peticion) -> float:
        # TODO: similitud CLIP entre el texto del matiz pedido y la imagen de la prenda.
        return 0.0

    @staticmethod
    def _motivo(p: Prenda, puesta: ObservacionVisual, peticion: Peticion, activas: set[str]) -> str:
        if "color" in activas:
            color = f"es de color {visible(p.color)}, como pediste"
        else:
            color = armonia(puesta.color, p)[1]
        estilo = NOMBRES_FORMALIDAD[p.formalidad]
        if "formalidad" in activas:
            estilo = f"Tiene el estilo {estilo} que buscabas."
        else:
            estilo = f"Su estilo es {estilo}."
        return f"Va con tu {describir(puesta.tipo, puesta.color)}: {color}. {estilo}"
