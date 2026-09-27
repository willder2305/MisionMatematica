import unittest
from pathlib import Path

from services.asignaciones_service import _normalizar_ids, _parse_fecha


ROOT = Path(__file__).resolve().parents[2]
ASIGNACIONES_SERVICE = ROOT / "backend" / "services" / "asignaciones_service.py"
ASIGNACIONES_PAGE = ROOT / "frontend" / "src" / "pages" / "AsignacionesPage.jsx"


class AsignacionesServiceTest(unittest.TestCase):
    def test_normaliza_ids_desde_lista_o_texto(self):
        self.assertEqual(_normalizar_ids(["3", 1, "3"]), [1, 3])
        self.assertEqual(_normalizar_ids("5, 2, 5"), [2, 5])

    def test_parse_fecha_datetime_local(self):
        errores = {}
        fecha = _parse_fecha("2026-08-28T10:30", "fecha_inicio", errores, requerida=True)

        self.assertEqual(errores, {})
        self.assertEqual(fecha.year, 2026)
        self.assertEqual(fecha.minute, 30)

    def test_parse_fecha_requerida_agrega_error(self):
        errores = {}
        self.assertIsNone(_parse_fecha("", "fecha_inicio", errores, requerida=True))
        self.assertIn("fecha_inicio", errores)

    def test_runtime_asignaciones_no_borra_relaciones(self):
        codigo = ASIGNACIONES_SERVICE.read_text(encoding="utf-8")
        self.assertNotIn("DELETE FROM asignacion_temas", codigo)
        self.assertNotIn("DELETE FROM asignacion_ejercicios", codigo)
        self.assertIn("estado = 'inactivo'", codigo)

    def test_asignaciones_frontend_no_envia_id_grupo(self):
        codigo = ASIGNACIONES_PAGE.read_text(encoding="utf-8")
        self.assertNotIn("obtenerGrupos", codigo)
        self.assertNotIn("id_grupo:", codigo)
        self.assertIn("id_institucion_grado", codigo)
        self.assertIn("id_seccion", codigo)


if __name__ == "__main__":
    unittest.main()
