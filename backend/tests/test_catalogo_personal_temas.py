import unittest
from pathlib import Path

from services.progreso_service import CATALOGO_PERSONAL_TEMAS, DEFINICIONES_TEMA_PERSONAL


ROOT = Path(__file__).resolve().parents[2]
PROGRESO_SERVICE = ROOT / "backend" / "services" / "progreso_service.py"
ASIGNACIONES_SERVICE = ROOT / "backend" / "services" / "asignaciones_service.py"
JUEGO_PAGE = ROOT / "frontend" / "src" / "pages" / "JuegoPage.jsx"


class CatalogoPersonalTemasTest(unittest.TestCase):
    def test_catalogo_personal_contiene_los_veintiun_temas_en_orden_pedagogico(self):
        self.assertEqual(len(CATALOGO_PERSONAL_TEMAS), 21)
        self.assertEqual(
            [tema[0] for tema in CATALOGO_PERSONAL_TEMAS],
            [
                "Suma", "Resta", "Multiplicacion", "Division", "Potencias", "Raiz cuadrada",
                "Operaciones combinadas", "Suma de fracciones", "Resta de fracciones",
                "Multiplicacion de fracciones", "Division de fracciones", "Operaciones combinadas de fracciones",
                "Conversiones de fracciones", "Suma de decimales", "Resta de decimales",
                "Multiplicacion de decimales", "Division de decimales", "Porcentajes",
                "Regla de tres directa", "Regla de tres inversa", "Geometria",
            ],
        )

    def test_grado_minimo_personal_respeta_la_matriz_curricular(self):
        for nombre, _, _, grado in CATALOGO_PERSONAL_TEMAS:
            esperado = "6P" if nombre == "Geometria" else "5P" if nombre in {
                "Regla de tres directa", "Regla de tres inversa", "Operaciones combinadas de fracciones", "Conversiones de fracciones",
            } else "4P"
            self.assertEqual(grado, esperado)
            self.assertEqual(DEFINICIONES_TEMA_PERSONAL[nombre]["grado_minimo"], esperado)

    def test_etiquetas_visibles_conservan_tildes_sin_cambiar_claves_internas(self):
        self.assertEqual(DEFINICIONES_TEMA_PERSONAL["Division"]["nombre_visible"], "División")
        self.assertEqual(DEFINICIONES_TEMA_PERSONAL["Multiplicacion"]["nombre_visible"], "Multiplicación")
        self.assertEqual(DEFINICIONES_TEMA_PERSONAL["Raiz cuadrada"]["nombre_visible"], "Raíz cuadrada")
        self.assertEqual(DEFINICIONES_TEMA_PERSONAL["Geometria"]["nombre_visible"], "Geometría")

    def test_catalogo_personal_no_usa_grado_desbloqueado_para_ocultar_temas(self):
        codigo = PROGRESO_SERVICE.read_text(encoding="utf-8")
        inicio = codigo.index("def listar_temas_personales")
        fin = codigo.index("def _tema_permitido_personal", inicio)
        consulta = codigo[inicio:fin]
        self.assertNotIn("_catalogo_personal", consulta)
        self.assertNotIn("orden_visualizacion <=", consulta)
        self.assertIn("NOT EXISTS", consulta)

    def test_progreso_personal_sigue_separado_por_tema(self):
        codigo = PROGRESO_SERVICE.read_text(encoding="utf-8")
        self.assertIn("WHERE ppt.id_usuario = %s AND ppt.tema_clave = %s", codigo)
        self.assertIn("tema_clave, id_tema_actual, id_grado_curricular", codigo)

    def test_actividades_docentes_siguen_restringidas_al_grado_institucional(self):
        codigo = ASIGNACIONES_SERVICE.read_text(encoding="utf-8")
        self.assertIn("AND id_grado = %s", codigo)
        self.assertIn("t.id_grado = %s", codigo)

    def test_selector_del_juego_agrupa_temas_y_no_expone_grado_ni_dificultad(self):
        codigo = JUEGO_PAGE.read_text(encoding="utf-8")
        self.assertIn("temasPorCategoria", codigo)
        self.assertIn("<optgroup", codigo)
        self.assertNotIn('name="id_grado"', codigo)
        self.assertNotIn('name="id_nivel"', codigo)


if __name__ == "__main__":
    unittest.main()
