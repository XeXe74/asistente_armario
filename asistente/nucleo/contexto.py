"""Estado de la conversación: lo que sabemos del usuario en esta sesión."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..modelos import Accion, Intencion, ObservacionVisual, Peticion, Sugerencia
from ..vocabulario import TIPOS

FORMALIDAD_POR_DEFECTO = 2


@dataclass
class Contexto:
    prenda_actual: ObservacionVisual | None = None
    peticion: Peticion = field(default_factory=Peticion)
    peticion_hecha: bool = False
    # Historial para adaptar las respuestas: no repetir lo que ya rechazó
    rechazadas: set[str] = field(default_factory=set)
    ultima_sugerencia: Sugerencia | None = None
    historial: list[Sugerencia] = field(default_factory=list)
    # Política de fallos y conflictos
    fallos_voz: int = 0
    insistencias: int = 0
    correccion_pendiente: Intencion | None = None

    def rechazar_ultima(self) -> None:
        if self.ultima_sugerencia:
            self.rechazadas.add(self.ultima_sugerencia.prenda.id)

    def actualizar_peticion(self, intencion: Intencion) -> None:
        """Una petición nueva reinicia las restricciones; un matiz las modifica."""
        if intencion.accion is Accion.PEDIR:
            self.peticion = Peticion()
        p = self.peticion

        if intencion.tipo:
            p.tipo = intencion.tipo
            p.zona = TIPOS.get(intencion.tipo, intencion.zona)
        elif intencion.zona:
            if p.zona != intencion.zona:
                p.tipo = None
            p.zona = intencion.zona

        if intencion.color:
            p.color = intencion.color
        if intencion.formalidad:
            p.formalidad = intencion.formalidad
        if intencion.ajuste_formalidad:
            base = p.formalidad or (
                self.ultima_sugerencia.prenda.formalidad
                if self.ultima_sugerencia else FORMALIDAD_POR_DEFECTO
            )
            p.formalidad = min(3, max(1, base + intencion.ajuste_formalidad))

        self.peticion_hecha = True
