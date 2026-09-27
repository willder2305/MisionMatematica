import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from services.asignaciones_service import _normalizar_ids, _parse_fecha, _validar_payload


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

    def test_asignaciones_siempre_fijan_diez_preguntas(self):
        codigo_backend = ASIGNACIONES_SERVICE.read_text(encoding="utf-8")
        codigo_frontend = ASIGNACIONES_PAGE.read_text(encoding="utf-8")
        self.assertIn("cantidad_preguntas = 10", codigo_backend)
        self.assertIn('cantidad_preguntas: 10', codigo_frontend)
        self.assertNotIn('name="cantidad_preguntas"', codigo_frontend)

    def test_payload_manipulado_no_puede_cambiar_las_diez_preguntas(self):
        """La validacion del servidor ignora cantidades enviadas por clientes alterados."""
        datos = {
            "nombre": "Actividad QA",
            "tipo": "generacion_automatica",
            "id_nivel_inicial": 1,
            "cantidad_preguntas": 999,
            "fecha_inicio": "2026-09-01T08:00",
            "temas": [1],
        }
        with patch("services.asignaciones_service._validar_nivel", return_value=True), patch(
            "services.asignaciones_service._validar_temas", return_value=True
        ):
            datos_limpios, errores = _validar_payload(datos, {"id_grado_base": 1}, MagicMock())

        self.assertEqual(errores, {})
        self.assertEqual(datos_limpios["cantidad_preguntas"], 10)


if __name__ == "__main__":
    unittest.main()
