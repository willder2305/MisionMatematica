import unittest
from unittest.mock import patch

from services.grupos_service import _generar_pin_unico


class CursorPinFake:
    # Simula busqueda de PIN activo para probar colisiones.
    def __init__(self, ocupados=None):
        self.ocupados = set(ocupados or [])
        self.ultimo_pin = None

    def execute(self, _query, params=None):
        self.ultimo_pin = params[0]

    def fetchone(self):
        return {"existe": 1} if self.ultimo_pin in self.ocupados else None


class GruposServiceTest(unittest.TestCase):
    def test_genera_pin_de_seis_digitos(self):
        cursor = CursorPinFake()

        with patch("services.grupos_service.secrets.randbelow", return_value=42):
            pin = _generar_pin_unico(cursor)

        self.assertEqual(pin, "000042")
        self.assertTrue(pin.isdigit())
        self.assertEqual(len(pin), 6)

    def test_resuelve_colision_de_pin_activo(self):
        cursor = CursorPinFake(ocupados={"123456"})

        with patch("services.grupos_service.secrets.randbelow", side_effect=[123456, 654321]):
            pin = _generar_pin_unico(cursor)

        self.assertEqual(pin, "654321")


if __name__ == "__main__":
    unittest.main()
