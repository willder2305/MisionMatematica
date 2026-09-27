import time
import unittest

from app import crear_app
from db import obtener_conexion
from werkzeug.security import generate_password_hash


PASSWORD = "Password123"


class AuthRoutesIntegrationTest(unittest.TestCase):
    def setUp(self):
        marca = time.time_ns()
        self.correo_admin = f"admin.auth.{marca}@test.local"
        self.correo_estudiante = f"estudiante.auth.{marca}@test.local"
        self.app = crear_app()
        self.client = self.app.test_client()
        self.ids_usuario = []

    def tearDown(self):
        if not self.ids_usuario:
            return
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            for id_usuario in self.ids_usuario:
                cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _registrar(self, correo, rol):
        if rol == "administrador":
            return self._crear_administrador_controlado(correo)

        respuesta = self.client.post("/api/auth/register", json={
            "nombres": "QA",
            "apellidos": rol.title(),
            "correo": correo,
            "password": PASSWORD,
            "rol": rol,
        })
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 201, payload)
        self.ids_usuario.append(payload["data"]["usuario"]["id_usuario"])
        return payload["data"]

    def _crear_administrador_controlado(self, correo):
        """Prepara un administrador de integración sin abrir el registro público."""
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'administrador'")
            rol = cursor.fetchone()
            self.assertIsNotNone(rol)
            cursor.execute(
                """
                INSERT INTO usuarios (nombres, apellidos, correo, password_hash, id_rol, estado, correo_verificado, onboarding_completado)
                VALUES ('QA', 'Administrador', %s, %s, %s, 'activo', 1, 1)
                """,
                (correo, generate_password_hash(PASSWORD), rol["id_rol"]),
            )
            self.ids_usuario.append(cursor.lastrowid)
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

        respuesta = self.client.post("/api/auth/login", json={"correo": correo, "password": PASSWORD})
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 200, payload)
        return payload["data"]

    def _auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_auth_me_valido_e_invalido(self):
        sesion = self._registrar(self.correo_admin, "administrador")

        valido = self.client.get("/api/auth/me", headers=self._auth_headers(sesion["access_token"]))
        invalido = self.client.get("/api/auth/me")

        self.assertEqual(valido.status_code, 200, valido.get_json())
        self.assertEqual(valido.get_json()["data"]["usuario"]["rol"], "administrador")
        self.assertEqual(invalido.status_code, 401, invalido.get_json())

    def test_registro_publico_rechaza_rol_administrador(self):
        """La API no permite elevar privilegios indicando el rol en el formulario."""
        respuesta = self.client.post("/api/auth/register", json={
            "nombres": "Intento",
            "apellidos": "Elevación",
            "correo": self.correo_admin,
            "password": PASSWORD,
            "rol": "administrador",
        })

        self.assertEqual(respuesta.status_code, 400, respuesta.get_json())
        self.assertIn("rol", respuesta.get_json()["errors"])

    def test_login_no_interpreta_el_correo_como_sql(self):
        """Una cadena de inyección no debe autenticar ni revelar datos de cuenta."""
        respuesta = self.client.post("/api/auth/login", json={
            "correo": "' OR 1=1 -- ",
            "password": "cualquier-valor",
        })

        self.assertEqual(respuesta.status_code, 401, respuesta.get_json())
        self.assertEqual(respuesta.get_json()["message"], "Correo o contraseña inválidos.")

    def test_refresh_valido_e_invalido(self):
        sesion = self._registrar(self.correo_admin, "administrador")

        refresh_valido = self.client.post("/api/auth/refresh", json={"refresh_token": sesion["refresh_token"]})
        refresh_invalido = self.client.post("/api/auth/refresh", json={"refresh_token": "token-invalido"})

        self.assertEqual(refresh_valido.status_code, 200, refresh_valido.get_json())
        self.assertIn("access_token", refresh_valido.get_json()["data"])
        self.assertIn("refresh_token", refresh_valido.get_json()["data"])
        self.assertEqual(refresh_invalido.status_code, 401, refresh_invalido.get_json())

    def test_admin_accede_a_modulos_protegidos(self):
        sesion = self._registrar(self.correo_admin, "administrador")
        headers = self._auth_headers(sesion["access_token"])

        rutas = (
            "/api/plantillas",
            "/api/admin/reportes/filtros",
            "/api/admin/reportes/institucional",
            "/api/asignaciones",
            "/api/asignaciones/contexto",
        )

        for ruta in rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta, headers=headers)
                self.assertEqual(respuesta.status_code, 200, respuesta.get_json())

    def test_403_no_invalida_sesion(self):
        sesion = self._registrar(self.correo_estudiante, "estudiante")
        headers = self._auth_headers(sesion["access_token"])

        rutas_prohibidas = (
            "/api/admin/panel",
            "/api/docente/reportes/agente/exportar/pdf",
            "/api/admin/reportes/institucional/exportar/xlsx",
        )
        me = self.client.get("/api/auth/me", headers=headers)

        for ruta in rutas_prohibidas:
            with self.subTest(ruta=ruta):
                prohibido = self.client.get(ruta, headers=headers)
                self.assertEqual(prohibido.status_code, 403, prohibido.get_json())
        self.assertEqual(me.status_code, 200, me.get_json())

    def test_404_no_invalida_sesion(self):
        sesion = self._registrar(self.correo_admin, "administrador")
        headers = self._auth_headers(sesion["access_token"])

        no_existe = self.client.get("/api/ruta-inexistente", headers=headers)
        me = self.client.get("/api/auth/me", headers=headers)

        self.assertEqual(no_existe.status_code, 404)
        self.assertEqual(me.status_code, 200, me.get_json())


if __name__ == "__main__":
    unittest.main()
