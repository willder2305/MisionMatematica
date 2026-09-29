import unittest
from unittest.mock import patch

from services.progreso_service import _actualizar_estado_personal, _porcentaje, evaluar_progresion_personal


class ProgresoServiceTest(unittest.TestCase):
    class CursorPromocionFake:
        """Simula las escrituras y el conteo de partidas usados durante una promoción."""
        def execute(self, _consulta, _parametros=None):
            return None

        def fetchone(self):
            return {"total": 1}

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

    def test_promocion_resuelve_tema_clave_desde_el_tema_de_partida(self):
        estado = {
            "id_progreso_personal_tema": 10,
            "id_grado_curricular": 1,
            "id_tema_actual": 4,
            "id_nivel_actual": 3,
            "codigo_nivel": "dificil",
            "codigo_grado": "4P",
            "total_intentos": 11,
            "total_aciertos": 11,
            "total_errores": 0,
            "racha_correctas": 11,
            "racha_incorrectas": 0,
            "tiempo_promedio_ms": 700,
        }
        partida = {"id_usuario": 7, "id_tema": 4, "id_grado": 1}
        nivel = {"id_nivel": 3}

        with patch("services.progreso_service._tema_por_id", return_value={"nombre_tema": "Suma"}), \
             patch("services.progreso_service._estado_personal", return_value=estado), \
             patch("services.progreso_service._evidencia_dificil_personal", return_value={"intentos_dificil": 12, "precision_dificil": 100, "resultados_recientes": [True] * 6}), \
             patch("services.progreso_service._grado_siguiente", return_value={"id_grado": 2}), \
             patch("services.progreso_service._tema_equivalente", return_value={"id_tema": 9}), \
             patch("services.progreso_service._nivel_inicial", return_value={"id_nivel": 1}), \
             patch("services.progreso_service._actualizar_catalogo_si_corresponde") as actualizar_catalogo:
            resultado = _actualizar_estado_personal(partida, True, 800, nivel, self.CursorPromocionFake())

        self.assertEqual(resultado["id_tema"], 9)
        self.assertEqual(resultado["id_grado"], 2)
        self.assertTrue(resultado["promocionado"])
        actualizar_catalogo.assert_called_once()


if __name__ == "__main__":
    unittest.main()
