import unittest

from services.instituciones_service import (
    normalizar_nombre_institucion,
    normalizar_secciones_configurables,
)


class ModeloInstitucionalTest(unittest.TestCase):
    def test_normaliza_nombre_institucion_para_evitar_duplicados(self):
        self.assertEqual(
            normalizar_nombre_institucion("  COLEGIO   San   Lorenzo  "),
            "colegio san lorenzo",
        )

    def test_acepta_unicamente_secciones_configurables_a_d(self):
        self.assertEqual(normalizar_secciones_configurables(["a", "B", "A"]), ["A", "B"])

    def test_rechaza_secciones_personalizadas_y_unica_desde_frontend(self):
        for seccion in ("E", "Matutina", "Única", "1"):
            with self.subTest(seccion=seccion):
                with self.assertRaises(ValueError):
                    normalizar_secciones_configurables([seccion])


if __name__ == "__main__":
    unittest.main()
