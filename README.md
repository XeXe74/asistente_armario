# Asistente de armario

Asistente conversacional que combina **visión** y **voz**: la cámara reconoce
la prenda que llevas puesta (tipo y color), le pides por voz algo que combine
("¿qué pantalón va con esto?", "algo más informal", "otra") y el sistema te
sugiere una prenda de tu armario catalogado explicando el motivo.

Todo se ejecuta en local: ninguna imagen ni audio sale del ordenador y los
fotogramas de la cámara no se guardan.

> **Estado actual: esqueleto ejecutable.** El bucle de interacción completo
> funciona con visión y voz **simuladas** (ver [Estado de los módulos](#estado-de-los-módulos)).

## Requisitos

- Windows 10/11 (probado en Windows 11).
- Python 3.14.
- Para la versión final: webcam, micrófono y [Ollama](https://ollama.com) instalado.

## Instalación

```powershell
git clone https://github.com/XeXe74/asistente_armario.git
cd asistente_armario
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecución

```powershell
python main.py              # con voz sintetizada
python main.py --sin-tts    # solo texto
```

Con la voz simulada, escribe en la consola lo que dirías en voz alta. Ejemplo:

```
Asistente: Veo que llevas camiseta de color rojo. ¿Qué quieres que te busque?
[voz] tú > ¿qué pantalón va con esto?
Asistente: Te sugiero esta prenda: vaquero de color azul. Va con tu camiseta de color rojo: un vaquero va con casi todo. Su estilo es intermedio. ¿Te vale, quieres otra o algo distinto?
[voz] tú > algo más informal
...
[voz] tú > sí, me lo quedo
```

Frases que entiende: peticiones ("¿qué pantalón va con esto?", "quiero una
camisa blanca"), matices ("más informal", "más elegante", "en negro"),
"otra", "sí"/"no", correcciones ("llevo una sudadera gris") y "salir".

## Pruebas

```powershell
python -m unittest -v
```

Recorren el escenario de la demo y cada rama de la política de fusión
(confianza baja, contradicción voz-visión, voz no entendida, sin prendas
compatibles) sin cámara ni micrófono.

## Configuración

Todo lo ajustable está en [`config.yaml`](config.yaml), fuera del código:
modo de cada módulo (simulado o real), umbrales de confianza, cámara, TTS y
rutas del catálogo. Para probar las ramas alternativas con la visión
simulada, cambia `vision.simulada.confianza` (p. ej. `0.4` para que pida
confirmación) o pon `tipo: null` para que no detecte nada.

## Arquitectura

Cuatro capas que solo se comunican mediante las estructuras de
[`asistente/modelos.py`](asistente/modelos.py) (`ObservacionVisual`,
`Intencion`, `Peticion`, `Prenda`, `Sugerencia`):

```
percepción  ──>  diálogo y fusión  ──>  recomendación  ──>  presentación
(visión, voz)    (máquina de estados)    (reglas + CLIP)     (texto, TTS, imagen)
```

```
asistente/
  modelos.py            contratos de datos compartidos
  vocabulario.py        tipos y colores comunes a todos los módulos
  catalogo.py           carga y validación del catálogo JSON
  config.py             lectura de config.yaml
  vision/               base.py (interfaz) · simulada.py · yolo_clip.py
  voz/                  base.py (interfaces) · simulada.py · whisper.py
                        interprete_reglas.py · interprete_llm.py
  nucleo/               maquina_estados.py (diagrama de flujo)
                        fusion.py (política visión-voz) · contexto.py
  recomendador/         reglas.py (zona, armonía de color, formalidad)
  presentacion/         consola.py · tts.py
data/catalogo.json      armario de ejemplo
scripts/alta_prendas.py catalogación de fotos (pendiente)
tests/                  pruebas unitarias y de flujo
main.py                 punto de entrada
```

### Política de fusión

| Situación | Qué hace el sistema |
|---|---|
| Visión con confianza < `umbral_confirmacion` | Pregunta "¿Llevas X?" y acepta sí / no / corrección por voz |
| No se detecta prenda | Pide al usuario que diga qué lleva |
| La voz contradice a la visión y la confianza visual ≥ `umbral_vision_gana` | Gana la visión y lo avisa; si el usuario insiste, se le hace caso |
| La voz contradice a la visión con confianza intermedia | Pide aclaración |
| Voz no entendida | Pide repetir; tras `max_fallos` intentos ofrece el teclado |
| Ninguna prenda cumple todo | Relaja restricciones (estilo → color → tipo → armonía) y lo dice |

## Estado de los módulos

| Módulo | Estado |
|---|---|
| Máquina de estados y fusión | Implementado |
| Recomendador por reglas | Implementado (falta el ranking por CLIP del matiz) |
| Intérprete por reglas | Implementado |
| TTS (pyttsx3) | Implementado |
| Visión | Simulada (`vision/yolo_clip.py` pendiente) |
| Voz (ASR) | Simulada con teclado (`voz/whisper.py` pendiente) |
| Intérprete LLM (Ollama) | Pendiente |
| Interfaz gráfica con imágenes | Pendiente (ahora, consola) |
| Alta de prendas desde fotos |  Pendiente (ahora, JSON a mano) |
