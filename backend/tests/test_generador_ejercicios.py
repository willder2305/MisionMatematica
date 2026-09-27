import unittest
from decimal import Decimal
from fractions import Fraction

from generators.generador_ejercicios import construir_ejercicio_desde_plantilla
from generators.contextos_regla_tres import DIRECTA, INVERSA


def plantilla(operacion, tipo_respuesta="seleccion_multiple", variables=None, extras=None):
    config = {"operacion": operacion, "variables": variables or {
        "a": {"tipo": "entero", "min": 2, "max": 9},
        "b": {"tipo": "entero", "min": 2, "max": 9},
    }}
    if extras:
        config.update(extras)
    return {
        "id_plantilla": 1,
        "id_tema": 1,
        "id_nivel": 1,
        "tipo_respuesta": tipo_respuesta,
        "plantilla_enunciado": "¿Cuánto es {a} x {b}?",
        "plantilla_explicacion": "{a} x {b} = {respuesta}.",
        "plantilla_pista": "Calcula paso a paso.",
        "configuracion_json": config,
    }


class GeneradorEjerciciosTest(unittest.TestCase):
    def test_genera_100_sumas_validas(self):
        base = plantilla("suma", variables={
            "a": {"tipo": "entero", "min": 1, "max": 20},
            "b": {"tipo": "entero", "min": 1, "max": 20},
        })
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            self.assertEqual(int(ejercicio["respuesta_correcta"]), ejercicio["parametros"]["a"] + ejercicio["parametros"]["b"])

    def test_resta_sin_negativos(self):
        base = plantilla("resta", "numerica", variables={
            "a": {"tipo": "entero", "min": 1, "max": 20},
            "b": {"tipo": "entero", "min": 1, "max": 20},
        }, extras={"permitir_negativos": False})
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            self.assertGreaterEqual(int(ejercicio["respuesta_correcta"]), 0)

    def test_multiplicacion_valida(self):
        base = plantilla("multiplicacion")
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            self.assertEqual(int(ejercicio["respuesta_correcta"]), ejercicio["parametros"]["a"] * ejercicio["parametros"]["b"])

    def test_division_exacta(self):
        base = plantilla("division", "numerica", variables={
            "resultado": {"tipo": "entero", "min": 2, "max": 12},
            "divisor": {"tipo": "entero", "min": 2, "max": 12},
        }, extras={"division_exacta": True})
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            self.assertNotEqual(ejercicio["parametros"]["b"], 0)
            self.assertEqual(ejercicio["parametros"]["a"] % ejercicio["parametros"]["b"], 0)

    def test_opciones_unicas_con_correcta_incluida(self):
        base = plantilla("multiplicacion")
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            textos = [opcion["texto"] for opcion in ejercicio["opciones"]]
            self.assertEqual(len(textos), 4)
            self.assertEqual(len(set(textos)), 4)
            self.assertIn(ejercicio["respuesta_correcta"], textos)

    def test_no_repite_parametros_si_hay_alternativas(self):
        base = plantilla("multiplicacion")
        primero = construir_ejercicio_desde_plantilla(base, seed=7)
        segundo = construir_ejercicio_desde_plantilla(base, historial_parametros=[primero["parametros"]], seed=7)
        self.assertNotEqual(primero["parametros"], segundo["parametros"])

    def test_potencia_y_raiz_exactas(self):
        potencia = plantilla("potencia", variables={
            "base": {"tipo": "entero", "min": 2, "max": 10},
            "exponente": {"tipo": "entero", "min": 2, "max": 4},
        }, extras={"incluir_base_10": True})
        raiz = plantilla("raiz_cuadrada", variables={
            "raiz": {"tipo": "entero", "min": 2, "max": 31},
        })
        for seed in range(50):
            ejercicio_potencia = construir_ejercicio_desde_plantilla(potencia, seed=seed)
            self.assertEqual(
                int(ejercicio_potencia["respuesta_correcta"]),
                ejercicio_potencia["parametros"]["base"] ** ejercicio_potencia["parametros"]["exponente"],
            )
            ejercicio_raiz = construir_ejercicio_desde_plantilla(raiz, seed=seed)
            self.assertEqual(
                int(ejercicio_raiz["respuesta_correcta"]) ** 2,
                ejercicio_raiz["parametros"]["radicando"],
            )
            self.assertLessEqual(ejercicio_raiz["parametros"]["radicando"], 961)

    def test_fracciones_usan_fraction_y_simplifican(self):
        base = plantilla("suma_fracciones", variables={
            "a_numerador": {"tipo": "entero", "min": 1, "max": 9},
            "a_denominador": {"tipo": "entero", "min": 2, "max": 9},
            "b_numerador": {"tipo": "entero", "min": 1, "max": 9},
            "b_denominador": {"tipo": "entero", "min": 2, "max": 9},
        })
        for seed in range(50):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            esperada = Fraction(ejercicio["parametros"]["f1"]) + Fraction(ejercicio["parametros"]["f2"])
            self.assertEqual(Fraction(ejercicio["respuesta_correcta"]), esperada)

    def test_decimales_usan_decimal(self):
        base = plantilla("multiplicacion_decimales", variables={
            "a": {"tipo": "decimal", "min": 100, "max": 999, "decimales": 2},
            "b": {"tipo": "decimal", "min": 10, "max": 99, "decimales": 1},
        })
        for seed in range(50):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            esperada = Decimal(ejercicio["parametros"]["a"]) * Decimal(ejercicio["parametros"]["b"])
            self.assertEqual(Decimal(ejercicio["respuesta_correcta"]), esperada)

    def test_division_decimal_es_exacta_y_no_aproxima(self):
        base = plantilla("division_decimales", "numerica", variables={
            "a": {"tipo": "decimal", "min": 100, "max": 999, "decimales": 1},
            "b": {"tipo": "decimal", "min": 10, "max": 99, "decimales": 1},
        })
        for seed in range(100):
            ejercicio = construir_ejercicio_desde_plantilla(base, seed=seed)
            parametros = ejercicio["parametros"]
            self.assertEqual(
                Decimal(parametros["a"]) / Decimal(parametros["b"]),
                Decimal(ejercicio["respuesta_correcta"]),
            )

    def test_regla_de_tres_directa_e_inversa(self):
        variables = {
            "a": {"tipo": "entero", "min": 2, "max": 12},
            "b": {"tipo": "entero", "min": 2, "max": 30},
            "c": {"tipo": "entero", "min": 2, "max": 12},
        }
        directa = plantilla("regla_tres_directa", variables=variables)
        inversa = plantilla("regla_tres_inversa", variables=variables)
        for seed in range(50):
            ej_directa = construir_ejercicio_desde_plantilla(directa, seed=seed)
            pd = ej_directa["parametros"]
            self.assertEqual(Fraction(ej_directa["respuesta_correcta"]), Fraction(pd["b"] * pd["c"], pd["a"]))
            self.assertEqual(pd["tipo_proporcion"], "directa")

            ej_inversa = construir_ejercicio_desde_plantilla(inversa, seed=seed)
            pi = ej_inversa["parametros"]
            self.assertEqual(Fraction(ej_inversa["respuesta_correcta"]), Fraction(pi["a"] * pi["b"], pi["c"]))
            self.assertEqual(pi["tipo_proporcion"], "inversa")

    def test_regla_de_tres_tiene_banco_amplio_y_ortografia_correcta(self):
        self.assertGreaterEqual(len(DIRECTA), 10)
        self.assertGreaterEqual(len(INVERSA), 10)
        variables = {"a": {"tipo": "entero", "min": 2, "max": 12}, "b": {"tipo": "entero", "min": 2, "max": 30}, "c": {"tipo": "entero", "min": 2, "max": 12}}
        contextos = set()
        for seed in range(80):
            ejercicio = construir_ejercicio_desde_plantilla(plantilla("regla_tres_directa", variables=variables), seed=seed)
            contextos.add(ejercicio["parametros"]["context_key"])
            self.assertTrue(ejercicio["enunciado"].endswith("?"))
            self.assertNotIn(" cuanto ", ejercicio["enunciado"].lower())
        self.assertGreaterEqual(len(contextos), 8)

    def test_conversiones_y_geometria_validas(self):
        conversion = plantilla("conversion_fracciones", extras={"subtipo": "mixta"})
        geometria = plantilla("geometria", extras={
            "figuras": ["cuadrado", "rectangulo", "triangulo", "circulo", "rombo", "poligono"],
            "calculos": ["area", "perimetro"],
            "min_medida": 2,
            "max_medida": 12,
        })
        for seed in range(50):
            ej_conversion = construir_ejercicio_desde_plantilla(conversion, seed=seed)
            self.assertEqual(ej_conversion["parametros"]["subtipo_conversion"], "mixta")
            self.assertIn(" ", ej_conversion["respuesta_correcta"])

            ej_geometria = construir_ejercicio_desde_plantilla(geometria, seed=seed)
            self.assertIn(ej_geometria["parametros"]["figura"], {"cuadrado", "rectangulo", "triangulo", "circulo", "rombo", "poligono"})
            self.assertIn(ej_geometria["parametros"]["calculo"], {"area", "perimetro"})
            self.assertTrue(ej_geometria["respuesta_correcta"])

    def test_todos_los_generadores_incluyen_procedimiento_breve_y_coherente(self):
        variables_enteras = {
            "a": {"tipo": "entero", "min": 2, "max": 12},
            "b": {"tipo": "entero", "min": 2, "max": 12},
        }
        variables_fracciones = {
            "a_numerador": {"tipo": "entero", "min": 1, "max": 9},
            "a_denominador": {"tipo": "entero", "min": 2, "max": 9},
            "b_numerador": {"tipo": "entero", "min": 1, "max": 9},
            "b_denominador": {"tipo": "entero", "min": 2, "max": 9},
            "c_numerador": {"tipo": "entero", "min": 1, "max": 9},
            "c_denominador": {"tipo": "entero", "min": 2, "max": 9},
        }
        configuraciones = [
            plantilla("suma", variables=variables_enteras),
            plantilla("resta", variables=variables_enteras),
            plantilla("multiplicacion", variables=variables_enteras),
            plantilla("division", variables={"resultado": {"min": 2, "max": 12}, "divisor": {"min": 2, "max": 12}}),
            plantilla("potencia", variables={"base": {"min": 2, "max": 10}, "exponente": {"min": 2, "max": 3}}),
            plantilla("raiz_cuadrada", variables={"raiz": {"min": 2, "max": 12}}),
            plantilla("operaciones_combinadas", variables={**variables_enteras, "c": {"min": 2, "max": 9}, "d": {"min": 2, "max": 9}}),
            *[plantilla(operacion, variables=variables_fracciones) for operacion in ("suma_fracciones", "resta_fracciones", "multiplicacion_fracciones", "division_fracciones", "operaciones_combinadas_fracciones")],
            *[plantilla(operacion, variables={"a": {"min": 100, "max": 999, "decimales": 2}, "b": {"min": 10, "max": 99, "decimales": 1}}) for operacion in ("suma_decimales", "resta_decimales", "multiplicacion_decimales", "division_decimales")],
            plantilla("porcentaje", variables={"cantidad": {"min": 10, "max": 200}, "porcentaje": {"min": 1, "max": 100}}),
            *[plantilla(operacion, variables={"a": {"min": 2, "max": 12}, "b": {"min": 2, "max": 30}, "c": {"min": 2, "max": 12}}) for operacion in ("regla_tres_directa", "regla_tres_inversa")],
            plantilla("conversion_fracciones", extras={"subtipo": "mixta"}),
            plantilla("geometria", extras={"figuras": ["cuadrado", "rectangulo", "triangulo", "circulo", "rombo", "poligono"], "calculos": ["area", "perimetro"]}),
        ]

        for indice, base in enumerate(configuraciones):
            with self.subTest(operacion=base["configuracion_json"]["operacion"]):
                ejercicio = construir_ejercicio_desde_plantilla(base, seed=indice + 1)
                pasos = ejercicio["explicacion_pasos"]
                self.assertGreaterEqual(len(pasos), 1)
                self.assertLessEqual(len(pasos), 4)
                self.assertIn(ejercicio["respuesta_correcta"], " ".join(pasos))


if __name__ == "__main__":
    unittest.main()
