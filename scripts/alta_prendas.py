"""Alta de prendas en el catálogo (PENDIENTE).

Uso previsto:
    python scripts/alta_prendas.py ruta/a/fotos/ --salida data/catalogo.json

Plan de implementación:
  1. Para cada foto de prenda: los MISMOS modelos que la visión en vivo
     (YOLO + CLIP zero-shot + k-means) para que las etiquetas coincidan.
  2. Formalidad: provisionalmente una regla por tipo; opcionalmente un
     clasificador lineal sobre embeddings CLIP (Fashion Product Images).
  3. Copiar la foto a data/imagenes/ y escribir/actualizar el JSON, que
     después se puede corregir a mano.
"""

import sys


def main() -> int:
    print("Pendiente de implementar. De momento edita data/catalogo.json a mano.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
