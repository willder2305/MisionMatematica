import unittest
from pathlib import Path

from config import Config
from scripts.seed_dev_student import (
    INITIAL_BALANCE,
    INITIAL_DESCRIPTION,
    TEST_EMAIL,
    TEST_GRADE_CODE,
    TEST_PASSWORD,
    require_non_production,
)


ROOT = Path(__file__).resolve().parents[2]


class SeedDevStudentTest(unittest.TestCase):
    """Verifica que la semilla local conserva sus garantias sin tocar la base real."""

    def test_constants_define_the_requested_local_qa_account(self):
        self.assertEqual(TEST_EMAIL, "estudiante500@mision.test")
        self.assertEqual(TEST_PASSWORD, "Mision500!")
        self.assertEqual(TEST_GRADE_CODE, "6P")
        self.assertEqual(INITIAL_BALANCE, 500)
        self.assertEqual(INITIAL_DESCRIPTION, "Saldo inicial para usuario de pruebas.")

    def test_production_guard_rejects_the_seed(self):
        previous_env = Config.APP_ENV
        try:
            Config.APP_ENV = "production"
            with self.assertRaises(RuntimeError):
                require_non_production()
        finally:
            Config.APP_ENV = previous_env

    def test_seed_uses_the_real_hash_and_local_only_movement(self):
        source = (ROOT / "backend" / "scripts" / "seed_dev_student.py").read_text(encoding="utf-8")
        self.assertIn("generate_password_hash(TEST_PASSWORD)", source)
        self.assertIn("'ajuste_pruebas'", source)
        self.assertIn("'cuenta_propia'", source)
        self.assertIn("--reset-balance", source)

    def test_optimization_migration_is_idempotent_and_included_for_clean_installs(self):
        migration = (ROOT / "database" / "optimizar_indices_y_seed_qa.sql").read_text(encoding="utf-8")
        init_database = (ROOT / "database" / "init_database.sql").read_text(encoding="utf-8")
        self.assertIn("information_schema.STATISTICS", migration)
        self.assertIn("idx_partidas_usuario_estado_actividad", migration)
        self.assertIn("idx_movimientos_usuario_fecha", migration)
        self.assertIn("'ajuste_pruebas'", migration)
        self.assertIn("SOURCE database/optimizar_indices_y_seed_qa.sql;", init_database)


if __name__ == "__main__":
    unittest.main()
