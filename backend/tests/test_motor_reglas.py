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
            "tiempo_promedio_ms": 0,
            "decisiones_recientes": [],
        }
        base.update(overrides)
        return base

    def test_aumenta_solo_con_tres_aciertos_exactos(self):
        decision = self.motor.decidir(self.metricas(correctas_consecutivas=3), NIVELES[0])
        self.assertEqual(decision["accion"], "aumentar")
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "intermedio")

        decision = self.motor.decidir(self.metricas(correctas_consecutivas=4), NIVELES[1])
        self.assertEqual(decision["accion"], "mantener")

    def test_reduce_con_dos_errores_y_refuerza_en_minimo(self):
        decision = self.motor.decidir(self.metricas(incorrectas_consecutivas=2), NIVELES[1])
        self.assertEqual(decision["accion"], "reducir")
        self.assertTrue(decision["recomendar_refuerzo"])
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "facil")

        decision = self.motor.decidir(self.metricas(incorrectas_consecutivas=2), NIVELES[0])
        self.assertEqual(decision["accion"], "reforzar")
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "facil")

    def test_mantiene_en_rango_estable(self):
        decision = self.motor.decidir(self.metricas(total_intentos=5, porcentaje_aciertos=70), NIVELES[1])
        self.assertEqual(decision["accion"], "mantener")
        self.assertEqual(decision["codigo_regla"], "rango_estable")

    def test_porcentaje_alto_respeta_cooldown(self):
        decision = self.motor.decidir(self.metricas(total_intentos=5, porcentaje_aciertos=100), NIVELES[1])
        self.assertEqual(decision["accion"], "aumentar")

        decision = self.motor.decidir(
            self.metricas(
                total_intentos=6,
                porcentaje_aciertos=100,
                decisiones_recientes=[{"accion": "aumentar"}],
            ),
            NIVELES[1],
        )
        self.assertEqual(decision["accion"], "mantener")

    def test_porcentaje_bajo_reduce_sin_cooldown_reciente(self):
        decision = self.motor.decidir(self.metricas(total_intentos=5, porcentaje_aciertos=40), NIVELES[2])
        self.assertEqual(decision["accion"], "reducir")
        self.assertEqual(decision["nivel_recomendado"]["codigo"], "intermedio")

        decision = self.motor.decidir(
            self.metricas(
                total_intentos=6,
                porcentaje_aciertos=30,
                decisiones_recientes=[{"accion": "reducir"}],
            ),
            NIVELES[2],
        )
        self.assertEqual(decision["accion"], "mantener")


if __name__ == "__main__":
    unittest.main()
