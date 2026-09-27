import unittest

from services.reportes_docente_service import _normalizar_entero, _parse_fecha, _porcentaje, _validar_filtros


class ReportesDocenteServiceTest(unittest.TestCase):
    def test_porcentaje_sin_intentos_devuelve_cero(self):
        self.assertEqual(_porcentaje(0, 0), 0)

    def test_porcentaje_calcula_valor_decimal(self):
        self.assertEqual(_porcentaje(2, 3), 66.67)

    def test_normalizar_entero_acepta_vacio(self):
        errores = {}
        self.assertIsNone(_normalizar_entero("", "id_grupo", errores))
        self.assertEqual(errores, {})

    def test_parse_fecha_datetime_local(self):
        errores = {}
        fecha = _parse_fecha("2026-08-28T19:30", "fecha_inicio", errores)
        self.assertEqual(errores, {})
        self.assertEqual(fecha.hour, 19)

    def test_validar_filtros_rechaza_rango_invertido(self):
        _, errores = _validar_filtros({
            "fecha_inicio": "2026-08-29T10:00",
            "fecha_fin": "2026-08-28T10:00",
        })
        self.assertIn("fecha_fin", errores)


if __name__ == "__main__":
    unittest.main()
