import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from generators.generador_ejercicios import construir_ejercicio_desde_plantilla


ROOT = Path(__file__).resolve().parents[2]
MIGRACION = ROOT / "database" / "actualizar_dificultad_facil.sql"


def plantilla(configuracion):
    """Crea una plantilla mínima para validar los parámetros fáciles sin usar MySQL."""
    return {
        "id_plantilla": 1,
        "id_tema": 1,
        "id_nivel": 1,
        "tipo_respuesta": "numerica",
        "plantilla_enunciado": "Resuelve {expresion}",
        "plantilla_explicacion": "",
        "plantilla_pista": "",
        "configuracion_json": configuracion,
    }


class DificultadFacilTest(unittest.TestCase):
    def test_migracion_actualiza_solo_las_plantillas_faciles_de_catalogo(self):
        sql = MIGRACION.read_text(encoding="utf-8")
        self.assertIn("n.codigo = 'facil'", sql)
        self.assertIn("p.nombre LIKE '% catalogo'", sql)
        self.assertNotIn("n.codigo IN ('intermedio', 'dificil')", sql)
        for tema in (
            "Suma", "Resta", "Multiplicacion", "Division", "Potencias", "Raiz cuadrada",
            "Operaciones combinadas", "Suma de fracciones", "Resta de fracciones",
            "Multiplicacion de fracciones", "Division de fracciones", "Suma de decimales",
            "Resta de decimales", "Multiplicacion de decimales", "Division de decimales",
            "Porcentajes", "Regla de tres directa", "Regla de tres inversa",
            "Operaciones combinadas de fracciones", "Conversiones de fracciones",
        ):
            self.assertIn(f"WHEN '{tema}'", sql)

    def test_fracciones_faciles_comparten_denominador_y_son_propias(self):
        base = plantilla({
            "operacion": "suma_fracciones",
            "denominadores_iguales": True,
            "fracciones_propias": True,
            "variables": {
                "a_numerador": {"min": 1, "max": 4}, "a_denominador": {"min": 3, "max": 6},
                "b_numerador": {"min": 1, "max": 4}, "b_denominador": {"min": 3, "max": 6},
            },
        })
        for seed in range(100):
            parametros = construir_ejercicio_desde_plantilla(base, seed=seed)["parametros"]
            primera, segunda = Fraction(parametros["f1"]), Fraction(parametros["f2"])
            self.assertEqual(primera.denominator, segunda.denominator)
            self.assertLess(primera.numerator, primera.denominator)
            self.assertLess(segunda.numerator, segunda.denominator)

    def test_combinadas_faciles_tienen_dos_operaciones_y_pocos_pasos(self):
        base = plantilla({
            "operacion": "operaciones_combinadas",
            "cantidad_operaciones": 2,
            "con_parentesis": False,
            "variables": {nombre: {"min": 2, "max": 9} for nombre in ("a", "b", "c", "d")},
        })
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            self.assertEqual(ejercicio["parametros"]["cantidad_operaciones"], 2)
            self.assertNotIn("−", ejercicio["parametros"]["expresion"])
            self.assertLessEqual(len(ejercicio["explicacion_pasos"]), 3)

    def test_porcentajes_y_reglas_de_tres_faciles_producen_resultados_enteros(self):
        porcentaje = plantilla({
            "operacion": "porcentaje",
            "porcentajes_permitidos": [10, 25, 50, 100],
            "resultado_entero": True,
            "variables": {"cantidad": {"min": 10, "max": 100}, "porcentaje": {"min": 10, "max": 100}},
        })
        regla = plantilla({
            "operacion": "regla_tres_directa",
            "relacion_entera": True,
            "variables": {
                "a": {"min": 2, "max": 5}, "b": {"min": 2, "max": 25},
                "c": {"min": 2, "max": 5}, "factor": {"min": 1, "max": 5},
            },
        })
        for seed in range(100):
            porcentaje_parametros = construir_ejercicio_desde_plantilla(porcentaje, seed=seed)["parametros"]
            self.assertIn(int(porcentaje_parametros["porcentaje"]), {10, 25, 50, 100})
            self.assertEqual(Decimal(porcentaje_parametros["respuesta"]) % 1, 0)
            regla_parametros = construir_ejercicio_desde_plantilla(regla, seed=seed)["parametros"]
            self.assertEqual(Fraction(regla_parametros["respuesta"]).denominator, 1)

    def test_decimales_y_geometria_faciles_se_mantienen_controlados(self):
        division = plantilla({
            "operacion": "division_decimales",
            "divisor_entero": True,
            "resultado_decimales": 1,
            "variables": {
                "a": {"min": 10, "max": 999, "decimales": 2},
                "b": {"min": 2, "max": 4}, "resultado": {"min": 10, "max": 99},
            },
        })
        geometria = plantilla({
            "operacion": "geometria",
            "figuras": ["cuadrado", "rectangulo", "triangulo"],
            "calculos": ["area"],
            "min_medida": 2,
            "max_medida": 8,
            "area_entera": True,
            "variables": {"a": {"min": 1, "max": 1}, "b": {"min": 1, "max": 1}},
        })
        for seed in range(100):
            decimal = construir_ejercicio_desde_plantilla(division, seed=seed)["parametros"]
            self.assertLessEqual(Decimal(decimal["a"]), Decimal("9.99"))
            self.assertEqual(Decimal(decimal["a"]) / Decimal(decimal["b"]), Decimal(decimal["respuesta"]))
            figura = construir_ejercicio_desde_plantilla(geometria, seed=seed)["parametros"]
            self.assertIn(figura["figura"], {"cuadrado", "rectangulo", "triangulo"})
            self.assertEqual(figura["calculo"], "area")
            self.assertLessEqual(max(figura["medidas"].values()), 9)
            self.assertEqual(Fraction(figura["respuesta"]).denominator, 1)


if __name__ == "__main__":
    unittest.main()
