import unittest
from unittest.mock import patch

from services.jwt_service import (
    TokenError,
    _base64url_encode,
    _firmar,
    crear_token,
    decodificar_token,
    hash_token,
)


USUARIO = {
    "id_usuario": 7,
    "correo": "estudiante@test.local",
    "rol": "estudiante",
}


class JwtServiceTest(unittest.TestCase):
    def test_crea_y_decodifica_access_token(self):
        token, payload = crear_token(USUARIO, tipo="access", expires_seconds=60)
        decodificado = decodificar_token(token, tipo="access")

        self.assertEqual(decodificado["sub"], USUARIO["id_usuario"])
        self.assertEqual(decodificado["correo"], USUARIO["correo"])
        self.assertEqual(decodificado["rol"], USUARIO["rol"])
        self.assertEqual(decodificado["type"], "access")
        self.assertEqual(decodificado["jti"], payload["jti"])

    def test_rechaza_tipo_incorrecto(self):
        token, _ = crear_token(USUARIO, tipo="refresh", expires_seconds=60)

        with self.assertRaises(TokenError):
            decodificar_token(token, tipo="access")

    def test_rechaza_algoritmo_distinto_aunque_la_firma_sea_valida(self):
        token, _ = crear_token(USUARIO, tipo="access", expires_seconds=60)
        _, payload_b64, _ = token.split(".")
        header_b64 = _base64url_encode(b'{"alg":"none","typ":"JWT"}')
        firma_b64 = _base64url_encode(_firmar(f"{header_b64}.{payload_b64}"))
        token_modificado = f"{header_b64}.{payload_b64}.{firma_b64}"

        with self.assertRaises(TokenError):
            decodificar_token(token_modificado, tipo="access")

    def test_rechaza_token_expirado(self):
        with patch("services.jwt_service.time.time", return_value=1000):
            token, _ = crear_token(USUARIO, tipo="access", expires_seconds=1)

        with patch("services.jwt_service.time.time", return_value=1002):
            with self.assertRaises(TokenError):
                decodificar_token(token, tipo="access")

    def test_hash_token_no_guarda_texto_plano(self):
        token_hash = hash_token("secreto")

        self.assertNotEqual(token_hash, "secreto")
        self.assertEqual(len(token_hash), 64)


if __name__ == "__main__":
    unittest.main()
