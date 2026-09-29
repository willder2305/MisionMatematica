import time
import unittest
from uuid import uuid4

from app import crear_app
from db import obtener_conexion


PASSWORD = "Password123"


class AsignacionesMultitemaIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = crear_app()
        self.client = self.app.test_client()
        self.id_usuario = None
        self.asignacion = self._buscar_asignacion_multitema()
        if not self.asignacion:
            self.skipTest("No existe una asignación activa con al menos dos temas para la prueba de integración.")

    def tearDown(self):
        if not self.id_usuario:
            return
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_partida FROM partidas_juego WHERE id_usuario = %s", (self.id_usuario,))
            partidas = [fila["id_partida"] for fila in cursor.fetchall()]
            for id_partida in partidas:
                cursor.execute("UPDATE partidas_juego SET id_ejercicio_generado_actual = NULL WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM decisiones_agente WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM intentos_juego WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM ejercicios_generados WHERE id_partida = %s", (id_partida,))
            cursor.execute("DELETE FROM partidas_juego WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_asignacion_tema_estudiante WHERE id_estudiante = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_tema_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_personal_tema WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM progreso_personal_catalogo WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM estudiante_asignaciones WHERE id_estudiante = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM movimientos_monedas WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM usuario_items WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM preferencias_estudiante WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM monederos WHERE id_usuario = %s", (self.id_usuario,))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (self.id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _buscar_asignacion_multitema(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT a.id_asignacion, a.id_institucion_grado, a.id_seccion,
                       ig.id_institucion, ig.id_grado_base
                FROM asignaciones a
                INNER JOIN institucion_grados ig ON ig.id_institucion_grado = a.id_institucion_grado
                INNER JOIN asignacion_temas at ON at.id_asignacion = a.id_asignacion AND at.estado = 'activo'
                WHERE a.estado = 'activa'
                  AND a.fecha_inicio <= CURRENT_TIMESTAMP
                  AND (a.fecha_limite IS NULL OR a.fecha_limite >= CURRENT_TIMESTAMP)
                GROUP BY a.id_asignacion, a.id_institucion_grado, a.id_seccion, ig.id_institucion, ig.id_grado_base
                HAVING COUNT(*) >= 2
                ORDER BY a.id_asignacion DESC
                LIMIT 1
                """
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    def _registrar_estudiante(self):
        respuesta = self.client.post(
            "/api/auth/register",
            json={
                "nombres": "QA",
                "apellidos": "Multitema",
                "correo": f"multitema.{time.time_ns()}@test.local",
                "password": PASSWORD,
                "rol": "estudiante",
            },
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.get_json())
        payload = respuesta.get_json()["data"]
        self.id_usuario = payload["usuario"]["id_usuario"]
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO perfiles_estudiante
                    (id_usuario, id_grado, id_institucion, id_institucion_grado, id_seccion, modalidad, personaje)
                VALUES (%s, %s, %s, %s, %s, 'grupo_educativo', 'femenino')
                """,
                (
                    self.id_usuario,
                    self.asignacion["id_grado_base"],
                    self.asignacion["id_institucion"],
                    self.asignacion["id_institucion_grado"],
                    self.asignacion["id_seccion"],
                ),
            )
            cursor.execute("UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s", (self.id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()
        return {"Authorization": f"Bearer {payload['access_token']}"}

    def _tema_actual(self, partida):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT eg.id_tema
                FROM partidas_juego p
                INNER JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = p.id_ejercicio_generado_actual
                WHERE p.id_partida = %s
                """,
                (partida["id_partida"],),
            )
            return cursor.fetchone()["id_tema"]
        finally:
            cursor.close()
            conexion.close()

    def _respuesta_correcta(self, partida):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT respuesta_correcta FROM ejercicios_generados WHERE id_ejercicio_generado = %s",
                (partida["id_ejercicio_generado_actual"],),
            )
            return cursor.fetchone()["respuesta_correcta"]
        finally:
            cursor.close()
            conexion.close()

    def _puntuacion_por_tema(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT id_tema, puntos_acumulados, aciertos_puntuados
                FROM progreso_tema_estudiante
                WHERE id_usuario = %s
                ORDER BY id_tema
                """,
                (self.id_usuario,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    def test_lista_y_juego_respetan_el_plan_multitema(self):
        headers = self._registrar_estudiante()
        listado = self.client.get("/api/estudiante/asignaciones", headers=headers)
        self.assertEqual(listado.status_code, 200, listado.get_json())
        actividad = next(item for item in listado.get_json()["data"] if item["id_asignacion"] == self.asignacion["id_asignacion"])
        temas_asignados = {tema["id_tema"] for tema in actividad["temas"]}
        self.assertGreaterEqual(len(temas_asignados), 2)
        self.assertEqual(actividad["progreso_correctas"], 0)

        inicio = self.client.post(
            "/api/juego/partidas",
            headers=headers,
            json={
                "id_asignacion": self.asignacion["id_asignacion"],
                "id_tema": -1,
                "request_id": str(uuid4()),
            },
        )
        self.assertEqual(inicio.status_code, 201, inicio.get_json())
        partida = inicio.get_json()["data"]["partida"]
        primer_tema = self._tema_actual(partida)
        self.assertIn(primer_tema, temas_asignados)

        incorrecta = self.client.post(
            f"/api/juego/partidas/{partida['id_partida']}/respuesta",
            headers=headers,
            json={
                "id_ejercicio_generado": partida["id_ejercicio_generado_actual"],
                "respuesta": "respuesta incorrecta",
                "request_id": str(uuid4()),
                "tiempo_respuesta_ms": 1000,
            },
        )
        self.assertEqual(incorrecta.status_code, 200, incorrecta.get_json())
        partida = incorrecta.get_json()["data"]["partida"]
        self.assertEqual(partida["total_correctos"], 0)
        self.assertEqual(self._tema_actual(partida), primer_tema)
        self.assertEqual(sum(fila["puntos_acumulados"] for fila in self._puntuacion_por_tema()), 0)

        request_id_acierto = str(uuid4())
        acierto = self.client.post(
            f"/api/juego/partidas/{partida['id_partida']}/respuesta",
            headers=headers,
            json={
                "id_ejercicio_generado": partida["id_ejercicio_generado_actual"],
                "respuesta": self._respuesta_correcta(partida),
                "request_id": request_id_acierto,
                "tiempo_respuesta_ms": 1000,
            },
        )
        self.assertEqual(acierto.status_code, 200, acierto.get_json())
        partida = acierto.get_json()["data"]["partida"]
        self.assertEqual(partida["total_correctos"], 1)
        self.assertIn(self._tema_actual(partida), temas_asignados)
        self.assertEqual(sum(fila["puntos_acumulados"] for fila in self._puntuacion_por_tema()), 2)

        # Repetir la misma solicitud no inserta otro intento ni vuelve a acreditar puntos.
        repetida = self.client.post(
            f"/api/juego/partidas/{partida['id_partida']}/respuesta",
            headers=headers,
            json={
                "id_ejercicio_generado": acierto.get_json()["data"]["partida"].get("id_ejercicio_generado_actual"),
                "respuesta": self._respuesta_correcta(partida),
                "request_id": request_id_acierto,
                "tiempo_respuesta_ms": 1000,
            },
        )
        self.assertEqual(repetida.status_code, 200, repetida.get_json())
        self.assertEqual(sum(fila["puntos_acumulados"] for fila in self._puntuacion_por_tema()), 2)

        salida = self.client.post(f"/api/juego/partidas/{partida['id_partida']}/salir", headers=headers)
        self.assertEqual(salida.status_code, 200, salida.get_json())
        reanudar = self.client.post(
            "/api/juego/partidas",
            headers=headers,
            json={"id_asignacion": self.asignacion["id_asignacion"], "request_id": str(uuid4())},
        )
        self.assertEqual(reanudar.status_code, 201, reanudar.get_json())
        partida_reanudada = reanudar.get_json()["data"]["partida"]
        self.assertEqual(partida_reanudada["total_correctos"], 1)
        self.assertIn(self._tema_actual(partida_reanudada), temas_asignados)

        for total_esperado in range(2, 11):
            respuesta = self.client.post(
                f"/api/juego/partidas/{partida_reanudada['id_partida']}/respuesta",
                headers=headers,
                json={
                    "id_ejercicio_generado": partida_reanudada["id_ejercicio_generado_actual"],
                    "respuesta": self._respuesta_correcta(partida_reanudada),
                    "request_id": str(uuid4()),
                    "tiempo_respuesta_ms": 1000,
                },
            )
            self.assertEqual(respuesta.status_code, 200, respuesta.get_json())
            partida_reanudada = respuesta.get_json()["data"]["partida"]
            self.assertEqual(partida_reanudada["total_correctos"], total_esperado)

        pendientes = self.client.get("/api/estudiante/asignaciones", headers=headers)
        self.assertEqual(pendientes.status_code, 200, pendientes.get_json())
        self.assertFalse(any(item["id_asignacion"] == self.asignacion["id_asignacion"] for item in pendientes.get_json()["data"]))
        puntuaciones = self._puntuacion_por_tema()
        self.assertEqual(sum(fila["aciertos_puntuados"] for fila in puntuaciones), 10)
        self.assertEqual(sum(fila["puntos_acumulados"] for fila in puntuaciones), 20)
        self.assertTrue(all(fila["id_tema"] in temas_asignados for fila in puntuaciones))


if __name__ == "__main__":
    unittest.main()
