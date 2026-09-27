import unittest

from services import juego_adaptativo_service as juego


class CatalogoAdaptativoServiceTest(unittest.TestCase):
    def test_respuesta_decimal_y_fraccion_equivalente(self):
        self.assertTrue(juego._evaluar_respuesta({"respuesta_correcta": "2.50"}, "2,5"))
        self.assertTrue(juego._evaluar_respuesta({"respuesta_correcta": "1/2"}, "2/4"))

    def test_fraccion_simplificada_requerida(self):
        ejercicio = {"respuesta_correcta": "1/2", "parametros_json": {"forma_simplificada_requerida": True}}
        self.assertFalse(juego._evaluar_respuesta(ejercicio, "2/4"))
        self.assertTrue(juego._evaluar_respuesta(ejercicio, "1/2"))


if __name__ == "__main__":
    unittest.main()
