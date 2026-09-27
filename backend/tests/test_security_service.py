import unittest
from unittest.mock import patch

from flask import Flask, request

from app import crear_app
from services.security_service import (
    _cliente_ip,
    _detalles_seguros,
    _limite_para_peticion,
    limpiar_rate_limit,
    verificar_rate_limit,
)


class SecurityServiceTest(unittest.TestCase):
    def setUp(self):
        limpiar_rate_limit()
        self.app = Flask(__name__)

        @self.app.route("/api/auth/login", endpoint="auth_bp.login", methods=["POST"])
        def login():
            return "ok"

        @self.app.route("/api/admin/panel", endpoint="admin_bp.panel_admin", methods=["GET"])
        def panel():
            return "ok"

    def tearDown(self):
        limpiar_rate_limit()

    def test_limite_auth_es_mas_estricto(self):
        with self.app.test_request_context("/api/auth/login", method="POST"):
            self.assertEqual(_limite_para_peticion(request), 10)

    def test_rate_limit_bloquea_al_superar_limite(self):
        with patch("services.security_service.Config.RATE_LIMIT_AUTH_PER_MINUTE", 2):
            with self.app.test_request_context("/api/auth/login", method="POST", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
                permitido, _ = verificar_rate_limit(request)
                self.assertTrue(permitido)
            with self.app.test_request_context("/api/auth/login", method="POST", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
                permitido, _ = verificar_rate_limit(request)
                self.assertTrue(permitido)
            with self.app.test_request_context("/api/auth/login", method="POST", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
                permitido, datos = verificar_rate_limit(request)
                self.assertFalse(permitido)
                self.assertEqual(datos["limite"], 2)

    def test_detalles_seguros_omite_secretos(self):
        with self.app.test_request_context(
            "/api/auth/login?x=1",
            method="POST",
            json={"correo": "demo@test.local", "password": "Password123", "refresh_token": "secreto"},
        ):
            detalles = _detalles_seguros(request)
            self.assertIn("correo", detalles["campos_json"])
            self.assertNotIn("password", detalles["campos_json"])
            self.assertNotIn("refresh_token", detalles["campos_json"])

    def test_no_confia_en_x_forwarded_for_sin_proxy_configurado(self):
        """Impide que un cliente altere su clave de rate limit enviando una IP falsa."""
        with patch("services.security_service.Config.TRUST_PROXY_HEADERS", False):
            with self.app.test_request_context(
                "/api/auth/login",
                headers={"X-Forwarded-For": "203.0.113.10"},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            ):
                self.assertEqual(_cliente_ip(request), "127.0.0.1")

    def test_acepta_x_forwarded_for_solo_con_proxy_confiable(self):
        """Permite conservar la IP original cuando el despliegue declara un proxy confiable."""
        with patch("services.security_service.Config.TRUST_PROXY_HEADERS", True):
            with self.app.test_request_context(
                "/api/auth/login",
                headers={"X-Forwarded-For": "203.0.113.10, 127.0.0.1"},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            ):
                self.assertEqual(_cliente_ip(request), "203.0.113.10")


class ApiSecurityIntegrationTest(unittest.TestCase):
    """Verifica los controles globales aplicados a cada respuesta de la API."""

    def setUp(self):
        limpiar_rate_limit()
        self.client = crear_app().test_client()

    def tearDown(self):
        limpiar_rate_limit()

    def test_cors_acepta_unicamente_origen_frontend_configurado(self):
        permitido = self.client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        rechazado = self.client.options(
            "/api/auth/login",
            headers={
                "Origin": "https://origen-no-confiable.example",
                "Access-Control-Request-Method": "POST",
            },
        )

        self.assertEqual(permitido.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:5173")
        self.assertIsNone(rechazado.headers.get("Access-Control-Allow-Origin"))

    def test_api_agrega_cabeceras_defensivas_en_respuesta_no_autorizada(self):
        respuesta = self.client.get("/api/auth/me")

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(respuesta.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(respuesta.headers.get("Cache-Control"), "no-store")


if __name__ == "__main__":
    unittest.main()
