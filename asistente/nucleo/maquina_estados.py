"""Máquina de estados del diálogo. Reproduce el diagrama de flujo.

    CAPTURA ──(confianza baja / nada)──> CONFIRMAR_PRENDA ──> ESCUCHA
       └──────────(confianza alta)─────────────────────────> ESCUCHA
    ESCUCHA ──(contradicción, confianza media)──> ACLARAR ──> BUSCAR
    ESCUCHA ──(petición / matiz / otra)──> BUSCAR ──> MOSTRAR ──> ESCUCHA (bucle)
    ESCUCHA ──(acepta la sugerencia / salir)──> FIN

Cada estado es un método que hace su trabajo y devuelve el estado siguiente.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum, auto

from ..modelos import Accion, Fuente, Intencion, ObservacionVisual, Peticion
from ..presentacion.base import Salida
from ..recomendador.reglas import RecomendadorReglas
from ..vision.base import FuenteVision
from ..vocabulario import describir
from ..voz.base import EntradaVoz, Interprete
from . import fusion
from .contexto import Contexto
from .fusion import ResultadoFusion

log = logging.getLogger(__name__)

AYUDA = "Puedes pedirme, por ejemplo: «¿qué pantalón va con esto?», «algo más informal» u «otra»."


class Estado(Enum):
    CAPTURA = auto()
    CONFIRMAR_PRENDA = auto()
    ESCUCHA = auto()
    ACLARAR = auto()
    BUSCAR = auto()
    MOSTRAR = auto()
    FIN = auto()


@dataclass(frozen=True)
class ConfigNucleo:
    umbral_confirmacion: float = 0.6
    umbral_vision_gana: float = 0.85
    max_fallos_voz: int = 2
    intentos_captura: int = 5
    espera_captura_s: float = 0.5


def _leer_teclado(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return "salir"


def _desc(obs: ObservacionVisual) -> str:
    return describir(obs.tipo, obs.color)


class MaquinaEstados:
    def __init__(
        self,
        vision: FuenteVision,
        voz: EntradaVoz,
        interprete: Interprete,
        recomendador: RecomendadorReglas,
        salida: Salida,
        config: ConfigNucleo = ConfigNucleo(),
        teclado: Callable[[str], str] = _leer_teclado,
    ):
        self.vision = vision
        self.voz = voz
        self.interprete = interprete
        self.recomendador = recomendador
        self.salida = salida
        self.cfg = config
        self.teclado = teclado
        self.ctx = Contexto()
        self.estado = Estado.CAPTURA
        self._manejadores: dict[Estado, Callable[[], Estado]] = {
            Estado.CAPTURA: self._captura,
            Estado.CONFIRMAR_PRENDA: self._confirmar_prenda,
            Estado.ESCUCHA: self._escucha,
            Estado.ACLARAR: self._aclarar,
            Estado.BUSCAR: self._buscar,
            Estado.MOSTRAR: self._mostrar,
        }

    # ------------------------------------------------------------------ bucle
    def ejecutar(self) -> Contexto:
        self.vision.iniciar()
        try:
            self.salida.decir("Hola, soy tu asistente de armario. Ponte frente a la cámara.")
            while self.estado is not Estado.FIN:
                siguiente = self._manejadores[self.estado]()
                log.debug("%s -> %s", self.estado.name, siguiente.name)
                self.estado = siguiente
        finally:
            self.vision.detener()
        return self.ctx

    # ---------------------------------------------------------------- estados
    def _captura(self) -> Estado:
        obs = self._esperar_observacion()
        if obs is None:
            self.ctx.prenda_actual = None
            self.salida.decir(
                "No consigo ver ninguna prenda. Dime qué llevas puesto, "
                "por ejemplo: «llevo una camiseta blanca»."
            )
            return Estado.CONFIRMAR_PRENDA

        self.ctx.prenda_actual = obs
        self.salida.aviso(f"[visión] {_desc(obs)} · confianza {obs.confianza:.0%}")
        if fusion.necesita_confirmacion(obs, self.cfg.umbral_confirmacion):
            self.salida.decir(
                f"Creo que llevas {_desc(obs)}, pero no estoy seguro. ¿Es correcto?"
            )
            return Estado.CONFIRMAR_PRENDA

        self.salida.decir(f"Veo que llevas {_desc(obs)}. ¿Qué quieres que te busque?")
        return Estado.ESCUCHA

    def _confirmar_prenda(self) -> Estado:
        intencion = self._como_descripcion_puesta(self._escuchar_intencion())
        accion, obs = intencion.accion, self.ctx.prenda_actual

        if accion is Accion.SALIR:
            return self._despedirse()
        if accion is Accion.DESCONOCIDA:
            return Estado.CONFIRMAR_PRENDA
        if accion is Accion.CONFIRMAR and obs:
            self.ctx.prenda_actual = fusion.confirmar(obs)
            self.salida.decir(f"Perfecto. ¿Qué quieres que te busque? {AYUDA}")
            return Estado.ESCUCHA
        if intencion.prenda_puesta_tipo or intencion.prenda_puesta_color:
            nueva = fusion.aplicar_correccion(obs, intencion)
            if nueva:
                self.ctx.prenda_actual = nueva
                if accion is Accion.PEDIR:
                    self.ctx.actualizar_peticion(intencion)
                    self.salida.decir(f"Entendido, llevas {_desc(nueva)}.")
                    return Estado.BUSCAR
                self.salida.decir(f"Entendido, llevas {_desc(nueva)}. ¿Qué quieres que te busque?")
                return Estado.ESCUCHA
        if accion is Accion.NEGAR:
            self.salida.decir("Vale. Dime qué llevas puesto, por ejemplo: «llevo una sudadera gris».")
            return Estado.CONFIRMAR_PRENDA

        pregunta = f"¿Llevas {_desc(obs)}?" if obs else "¿Qué prenda llevas?"
        self.salida.decir(f"Antes necesito saber qué llevas puesto. {pregunta}")
        return Estado.CONFIRMAR_PRENDA

    def _escucha(self) -> Estado:
        intencion = self._escuchar_intencion()
        accion = intencion.accion
        hay_sugerencia = self.ctx.ultima_sugerencia is not None

        if accion is Accion.SALIR:
            return self._despedirse()
        if accion is Accion.DESCONOCIDA:
            return Estado.ESCUCHA
        if accion is Accion.CONFIRMAR and hay_sugerencia:
            p = self.ctx.ultima_sugerencia.prenda
            self.salida.decir(f"¡Genial! Te quedas con {describir(p.tipo, p.color)}. ¡Hasta luego!")
            return Estado.FIN
        if accion in (Accion.CONFIRMAR, Accion.NEGAR) and not hay_sugerencia:
            self.salida.decir(f"¿Qué quieres que te busque? {AYUDA}")
            return Estado.ESCUCHA
        if accion is Accion.CORREGIR:
            return self._resolver_referencia(
                intencion, Estado.BUSCAR if self.ctx.peticion_hecha else Estado.ESCUCHA
            )

        # PEDIR, MATIZAR, OTRA, o NEGAR tras una sugerencia
        if hay_sugerencia and accion in (Accion.OTRA, Accion.NEGAR, Accion.MATIZAR):
            self.ctx.rechazar_ultima()
        self.ctx.actualizar_peticion(intencion)
        if intencion.prenda_puesta_tipo or intencion.prenda_puesta_color:
            return self._resolver_referencia(intencion, Estado.BUSCAR)
        return Estado.BUSCAR

    def _aclarar(self) -> Estado:
        intencion = self._como_descripcion_puesta(self._escuchar_intencion())
        accion, obs = intencion.accion, self.ctx.prenda_actual
        pendiente = self.ctx.correccion_pendiente

        if accion is Accion.SALIR:
            return self._despedirse()
        if accion is Accion.DESCONOCIDA:
            return Estado.ACLARAR
        if accion is Accion.CONFIRMAR and pendiente:
            self.ctx.prenda_actual = fusion.aplicar_correccion(obs, pendiente) or obs
        elif accion is Accion.NEGAR and obs:
            self.ctx.prenda_actual = fusion.confirmar(obs)
        elif intencion.prenda_puesta_tipo or intencion.prenda_puesta_color:
            self.ctx.prenda_actual = fusion.aplicar_correccion(obs, intencion) or obs
        else:
            self.salida.decir("Perdona, antes necesito aclarar qué llevas. Responde «sí» o «no».")
            return Estado.ACLARAR

        self.ctx.correccion_pendiente = None
        self.ctx.insistencias = 0
        self.salida.decir(f"Vale, llevas {_desc(self.ctx.prenda_actual)}.")
        if self.ctx.peticion_hecha:
            return Estado.BUSCAR
        self.salida.decir("¿Qué quieres que te busque?")
        return Estado.ESCUCHA

    def _buscar(self) -> Estado:
        self._refrescar_prenda_actual()
        if self.ctx.prenda_actual is None:
            return Estado.CAPTURA

        sugerencia = self._recomendar()
        if sugerencia is None and self.ctx.rechazadas:
            self.salida.decir(
                "Ya te he enseñado todas las opciones que encajan. "
                "Vuelvo a empezar con las que habías descartado."
            )
            self.ctx.rechazadas.clear()
            sugerencia = self._recomendar()
        if sugerencia is None:
            self.salida.decir(f"No tengo nada en tu armario para esa petición. {AYUDA}")
            self.ctx.peticion = Peticion()
            return Estado.ESCUCHA

        self.ctx.ultima_sugerencia = sugerencia
        self.ctx.historial.append(sugerencia)
        return Estado.MOSTRAR

    def _mostrar(self) -> Estado:
        sug = self.ctx.ultima_sugerencia
        self.salida.mostrar_sugerencia(sug)
        frase = f"Te sugiero esta prenda: {describir(sug.prenda.tipo, sug.prenda.color)}. {sug.motivo}"
        if sug.restricciones_relajadas:
            frase += (
                " No tenía nada que cumpliera todo lo que pediste, así que no he tenido en cuenta "
                + " ni ".join(sug.restricciones_relajadas) + "."
            )
        self.salida.decir(frase + " ¿Te vale, quieres otra o algo distinto?")
        return Estado.ESCUCHA

    # ------------------------------------------------------------- auxiliares
    def _escuchar_intencion(self) -> Intencion:
        """Escucha al usuario aplicando la política de voz no entendida."""
        if self.ctx.fallos_voz >= self.cfg.max_fallos_voz:
            self.salida.decir("Sigo sin entenderte por voz. Escríbelo con el teclado, por favor.")
            texto = self.teclado("[teclado] tú > ")
            self.ctx.fallos_voz = 0
        else:
            texto = self.voz.escuchar()

        intencion = self.interprete.interpretar(texto or "")
        log.info("Usuario: %r -> %s", texto, intencion)
        if intencion.accion is Accion.DESCONOCIDA:
            self.ctx.fallos_voz += 1
            if self.ctx.fallos_voz < self.cfg.max_fallos_voz:
                self.salida.decir(f"No te he entendido, ¿puedes repetirlo? {AYUDA}")
        else:
            self.ctx.fallos_voz = 0
        return intencion

    @staticmethod
    def _como_descripcion_puesta(intencion: Intencion) -> Intencion:
        """Cuando preguntamos qué lleva, «una camisa blanca» describe lo puesto, no una petición."""
        if (
            intencion.accion in (Accion.PEDIR, Accion.MATIZAR)
            and not (intencion.prenda_puesta_tipo or intencion.prenda_puesta_color)
            and (intencion.tipo or intencion.color)
        ):
            return replace(
                intencion,
                accion=Accion.CORREGIR,
                prenda_puesta_tipo=intencion.tipo,
                prenda_puesta_color=intencion.color,
            )
        return intencion

    def _resolver_referencia(self, intencion: Intencion, siguiente: Estado) -> Estado:
        """Aplica la política de fusión cuando el usuario describe lo que lleva puesto."""
        obs = self.ctx.prenda_actual
        resultado = fusion.evaluar_correccion(
            obs, intencion, self.cfg.umbral_vision_gana, self.ctx.insistencias
        )
        log.info("Fusión: %s", resultado.name)

        if resultado in (ResultadoFusion.SIN_CONFLICTO, ResultadoFusion.ACEPTAR_USUARIO):
            nueva = fusion.aplicar_correccion(obs, intencion)
            if nueva is None:
                self.salida.decir("¿Qué prenda llevas puesta? Por ejemplo: «llevo una sudadera gris».")
                return Estado.CONFIRMAR_PRENDA
            if obs is None or (nueva.tipo, nueva.color) != (obs.tipo, obs.color):
                self.salida.decir(f"Entendido, llevas {_desc(nueva)}.")
            self.ctx.prenda_actual = nueva
            self.ctx.insistencias = 0
            if siguiente is Estado.ESCUCHA:
                self.salida.decir("¿Qué quieres que te busque?")
            return siguiente

        if resultado is ResultadoFusion.GANA_VISION:
            self.ctx.insistencias += 1
            self.salida.decir(
                f"La cámara ve con bastante claridad {_desc(obs)}, así que sigo con eso. "
                "Si de verdad llevas otra cosa, dímelo otra vez."
            )
            return siguiente

        # PEDIR_ACLARACION
        self.ctx.correccion_pendiente = intencion
        dicho = fusion.aplicar_correccion(obs, intencion)
        self.salida.decir(
            f"Dices que llevas {_desc(dicho)}, pero yo veo {_desc(obs)}. "
            f"¿Llevas {_desc(dicho)}? Responde «sí» o «no»."
        )
        return Estado.ACLARAR

    def _esperar_observacion(self) -> ObservacionVisual | None:
        for intento in range(self.cfg.intentos_captura):
            obs = self.vision.observacion_actual()
            if obs is not None:
                return obs
            if intento == 0:
                self.salida.aviso("Buscando tu prenda en la cámara...")
            time.sleep(self.cfg.espera_captura_s)
        return None

    def _refrescar_prenda_actual(self) -> None:
        """La cámara sigue funcionando: si cambia la prenda, usamos la nueva."""
        actual = self.ctx.prenda_actual
        if actual and actual.fuente is Fuente.USUARIO:
            return
        obs = self.vision.observacion_actual()
        if obs and obs.confianza >= self.cfg.umbral_confirmacion:
            self.ctx.prenda_actual = obs

    def _recomendar(self):
        return self.recomendador.recomendar(
            self.ctx.prenda_actual, self.ctx.peticion, self.ctx.rechazadas
        )

    def _despedirse(self) -> Estado:
        self.salida.decir("¡Hasta luego!")
        return Estado.FIN
