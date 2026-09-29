import unittest
from unittest.mock import patch

from app import crear_app
from config import Config


ORIGEN_CANONICO = "https://misionmatematica.com"
ORIGEN_WWW = "https://www.misionmatematica.com"


class CorsProduccionTest(unittest.TestCase):
    def _cliente_con_origenes_produccion(self):
        # Construye una app aislada para verificar los orígenes explícitos del VPS.
        with patch.object(Config, "FRONTEND_URLS", [ORIGEN_CANONICO, ORIGEN_WWW]):
            return crear_app().test_client()

    def test_preflight_permite_dominio_canonico(self):
        response = self._cliente_con_origenes_produccion().options(
            "/api/health",
            headers={
                "Origin": ORIGEN_CANONICO,
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ORIGEN_CANONICO)

    def test_preflight_rechaza_origen_no_configurado(self):
        response = self._cliente_con_origenes_produccion().options(
            "/api/health",
            headers={
                "Origin": "https://sitio-malicioso.example",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))


if __name__ == "__main__":
    unittest.main()
