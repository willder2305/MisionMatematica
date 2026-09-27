"""Contrato del endpoint de salud usado por el despliegue productivo."""

import unittest

from app import crear_app


class HealthRouteTest(unittest.TestCase):
    """Verifica que el healthcheck sea público, mínimo y estable."""

    def test_healthcheck_responde_sin_dependencia_de_base_de_datos(self):
        respuesta = crear_app().test_client().get("/api/health")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json(), {"success": True, "data": {"status": "ok"}})


if __name__ == "__main__":
    unittest.main()
