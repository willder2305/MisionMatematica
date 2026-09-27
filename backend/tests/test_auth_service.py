import unittest

from services.auth_service import _validar_registro


class AuthServiceValidationTest(unittest.TestCase):
    def test_valida_registro_correcto(self):
        datos, errores = _validar_registro({
            "nombres": "Ana",
            "apellidos": "Lopez",
            "correo": "ANA@TEST.LOCAL",
            "password": "Password123",
            "rol": "estudiante",
        })

        self.assertEqual(errores, {})
        self.assertEqual(datos["correo"], "ana@test.local")
        self.assertEqual(datos["rol"], "estudiante")

    def test_rechaza_password_corto_y_rol_invalido(self):
        _, errores = _validar_registro({
            "nombres": "A",
            "apellidos": "B",
            "correo": "correo-invalido",
            "password": "123",
            "rol": "superusuario",
        })

        self.assertIn("nombres", errores)
        self.assertIn("apellidos", errores)
        self.assertIn("correo", errores)
        self.assertIn("password", errores)
        self.assertIn("rol", errores)

    def test_registro_publico_no_permite_crear_administradores(self):
        """Evita que un cliente anónimo se asigne el rol privilegiado de administrador."""
        _, errores = _validar_registro({
            "nombres": "Ana",
            "apellidos": "Admin",
            "correo": "ana.admin@test.local",
            "password": "Password123",
            "rol": "administrador",
        })

        self.assertIn("rol", errores)


if __name__ == "__main__":
    unittest.main()
