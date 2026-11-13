"""Recorridos completos de la máquina de estados con módulos simulados."""

import unittest

from asistente.modelos import Fuente, Zona
from asistente.nucleo import Estado
from tests.dobles import crear_maquina


class TestEscenarioDemo(unittest.TestCase):
    def test_camino_feliz_con_matices(self):
        maquina, salida = crear_maquina([
            "¿Qué pantalón va con esto?",
            "otra",
            "algo más informal",
            "sí, me lo quedo",
        ])
        ctx = maquina.ejecutar()

        self.assertIs(maquina.estado, Estado.FIN)
        self.assertGreaterEqual(len(salida.sugerencias), 3)
        self.assertTrue(all(s.prenda.zona is Zona.INFERIOR for s in salida.sugerencias))
        ids = [s.prenda.id for s in salida.sugerencias]
        self.assertEqual(len(ids), len(set(ids)), "no debe repetir sugerencias rechazadas")
        self.assertEqual(ctx.ultima_sugerencia.prenda.formalidad, 1)
        self.assertIn("Te quedas con", salida.todo())

    def test_pide_tipo_y_color_concretos(self):
        maquina, salida = crear_maquina(["quiero un pantalón de traje negro", "vale"])
        maquina.ejecutar()
        self.assertEqual(salida.sugerencias[0].prenda.id, "inf-03")


class TestPoliticaFusion(unittest.TestCase):
    def test_confianza_baja_pide_confirmacion(self):
        maquina, salida = crear_maquina(["sí", "qué pantalón me pongo", "vale"], confianza=0.4)
        ctx = maquina.ejecutar()
        self.assertIn("no estoy seguro", salida.dichos[1])
        self.assertIs(ctx.prenda_actual.fuente, Fuente.USUARIO)
        self.assertEqual(len(salida.sugerencias), 1)

    def test_confianza_baja_el_usuario_corrige(self):
        maquina, _ = crear_maquina(["no, es una camisa blanca", "salir"], confianza=0.4)
        ctx = maquina.ejecutar()
        self.assertEqual((ctx.prenda_actual.tipo, ctx.prenda_actual.color), ("camisa", "blanco"))

    def test_sin_deteccion_pregunta_al_usuario(self):
        maquina, salida = crear_maquina(["una sudadera gris", "salir"], tipo=None)
        ctx = maquina.ejecutar()
        self.assertIn("No consigo ver", salida.dichos[1])
        self.assertEqual(ctx.prenda_actual.tipo, "sudadera")

    def test_contradiccion_con_vision_segura_gana_vision(self):
        maquina, salida = crear_maquina(
            ["¿qué pantalón va con mi camisa verde?", "salir"], confianza=0.95
        )
        ctx = maquina.ejecutar()
        self.assertIn("La cámara ve con bastante claridad", salida.todo())
        self.assertEqual(ctx.prenda_actual.tipo, "camiseta")
        self.assertEqual(len(salida.sugerencias), 1)

    def test_si_el_usuario_insiste_se_le_hace_caso(self):
        maquina, _ = crear_maquina(
            ["llevo una camisa verde", "que no, llevo una camisa verde", "salir"], confianza=0.95
        )
        ctx = maquina.ejecutar()
        self.assertEqual((ctx.prenda_actual.tipo, ctx.prenda_actual.color), ("camisa", "verde"))

    def test_contradiccion_con_vision_dudosa_pide_aclaracion(self):
        maquina, salida = crear_maquina(
            ["¿qué pantalón va con mi camisa verde?", "sí", "vale"], confianza=0.7
        )
        ctx = maquina.ejecutar()
        self.assertIn("pero yo veo", salida.todo())
        self.assertEqual(ctx.prenda_actual.tipo, "camisa")
        self.assertEqual(len(salida.sugerencias), 1)

    def test_voz_no_entendida_pasa_a_teclado(self):
        maquina, salida = crear_maquina(
            [None, "blablabla"], teclado=["qué pantalón va con esto", "salir"]
        )
        maquina.ejecutar()
        self.assertIn("No te he entendido", salida.todo())
        self.assertIn("Escríbelo con el teclado", salida.todo())
        self.assertEqual(len(salida.sugerencias), 1)

    def test_sin_prendas_compatibles_relaja_y_avisa(self):
        maquina, salida = crear_maquina(["quiero un pantalón rojo", "salir"])
        maquina.ejecutar()
        self.assertTrue(salida.sugerencias[0].restricciones_relajadas)
        self.assertIn("no he tenido en cuenta el color", salida.todo())


if __name__ == "__main__":
    unittest.main()
