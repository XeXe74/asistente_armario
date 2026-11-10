"""Intérprete por reglas (palabras clave).

Resuelve las órdenes cortas y sirve de respaldo cuando el LLM falla o tarda.
"""

from __future__ import annotations

from ..modelos import Accion, Intencion, Zona
from ..vocabulario import (
    SINONIMOS_COLOR,
    SINONIMOS_TIPO,
    TIPOS,
    ZONAS_GENERICAS,
    buscar_frase,
    contiene,
    normalizar,
)

SALIR = ("salir", "adios", "terminar", "termina", "hasta luego", "apagar")
OTRA = ("otra", "otro", "siguiente", "cambia", "cambiala", "diferente", "distinta", "distinto")
PEDIR = (
    "combina", "combinan", "va con", "pega", "pegan", "quiero", "dame", "busca", "buscame",
    "recomienda", "recomiendame", "sugiere", "sugiereme", "me pongo", "ponerme", "necesito",
)
CONFIRMAR = (
    "si", "vale", "perfecto", "genial", "me gusta", "correcto", "eso es", "me lo quedo",
    "me la quedo", "de acuerdo", "ok", "okay", "claro",
)
NEGAR = ("no", "incorrecto", "tampoco", "no me gusta", "nop")
# Marcadores de que el usuario describe lo que lleva puesto
CORRECCION = (
    "llevo", "tengo puesto", "tengo puesta", "tengo puestos", "tengo puestas",
    "es un", "es una", "son unos", "son unas",
)
MAS_INFORMAL = ("mas informal", "menos formal", "mas casual", "mas comodo", "mas deportivo")
MAS_FORMAL = ("mas formal", "menos informal", "mas elegante", "mas arreglado", "mas de vestir")
INFORMAL = ("informal", "casual", "comodo", "deportivo")
FORMAL = ("formal", "elegante", "arreglado", "de vestir")


def _posicion_primera(texto: str, frases: tuple[str, ...]) -> int:
    relleno = f" {texto} "
    posiciones = [relleno.find(f" {f} ") for f in frases if f" {f} " in relleno]
    return min(posiciones) if posiciones else -1


def _segmento_correccion(texto: str) -> str | None:
    """Texto que sigue al último marcador de corrección ("llevo ...", "es una ...")."""
    relleno = f" {texto} "
    mejor = -1
    largo = 0
    for marcador in CORRECCION:
        pos = relleno.rfind(f" {marcador} ")
        if pos > mejor:
            mejor, largo = pos, len(marcador) + 2
    return relleno[mejor + largo:].strip() if mejor >= 0 else None


class InterpreteReglas:
    def interpretar(self, texto: str) -> Intencion:
        t = normalizar(texto or "")
        if not t:
            return Intencion(Accion.DESCONOCIDA, texto)

        if contiene(t, SALIR):
            return Intencion(Accion.SALIR, texto)

        # "llevo una camisa blanca" / "no es una camiseta, es una sudadera"
        segmento = _segmento_correccion(t)
        if segmento is not None:
            tipo = buscar_frase(segmento, SINONIMOS_TIPO)
            color = buscar_frase(segmento, SINONIMOS_COLOR)
            if tipo or color:
                return Intencion(
                    Accion.CORREGIR, texto, prenda_puesta_tipo=tipo, prenda_puesta_color=color
                )

        # "¿qué pantalón va con esta camisa roja?": lo que va tras "con" describe
        # lo que lleva puesto (referencia), no lo que pide.
        pedido, _, referencia = f" {t} ".partition(" con ")
        pedido, referencia = pedido.strip(), referencia.strip()

        tipo = buscar_frase(pedido, SINONIMOS_TIPO)
        zona: Zona | None = TIPOS[tipo] if tipo else buscar_frase(pedido, ZONAS_GENERICAS)
        color = buscar_frase(pedido, SINONIMOS_COLOR)
        ajuste = -1 if contiene(t, MAS_INFORMAL) else 1 if contiene(t, MAS_FORMAL) else 0
        formalidad = None
        if not ajuste:
            formalidad = 1 if contiene(t, INFORMAL) else 3 if contiene(t, FORMAL) else None
        hay_restricciones = any((zona, color, formalidad, ajuste))
        ref_tipo = buscar_frase(referencia, SINONIMOS_TIPO) if referencia else None
        ref_color = buscar_frase(referencia, SINONIMOS_COLOR) if referencia else None

        def con(accion: Accion) -> Intencion:
            return Intencion(
                accion, texto, zona=zona, tipo=tipo, color=color,
                formalidad=formalidad, ajuste_formalidad=ajuste,
                prenda_puesta_tipo=ref_tipo, prenda_puesta_color=ref_color,
            )

        if contiene(t, OTRA):
            return con(Accion.OTRA)
        if zona or contiene(t, PEDIR):
            return con(Accion.PEDIR)
        if hay_restricciones:
            return con(Accion.MATIZAR)

        pos_no = _posicion_primera(t, NEGAR)
        pos_si = _posicion_primera(t, CONFIRMAR)
        if pos_no >= 0 and (pos_si < 0 or pos_no <= pos_si):
            return Intencion(Accion.NEGAR, texto)
        if pos_si >= 0:
            return Intencion(Accion.CONFIRMAR, texto)

        return Intencion(Accion.DESCONOCIDA, texto)
