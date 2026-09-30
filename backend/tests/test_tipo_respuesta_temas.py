import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TipoRespuestaTemasTest(unittest.TestCase):
    """Verifica la fuente canónica que decide el control visible del juego."""

    def test_migracion_deja_escrita_como_regla_predeterminada(self):
        migracion = (ROOT / "database" / "actualizar_tipo_respuesta_temas.sql").read_text(encoding="utf-8")

        self.assertIn("DEFAULT 'numerica'", migracion)
        self.assertIn("'Suma de fracciones'", migracion)
        self.assertIn("'Regla de tres directa'", migracion)
        self.assertIn("'Geometria'", migracion)
        self.assertIn("ELSE 'numerica'", migracion)

    def test_init_incluye_la_migracion_canonica(self):
        init_database = (ROOT / "database" / "init_database.sql").read_text(encoding="utf-8")

        self.assertIn("SOURCE database/actualizar_tipo_respuesta_temas.sql;", init_database)
        self.assertIn("tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL DEFAULT 'numerica'", init_database)


if __name__ == "__main__":
    unittest.main()
