import unittest

from asistente.modelos import ObservacionVisual, Peticion, Prenda, Zona
from asistente.recomendador.reglas import RecomendadorReglas, armonia

CATALOGO = [
    Prenda("v", Zona.INFERIOR, "vaquero", "azul", 2, ""),
    Prenda("c", Zona.INFERIOR, "chino", "beige", 2, ""),
    Prenda("r", Zona.INFERIOR, "falda", "rojo", 2, ""),
    Prenda("t", Zona.INFERIOR, "pantalon de traje", "negro", 3, ""),
    Prenda("s", Zona.SUPERIOR, "camiseta", "blanco", 1, ""),
]
CAMISETA_ROJA = ObservacionVisual(Zona.SUPERIOR, "camiseta", "rojo", 0.9)


class TestRecomendador(unittest.TestCase):
    def setUp(self):
        self.r = RecomendadorReglas(CATALOGO)

    def test_zona_complementaria_por_defecto(self):
        s = self.r.recomendar(CAMISETA_ROJA, Peticion())
        self.assertIs(s.prenda.zona, Zona.INFERIOR)

    def test_prefiere_combinacion_buena(self):
        # rojo + azul está en COMBINACIONES: puntúa más que un neutro
        s = self.r.recomendar(ObservacionVisual(Zona.SUPERIOR, "camisa", "rojo", 0.9), Peticion())
        self.assertIn(s.prenda.id, {"v"})

    def test_no_sugiere_mismo_color_no_neutro(self):
        self.assertEqual(armonia("rojo", CATALOGO[2])[0], 0)

    def test_excluye_rechazadas(self):
        primera = self.r.recomendar(CAMISETA_ROJA, Peticion())
        segunda = self.r.recomendar(CAMISETA_ROJA, Peticion(), excluir={primera.prenda.id})
        self.assertNotEqual(primera.prenda.id, segunda.prenda.id)

    def test_relaja_y_lo_dice(self):
        s = self.r.recomendar(CAMISETA_ROJA, Peticion(zona=Zona.INFERIOR, color="verde"))
        self.assertIn("el color", s.restricciones_relajadas)

    def test_sin_candidatas(self):
        todas = {p.id for p in CATALOGO}
        self.assertIsNone(self.r.recomendar(CAMISETA_ROJA, Peticion(), excluir=todas))

    def test_motivo_explica(self):
        s = self.r.recomendar(CAMISETA_ROJA, Peticion(formalidad=3))
        self.assertEqual(s.prenda.id, "t")
        self.assertIn("formal", s.motivo)


if __name__ == "__main__":
    unittest.main()
