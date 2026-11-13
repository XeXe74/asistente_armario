"""Punto de entrada del asistente de armario.

    python main.py                  # usa config.yaml
    python main.py --sin-tts        # sin voz sintetizada
    python main.py --config otra.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from asistente.catalogo import cargar_catalogo
from asistente.config import cargar_config, ruta_proyecto
from asistente.nucleo import ConfigNucleo, MaquinaEstados
from asistente.presentacion.consola import SalidaConsola
from asistente.presentacion.tts import crear_motor_tts
from asistente.recomendador import RecomendadorReglas
from asistente.voz.interprete_reglas import InterpreteReglas


def crear_vision(cfg: dict[str, Any]):
    modo = cfg.get("modo", "simulada")
    if modo == "simulada":
        from asistente.vision.simulada import VisionSimulada

        return VisionSimulada(**cfg["simulada"])
    if modo == "yolo_clip":
        from asistente.vision.yolo_clip import VisionYoloClip

        return VisionYoloClip(**cfg)
    raise ValueError(f"vision.modo desconocido: {modo}")


def crear_voz(cfg: dict[str, Any]):
    modo = cfg.get("modo", "teclado")
    if modo == "teclado":
        from asistente.voz.simulada import VozTeclado

        return VozTeclado()
    if modo == "whisper":
        from asistente.voz.whisper import VozWhisper

        return VozWhisper(**cfg)
    raise ValueError(f"voz.modo desconocido: {modo}")


def crear_interprete(cfg: dict[str, Any]):
    modo = cfg.get("interprete", "reglas")
    if modo == "reglas":
        return InterpreteReglas()
    if modo == "llm":
        from asistente.voz.interprete_llm import InterpreteLLM

        return InterpreteLLM(**cfg)
    raise ValueError(f"voz.interprete desconocido: {modo}")


def construir(config: dict[str, Any], sin_tts: bool = False) -> MaquinaEstados:
    cfg_catalogo = config.get("catalogo", {})
    cfg_vision = config.get("vision", {})
    cfg_voz = config.get("voz", {})
    cfg_fusion = config.get("fusion", {})
    cfg_salida = config.get("salida", {})

    catalogo = cargar_catalogo(ruta_proyecto(cfg_catalogo.get("ruta", "data/catalogo.json")))
    motor_tts = None
    if cfg_salida.get("tts", True) and not sin_tts:
        motor_tts = crear_motor_tts(cfg_salida.get("velocidad_tts"))

    return MaquinaEstados(
        vision=crear_vision(cfg_vision),
        voz=crear_voz(cfg_voz),
        interprete=crear_interprete(cfg_voz),
        recomendador=RecomendadorReglas(catalogo),
        salida=SalidaConsola(
            motor_tts=motor_tts,
            carpeta_imagenes=ruta_proyecto(cfg_catalogo.get("carpeta_imagenes", "data/imagenes")),
        ),
        config=ConfigNucleo(
            umbral_confirmacion=cfg_fusion.get("umbral_confirmacion", 0.6),
            umbral_vision_gana=cfg_fusion.get("umbral_vision_gana", 0.85),
            max_fallos_voz=cfg_voz.get("max_fallos", 2),
            intentos_captura=cfg_vision.get("intentos_captura", 5),
            espera_captura_s=cfg_vision.get("espera_captura_s", 0.5),
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asistente de armario multimodal")
    parser.add_argument("--config", help="ruta a un config.yaml alternativo")
    parser.add_argument("--sin-tts", action="store_true", help="no leer las respuestas en voz alta")
    args = parser.parse_args(argv)

    # Que un carácter no representable en la consola no tumbe el programa
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    try:
        config = cargar_config(args.config)
        logging.basicConfig(
            level=config.get("log_nivel", "WARNING"),
            format="%(levelname)s %(name)s: %(message)s",
        )
        maquina = construir(config, sin_tts=args.sin_tts)
        maquina.ejecutar()
    except KeyboardInterrupt:
        print("\nHasta luego.")
    except (FileNotFoundError, ValueError, NotImplementedError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
