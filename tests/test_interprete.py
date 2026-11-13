import unittest

from asistente.modelos import Accion, Zona
from asistente.voz.interprete_reglas import InterpreteReglas


class TestInterpreteReglas(unittest.TestCase):
    def setUp(self):
        self.i = InterpreteReglas()

    def test_ordenes_cortas(self):
        casos = {
            "sí": Accion.CONFIRMAR,
            "Vale, me lo quedo": Accion.CONFIRMAR,
            "no": Accion.NEGAR,
            "no me gusta": Accion.NEGAR,
            "otra": Accion.OTRA,
            "dame otra": Accion.OTRA,
            "adiós": Accion.SALIR,
            "": Accion.DESCONOCIDA,
            "blablabla": Accion.DESCONOCIDA,
        }
        for texto, esperada in casos.items():
            with self.subTest(texto=texto):
                self.assertIs(self.i.interpretar(texto).accion, esperada)

    def test_peticion_con_deixis(self):
        r = self.i.interpretar("¿Qué pantalón va con esto?")
        self.assertIs(r.accion, Accion.PEDIR)
        self.assertIs(r.zona, Zona.INFERIOR)
        self.assertIsNone(r.prenda_puesta_tipo)

    def test_referencia_a_lo_puesto_tras_con(self):
        r = self.i.interpretar("¿qué pantalón va con mi camisa roja?")
        self.assertIs(r.zona, Zona.INFERIOR)
        self.assertIsNone(r.color)
        self.assertEqual((r.prenda_puesta_tipo, r.prenda_puesta_color), ("camisa", "rojo"))

    def test_tipo_y_color(self):
        r = self.i.interpretar("quiero unos vaqueros azul marino")
        self.assertEqual((r.tipo, r.color, r.zona), ("vaquero", "marino", Zona.INFERIOR))

    def test_matices_de_formalidad(self):
        self.assertEqual(self.i.interpretar("algo más informal").ajuste_formalidad, -1)
        self.assertEqual(self.i.interpretar("menos informal").ajuste_formalidad, 1)
        r = self.i.interpretar("algo elegante")
        self.assertIs(r.accion, Accion.MATIZAR)
        self.assertEqual(r.formalidad, 3)

    def test_correcciones(self):
        r = self.i.interpretar("Llevo una camiseta negra")
        self.assertIs(r.accion, Accion.CORREGIR)
        self.assertEqual((r.prenda_puesta_tipo, r.prenda_puesta_color), ("camiseta", "negro"))
        r = self.i.interpretar("no es una camiseta, es una sudadera")
        self.assertEqual(r.prenda_puesta_tipo, "sudadera")


if __name__ == "__main__":
    unittest.main()
