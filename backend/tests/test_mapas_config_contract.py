import re
import unittest
from pathlib import Path


class MapasConfigContractTest(unittest.TestCase):
    def setUp(self):
        self.codigo = Path(__file__).resolve().parents[2] / "frontend" / "src" / "config" / "mapasConfig.js"
        self.contenido = self.codigo.read_text(encoding="utf-8")

    def test_declara_mapas_base_y_recompensas(self):
        self.assertIn('import bosqueAsset from "../assets/juego/escenarios/escenario_1_base_1983x793.png"', self.contenido)
        self.assertIn('import mapa2Asset from "../assets/juego/escenarios/escenario_2_alineado_1983x793.png"', self.contenido)
        self.assertIn('import mapa3Asset from "../assets/juego/escenarios/escenario_3_alineado_1983x793.png"', self.contenido)
        self.assertIn('mapa_4_espacio: crearMapa("mapa_4_espacio"', self.contenido)
        self.assertIn('mapa_9_cueva_cristales: crearMapa("mapa_9_cueva_cristales"', self.contenido)
        self.assertIn("export const MAPAS_DISPONIBLES = Object.keys(mapasConfig)", self.contenido)
        self.assertIn("export const MAP_BASE_WIDTH = 1983", self.contenido)
        self.assertIn("export const MAP_BASE_HEIGHT = 793", self.contenido)

    def test_cada_mapa_tiene_casillas_logicas_cero_a_diez(self):
        casillas = {int(valor) for valor in re.findall(r"\{\s*tile:\s*(\d+),\s*x:", self.contenido)}
        self.assertEqual(sorted(casillas), list(range(11)))


if __name__ == "__main__":
    unittest.main()
