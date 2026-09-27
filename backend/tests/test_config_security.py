"""Pruebas de endurecimiento para configuración sensible del backend."""

import unittest
from unittest.mock import patch

from config import Config, validar_configuracion_produccion


class ConfigSecurityTest(unittest.TestCase):
    """Verifica que producción no pueda iniciarse con secretos JWT de ejemplo."""

    def test_produccion_rechaza_secreto_jwt_de_desarrollo(self):
        """Bloquea una configuración que permitiría firmar tokens previsibles."""
        with patch.object(Config, "APP_ENV", "production"), patch.object(Config, "JWT_SECRET_KEY", "dev-secret-change-me"):
            with self.assertRaises(RuntimeError):
                validar_configuracion_produccion()

    def test_produccion_acepta_secreto_jwt_configurado(self):
        """Acepta un secreto no predeterminado entregado por variables de entorno."""
        with patch.object(Config, "APP_ENV", "production"), patch.object(Config, "JWT_SECRET_KEY", "secreto-local-de-prueba-no-predeterminado"):
            validar_configuracion_produccion()


if __name__ == "__main__":
    unittest.main()
