import json
import unittest
from unittest.mock import patch

from services.plantillas_service import generar_y_guardar_ejercicio


class CursorFake:
    # Simula las consultas minimas que usa generar_y_guardar_ejercicio.
    def __init__(self):
        self.lastrowid = None
        self.generado_guardado = None

    def execute(self, query, params=None):
        self.ultima_consulta = query
        self.ultimos_params = params
        if query.lstrip().startswith("INSERT INTO ejercicios_generados"):
            self.lastrowid = 99
            self.generado_guardado = {
                "id_ejercicio_generado": self.lastrowid,
                "id_plantilla": params[0],
                "id_partida": params[1],
                "id_tema": params[2],
                "id_nivel": params[3],
                "enunciado": params[4],
                "tipo_respuesta": params[5],
                "respuesta_correcta": params[6],
                "explicacion": params[7],
                "explicacion_pasos": params[8],
                "pista": params[9],
                "opciones_json": params[10],
                "parametros_json": params[11],
                "semilla_generacion": params[12],
                "codigo_nivel": "facil",
                "nombre_nivel": "Facil",
                "orden_nivel": 1,
            }

    def fetchall(self):
        if "FROM plantillas_ejercicios" in self.ultima_consulta:
            return [
                self._plantilla(1, "Plantilla invalida"),
                self._plantilla(2, "Plantilla valida"),
            ]
        if "FROM ejercicios_generados" in self.ultima_consulta:
            return []
        return []

    def fetchone(self):
        if "FROM ejercicios_generados" in self.ultima_consulta:
            return self.generado_guardado
        return None

    def _plantilla(self, id_plantilla, nombre):
        return {
            "id_plantilla": id_plantilla,
            "id_grado": 1,
            "id_tema": 1,
            "id_nivel": 1,
            "nombre": nombre,
            "descripcion": None,
            "tipo_respuesta": "seleccion_multiple",
            "plantilla_enunciado": "Cuanto es {a} x {b}?",
            "configuracion_json": {
                "operacion": "multiplicacion",
                "variables": {
                    "a": {"tipo": "entero", "min": 2, "max": 9},
                    "b": {"tipo": "entero", "min": 2, "max": 9},
                },
            },
            "plantilla_explicacion": "{a} x {b} = {respuesta}.",
            "plantilla_pista": "Multiplica los factores.",
            "estado": "publicada",
            "fecha_creacion": None,
            "fecha_modificacion": None,
        }


class PlantillasServiceTest(unittest.TestCase):
    def test_intenta_otra_plantilla_si_la_primera_falla(self):
        generado_valido = {
            "id_plantilla": 2,
            "id_grado": 1,
            "id_tema": 1,
            "id_nivel": 1,
            "enunciado": "Cuanto es 4 x 7?",
            "tipo_respuesta": "seleccion_multiple",
            "respuesta_correcta": "28",
            "explicacion": "4 x 7 = 28.",
            "explicacion_pasos": ["4 × 7 = 28."],
            "pista": "Multiplica los factores.",
            "opciones": [
                {"id": "a", "texto": "21"},
                {"id": "b", "texto": "28"},
                {"id": "c", "texto": "32"},
                {"id": "d", "texto": "35"},
            ],
            "parametros": {"a": 4, "b": 7, "respuesta": 28, "operacion": "multiplicacion"},
            "semilla_generacion": 123456,
        }
        cursor = CursorFake()

        with patch(
            "services.plantillas_service.construir_ejercicio_desde_plantilla",
            side_effect=[ValueError("plantilla invalida"), generado_valido],
        ) as construir:
            pregunta = generar_y_guardar_ejercicio(10, 1, 1, 1, cursor)

        self.assertEqual(construir.call_count, 2)
        self.assertEqual(pregunta["id_plantilla"], 2)
        self.assertEqual(pregunta["id_ejercicio_generado"], 99)
        self.assertEqual(pregunta["origen"], "generado")
        self.assertNotIn("respuesta_correcta", pregunta)
        self.assertEqual(json.loads(cursor.generado_guardado["parametros_json"])["respuesta"], 28)
        self.assertEqual(json.loads(cursor.generado_guardado["explicacion_pasos"]), ["4 × 7 = 28."])

    def test_rechaza_plantilla_que_no_corresponde_al_objetivo(self):
        cursor = CursorFake()

        pregunta = generar_y_guardar_ejercicio(10, 2, 1, 1, cursor)

        self.assertIsNone(pregunta)
        self.assertIsNone(cursor.generado_guardado)


if __name__ == "__main__":
    unittest.main()
