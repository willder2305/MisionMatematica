import unittest

from services.report_metrics_service import calcular_mejora, calcular_porcentaje


class ReportMetricsServiceTest(unittest.TestCase):
    def test_calcula_precision_con_dos_decimales(self):
        self.assertEqual(calcular_porcentaje(2, 3), 66.67)

    def test_mejora_positiva_con_veinte_intentos(self):
        mejora, estado = calcular_mejora(([True] * 4 + [False] * 6) + ([True] * 6 + [False] * 4))
        self.assertEqual((mejora, estado), (20.0, "suficiente"))

    def test_mejora_negativa_con_veinte_intentos(self):
        mejora, estado = calcular_mejora(([True] * 6 + [False] * 4) + ([True] * 4 + [False] * 6))
        self.assertEqual((mejora, estado), (-20.0, "suficiente"))

    def test_mejora_cero_con_veinte_intentos(self):
        mejora, estado = calcular_mejora(([True, False] * 5) + ([True, False] * 5))
        self.assertEqual((mejora, estado), (0.0, "suficiente"))

    def test_diecisiete_a_diecinueve_intentos_no_infiere_tendencia(self):
        for cantidad in (17, 18, 19):
            with self.subTest(cantidad=cantidad):
                self.assertEqual(calcular_mejora([True] * cantidad), (None, "sin_datos_suficientes"))


if __name__ == "__main__":
    unittest.main()
