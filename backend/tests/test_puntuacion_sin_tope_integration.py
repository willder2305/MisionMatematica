import time
import unittest
from uuid import uuid4

from app import crear_app
from db import obtener_conexion
from services.puntuaciones_service import _puntuacion_usuario


class PuntuacionSinTopeIntegrationTest(unittest.TestCase):
    """Recorre cinco partidas reales para impedir regresiones alrededor de 56 puntos."""

    def setUp(self):
        self.app = crear_app()
        self.client = self.app.test_client()
        self.id_usuario = None
        self.id_tema_suma = None
        self.headers = None

    def tearDown(self):
        if not self.id_usuario:
            return
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_partida FROM partidas_juego WHERE id_usuario = %s", (self.id_usuario,))
            for fila in cursor.fetchall():
                id_partida = fila["id_partida"]
                cursor.execute("UPDATE partidas_juego SET id_ejercicio_generado_actual = NULL WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM decisiones_agente WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM intentos_juego WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM ejercicios_generados WHERE id_partida = %s", (id_partida,))
            cursor.execute("DELETE FROM partidas_juego WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM promociones_curriculares_tema WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_tema_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_personal_tema WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_personal_catalogo WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM movimientos_monedas WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM usuario_items WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM preferencias_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM monederos WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (self.id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _preparar_estudiante(self):
        respuesta = self.client.post(
            "/api/auth/register",
            json={
                "nombres": "QA",
                "apellidos": "Puntuacion",
                "correo": f"puntuacion.{time.time_ns()}@test.local",
                "password": "Password123",
                "rol": "estudiante",
            },
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.get_json())
        datos = respuesta.get_json()["data"]
        self.id_usuario = datos["usuario"]["id_usuario"]
        self.headers = {"Authorization": f"Bearer {datos['access_token']}"}

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_grado FROM grados WHERE codigo_grado = '4P' LIMIT 1")
            grado = cursor.fetchone()["id_grado"]
            cursor.execute(
                "SELECT id_tema FROM temas WHERE id_grado = %s AND nombre_tema = 'Suma' LIMIT 1",
                (grado,),
            )
            self.id_tema_suma = cursor.fetchone()["id_tema"]
            cursor.execute(
                """
                INSERT INTO perfiles_estudiante (id_usuario, id_grado, modalidad, personaje)
                VALUES (%s, %s, 'cuenta_propia', 'masculino')
                """,
                (self.id_usuario, grado),
            )
            cursor.execute(
                """
                INSERT INTO preferencias_estudiante (id_usuario, personaje_key, modo_mapa)
                VALUES (%s, 'masculino', 'aleatorio')
                """,
                (self.id_usuario,),
            )
            cursor.execute("INSERT INTO monederos (id_usuario, saldo_monedas) VALUES (%s, 0)", (self.id_usuario,))
            cursor.execute("UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s", (self.id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _respuesta_correcta(self, id_ejercicio_generado):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT respuesta_correcta FROM ejercicios_generados WHERE id_ejercicio_generado = %s",
                (id_ejercicio_generado,),
            )
            return cursor.fetchone()["respuesta_correcta"]
        finally:
            cursor.close()
            conexion.close()

    def _puntos_suma(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            return _puntuacion_usuario(self.id_usuario, self.id_tema_suma, cursor)
        finally:
            cursor.close()
            conexion.close()

    def test_cincuenta_aciertos_acumulan_cien_puntos_sin_reiniciar_por_grado(self):
        self._preparar_estudiante()
        partida = None
        for numero in range(1, 51):
            if not partida or partida["estado"] != "en_curso":
                inicio = self.client.post(
                    "/api/juego/partidas",
                    headers=self.headers,
                    json={"id_tema": self.id_tema_suma, "request_id": str(uuid4())},
                )
                self.assertEqual(inicio.status_code, 201, inicio.get_json())
                datos_inicio = inicio.get_json()["data"]
                partida = datos_inicio["partida"]
                self.assertEqual(datos_inicio["pregunta_actual"]["tipo_respuesta"], "numerica")

            respuesta = self.client.post(
                f"/api/juego/partidas/{partida['id_partida']}/respuesta",
                headers=self.headers,
                json={
                    "id_ejercicio_generado": partida["id_ejercicio_generado_actual"],
                    "respuesta": self._respuesta_correcta(partida["id_ejercicio_generado_actual"]),
                    "request_id": str(uuid4()),
                    "tiempo_respuesta_ms": 1000,
                },
            )
            self.assertEqual(respuesta.status_code, 200, respuesta.get_json())
            partida = respuesta.get_json()["data"]["partida"]
            self.assertEqual(self._puntos_suma(), numero * 2)

        self.assertEqual(self._puntos_suma(), 100)


if __name__ == "__main__":
    unittest.main()
