import unittest
from pathlib import Path

from services.ejercicios_service import obtener_explicacion_pasos_ejercicio
from services.plantillas_service import serializar_pregunta_generada


ROOT = Path(__file__).resolve().parents[2]


class RetroalimentacionProcedimientoTest(unittest.TestCase):
    def test_pregunta_generada_no_expone_respuesta_ni_procedimiento(self):
        pregunta = serializar_pregunta_generada({
            "id_ejercicio_generado": 1,
            "id_plantilla": 1,
            "id_tema": 1,
            "id_nivel": 1,
            "codigo_nivel": "facil",
            "nombre_nivel": "Fácil",
            "orden_nivel": 1,
            "enunciado": "¿Cuánto es 4 × 7?",
            "tipo_respuesta": "seleccion_multiple",
            "pista": "Multiplica.",
            "opciones_json": [],
            "respuesta_correcta": "28",
            "explicacion_pasos": ["4 × 7 = 28."],
        })

        self.assertNotIn("respuesta_correcta", pregunta)
        self.assertNotIn("explicacion_pasos", pregunta)

    def test_recupera_pasos_persistidos_y_limita_su_longitud(self):
        pasos = obtener_explicacion_pasos_ejercicio({
            "explicacion_pasos": '["24 × 10 = 240.", "24 × 3 = 72.", "240 + 72 = 312.", "Paso adicional.", "No debe mostrarse."]',
        })

        self.assertEqual(pasos, ["24 × 10 = 240.", "24 × 3 = 72.", "240 + 72 = 312.", "Paso adicional."])

    def test_panel_muestra_una_respuesta_y_la_seccion_de_procedimiento(self):
        pagina = (ROOT / "frontend" / "src" / "pages" / "JuegoPage.jsx").read_text(encoding="utf-8")

        self.assertEqual(pagina.count("Respuesta correcta:"), 1)
        self.assertNotIn("La respuesta correcta es", pagina)
        self.assertIn("¿Cómo se resuelve?", pagina)
        self.assertIn("explicacionPasos", pagina)


if __name__ == "__main__":
    unittest.main()
