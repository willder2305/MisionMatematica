import unittest

from services.progreso_service import _porcentaje, evaluar_progresion_personal


class ProgresoServiceTest(unittest.TestCase):
    def estado_promocion(self, **cambios):
        estado = {
            "intentos_dificil": 12,
            "precision_dificil": 85,
            "porcentaje_aciertos": 85,
        }
        estado.update(cambios)
        return estado

    def test_porcentaje_usa_formula_oficial(self):
        self.assertEqual(_porcentaje(8, 10), 80)
        self.assertEqual(_porcentaje(1, 3), 33.33)

    def test_porcentaje_sin_intentos_es_cero(self):
        self.assertEqual(_porcentaje(0, 0), 0)

    def test_no_promueve_con_evidencia_insuficiente(self):
        decision = evaluar_progresion_personal(
            self.estado_promocion(intentos_dificil=11), {"codigo": "dificil"}, "4P", [True] * 6
        )
        self.assertEqual(decision, "mantener")

    def test_promueve_cuarto_dificil_a_quinto_con_dominio_sostenido(self):
        decision = evaluar_progresion_personal(self.estado_promocion(), {"codigo": "dificil"}, "4P", [True, True, False, True, True, True])
        self.assertEqual(decision, "promover_grado")

    def test_promueve_quinto_dificil_a_sexto_con_dominio_sostenido(self):
        decision = evaluar_progresion_personal(self.estado_promocion(), {"codigo": "dificil"}, "5P", [True, True, True, True, True, False])
        self.assertEqual(decision, "promover_grado")

    def test_sexto_dificil_es_el_maximo_curricular(self):
        decision = evaluar_progresion_personal(self.estado_promocion(), {"codigo": "dificil"}, "6P", [True] * 6)
        self.assertEqual(decision, "mantener")

    def test_promocion_exige_dificultad_dificil(self):
        decision = evaluar_progresion_personal(self.estado_promocion(), {"codigo": "intermedio"}, "4P", [True] * 6)
        self.assertEqual(decision, "mantener")


if __name__ == "__main__":
    unittest.main()
