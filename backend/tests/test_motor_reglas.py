import unittest

from agent.motor_reglas import MotorReglasAdaptativo


NIVELES = [
    {"id_nivel": 1, "codigo": "facil", "nombre": "Facil", "orden_nivel": 1},
    {"id_nivel": 2, "codigo": "intermedio", "nombre": "Intermedio", "orden_nivel": 2},
    {"id_nivel": 3, "codigo": "dificil", "nombre": "Dificil", "orden_nivel": 3},
]

REGLAS = [
    {"codigo_regla": "dos_errores_consecutivos", "prioridad": 1, "parametros_json": {"incorrectas_consecutivas": 2}},
    {"codigo_regla": "tres_aciertos_consecutivos", "prioridad": 2, "parametros_json": {"correctas_consecutivas": 3}},
    {"codigo_regla": "porcentaje_bajo", "prioridad": 3, "parametros_json": {"min_intentos": 5, "porcentaje_maximo": 60, "cooldown_intentos": 3}},
    {"codigo_regla": "porcentaje_alto", "prioridad": 4, "parametros_json": {"min_intentos": 5, "porcentaje_minimo": 80, "cooldown_intentos": 3}},
    {"codigo_regla": "rango_estable", "prioridad": 5, "parametros_json": {"min_intentos": 5, "porcentaje_minimo": 60, "porcentaje_maximo": 80}},
]


class MotorReglasAdaptativoTest(unittest.TestCase):
    def setUp(self):
        self.motor = MotorReglasAdaptativo(NIVELES, REGLAS)

    def metricas(self, **overrides):
        base = {
            "total_intentos": 0,
            "total_aciertos": 0,
            "total_errores": 0,
            "porcentaje_aciertos": 0,
            "correctas_consecutivas": 0,
            "incorrectas_consecutivas": 0,
            "errores_ultimas_cinco": 0,
            "preguntas_desde_ultimo_cambio": 99,
            "tiempo_promedio_ms": 0,
            "decisiones_recientes": [],
        }
        base.update(overrides)
        return base

    def test_tres_aciertos_no_promueven_y_ocho_consistentes_si(self):
        decision = self.motor.decidir(self.metricas(total_intentos=3, porcentaje_aciertos=100, correctas_consecutivas=3), NIVELES[0])
        self.assertEqual(decision["accion"], "mantener")
        decision = self.motor.decidir(self.metricas(total_intentos=8, porcentaje_aciertos=87.5, correctas_consecutivas=4), NIVELES[0])
        self.assertEqual(decision["accion"], "aumentar")
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "intermedio")

    def test_descenso_requiere_patron_y_refuerza_en_minimo(self):
        decision = self.motor.decidir(self.metricas(total_intentos=6, porcentaje_aciertos=40), NIVELES[1])
        self.assertEqual(decision["accion"], "reducir")
        self.assertTrue(decision["recomendar_refuerzo"])
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "facil")

        decision = self.motor.decidir(self.metricas(total_intentos=6, errores_ultimas_cinco=3), NIVELES[0])
        self.assertEqual(decision["accion"], "reforzar")
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "facil")

    def test_error_aislado_mantiene_el_nivel(self):
        decision = self.motor.decidir(self.metricas(total_intentos=6, porcentaje_aciertos=83, errores_ultimas_cinco=1), NIVELES[1])
        self.assertEqual(decision["accion"], "mantener")

    def test_cooldown_impide_otro_cambio_antes_de_seis_preguntas(self):
        decision = self.motor.decidir(self.metricas(total_intentos=8, porcentaje_aciertos=100, correctas_consecutivas=8, preguntas_desde_ultimo_cambio=5), NIVELES[1])
        self.assertEqual(decision["accion"], "mantener")


if __name__ == "__main__":
    unittest.main()
