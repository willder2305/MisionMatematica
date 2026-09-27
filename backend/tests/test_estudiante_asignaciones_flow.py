import time
import unittest
from uuid import uuid4

from app import crear_app
from db import obtener_conexion


PASSWORD = "Password123"
ID_ASIGNACION_DEMO = 6
ID_GRADO_DEMO = 1
ID_TEMA_RESTA = 7
ID_INSTITUCION_GRADO_DEMO = 1
ID_SECCION_DEMO = 2


class EstudianteAsignacionesFlowTest(unittest.TestCase):
    def setUp(self):
        self.app = crear_app()
        self.client = self.app.test_client()
        self.ids_usuario = []
        self._asegurar_asignacion_demo_activa()

    def tearDown(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            for id_usuario in self.ids_usuario:
                cursor.execute("SELECT id_partida FROM partidas_juego WHERE id_usuario = %s", (id_usuario,))
                partidas = [fila["id_partida"] for fila in cursor.fetchall()]
                for id_partida in partidas:
                    cursor.execute(
                        """
                        UPDATE partidas_juego
                        SET id_ejercicio_actual = NULL,
                            id_ejercicio_generado_actual = NULL
                        WHERE id_partida = %s
                        """,
                        (id_partida,),
                    )
                    cursor.execute("DELETE FROM decisiones_agente WHERE id_partida = %s", (id_partida,))
                    cursor.execute("DELETE FROM intentos_juego WHERE id_partida = %s", (id_partida,))
                    cursor.execute("DELETE FROM ejercicios_generados WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM estudiante_asignaciones WHERE id_estudiante = %s", (id_usuario,))
                for id_partida in partidas:
                    cursor.execute("DELETE FROM partidas_juego WHERE id_partida = %s", (id_partida,))
                cursor.execute("DELETE FROM progreso_asignacion_tema_estudiante WHERE id_estudiante = %s", (id_usuario,))
                cursor.execute("DELETE FROM progreso_personal_tema WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM progreso_personal_catalogo WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM movimientos_monedas WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM usuario_items WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM preferencias_estudiante WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM monederos WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _asegurar_asignacion_demo_activa(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE asignaciones
                SET estado = 'activa',
                    fecha_inicio = CURRENT_TIMESTAMP - INTERVAL 1 DAY,
                    fecha_limite = CURRENT_TIMESTAMP + INTERVAL 30 DAY
                WHERE id_asignacion = %s
                """,
                (ID_ASIGNACION_DEMO,),
            )
            cursor.execute(
                """
                INSERT INTO asignacion_temas (id_asignacion, id_tema, estado, fecha_fin)
                VALUES (%s, %s, 'activo', NULL)
                ON DUPLICATE KEY UPDATE estado = 'activo', fecha_fin = NULL
                """,
                (ID_ASIGNACION_DEMO, ID_TEMA_RESTA),
            )
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _registrar_estudiante(self, sufijo):
        respuesta = self.client.post("/api/auth/register", json={
            "nombres": "QA",
            "apellidos": "Estudiante",
            "correo": f"actividad.{sufijo}.{time.time_ns()}@test.local",
            "password": PASSWORD,
            "rol": "estudiante",
        })
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 201, payload)
        id_usuario = payload["data"]["usuario"]["id_usuario"]
        self.ids_usuario.append(id_usuario)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO perfiles_estudiante
                    (id_usuario, id_grado, id_institucion, id_institucion_grado, id_seccion, modalidad, personaje)
                VALUES (%s, %s, 1, %s, %s, 'grupo_educativo', 'femenino')
                """,
                (id_usuario, ID_GRADO_DEMO, ID_INSTITUCION_GRADO_DEMO, ID_SECCION_DEMO),
            )
            cursor.execute("UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s", (id_usuario,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

        return id_usuario, {"Authorization": f"Bearer {payload['data']['access_token']}"}

    def _listar_actividades(self, headers):
        respuesta = self.client.get("/api/estudiante/asignaciones", headers=headers)
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 200, payload)
        return payload["data"]

    def _iniciar_partida(self, headers, request_id=None):
        respuesta = self.client.post(
            "/api/juego/partidas",
            headers=headers,
            json={
                "personaje": "femenino",
                "id_asignacion": ID_ASIGNACION_DEMO,
                "id_grado": ID_GRADO_DEMO,
                "id_tema": ID_TEMA_RESTA,
                "request_id": request_id or str(uuid4()),
            },
        )
        payload = respuesta.get_json()
        self.assertIn(respuesta.status_code, (200, 201), payload)
        return respuesta.status_code, payload["data"]["partida"]

    def _respuesta_correcta_actual(self, id_partida):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT eg.respuesta_correcta
                FROM partidas_juego p
                INNER JOIN ejercicios_generados eg
                    ON eg.id_ejercicio_generado = p.id_ejercicio_generado_actual
                WHERE p.id_partida = %s
                """,
                (id_partida,),
            )
            return cursor.fetchone()["respuesta_correcta"]
        finally:
            cursor.close()
            conexion.close()

    def _responder(self, headers, partida, respuesta, request_id=None):
        payload = {
            "id_ejercicio": partida.get("id_ejercicio_actual"),
            "id_ejercicio_generado": partida.get("id_ejercicio_generado_actual"),
            "respuesta": respuesta,
            "request_id": request_id or str(uuid4()),
            "tiempo_respuesta_ms": 1000,
        }
        respuesta_http = self.client.post(
            f"/api/juego/partidas/{partida['id_partida']}/respuesta",
            headers=headers,
            json=payload,
        )
        data = respuesta_http.get_json()
        self.assertEqual(respuesta_http.status_code, 200, data)
        return payload, data["data"]["partida"]

    def _contar_intentos(self, id_partida):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM intentos_juego WHERE id_partida = %s", (id_partida,))
            return cursor.fetchone()["total"]
        finally:
            cursor.close()
            conexion.close()

    def _progreso(self, id_usuario):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT *
                FROM estudiante_asignaciones
                WHERE id_asignacion = %s
                  AND id_estudiante = %s
                """,
                (ID_ASIGNACION_DEMO, id_usuario),
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

    def test_reintentos_y_completado_son_por_estudiante(self):
        id_estudiante_a, headers_a = self._registrar_estudiante("a")
        id_estudiante_b, headers_b = self._registrar_estudiante("b")

        pendientes_a = self._listar_actividades(headers_a)
        self.assertTrue(any(item["id_asignacion"] == ID_ASIGNACION_DEMO for item in pendientes_a))
        self.assertEqual(self._progreso(id_estudiante_a)["estado"], "pendiente")

        _, partida_1 = self._iniciar_partida(headers_a)
        self.assertEqual(partida_1["casilla_actual"], 0)
        self.assertEqual(partida_1["vidas_restantes"], 5)
        self.assertEqual(self._progreso(id_estudiante_a)["estado"], "en_progreso")

        salir = self.client.post(f"/api/juego/partidas/{partida_1['id_partida']}/salir", headers=headers_a)
        self.assertEqual(salir.status_code, 200, salir.get_json())
        self.assertEqual(self._progreso(id_estudiante_a)["estado"], "en_progreso")
        self.assertTrue(any(item["id_asignacion"] == ID_ASIGNACION_DEMO for item in self._listar_actividades(headers_a)))

        _, partida_2 = self._iniciar_partida(headers_a)
        self.assertNotEqual(partida_1["id_partida"], partida_2["id_partida"])
        self.assertNotEqual(partida_1["mapa"], partida_2["mapa"])
        for _ in range(5):
            _, partida_2 = self._responder(headers_a, partida_2, "respuesta-incorrecta")
        self.assertEqual(partida_2["estado"], "sin_vidas")
        self.assertEqual(self._progreso(id_estudiante_a)["estado"], "en_progreso")
        self.assertTrue(any(item["id_asignacion"] == ID_ASIGNACION_DEMO for item in self._listar_actividades(headers_a)))

        _, partida_3 = self._iniciar_partida(headers_a)
        payload_final = None
        request_id_final = str(uuid4())
        for indice in range(10):
            correcta = self._respuesta_correcta_actual(partida_3["id_partida"])
            payload_final, partida_3 = self._responder(
                headers_a,
                partida_3,
                correcta,
                request_id=request_id_final if indice == 9 else None,
            )
        self.assertEqual(partida_3["casilla_actual"], 10)
        self.assertEqual(partida_3["total_correctos"], 10)
        self.assertEqual(partida_3["estado"], "completada")
        intentos_antes = self._contar_intentos(partida_3["id_partida"])
        repetida = self.client.post(
            f"/api/juego/partidas/{partida_3['id_partida']}/respuesta",
            headers=headers_a,
            json=payload_final,
        )
        self.assertEqual(repetida.status_code, 200, repetida.get_json())
        self.assertEqual(self._contar_intentos(partida_3["id_partida"]), intentos_antes)
        progreso_a = self._progreso(id_estudiante_a)
        self.assertEqual(progreso_a["estado"], "completada")
        self.assertEqual(progreso_a["cantidad_intentos"], 3)
        self.assertFalse(any(item["id_asignacion"] == ID_ASIGNACION_DEMO for item in self._listar_actividades(headers_a)))
        self.assertTrue(any(item["id_asignacion"] == ID_ASIGNACION_DEMO for item in self._listar_actividades(headers_b)))
        self.assertEqual(self._progreso(id_estudiante_b)["estado"], "pendiente")

    def test_inicio_partida_es_idempotente_por_request_id(self):
        _, headers = self._registrar_estudiante("idempotente")
        request_id = str(uuid4())

        estado_1, partida_1 = self._iniciar_partida(headers, request_id=request_id)
        estado_2, partida_2 = self._iniciar_partida(headers, request_id=request_id)

        self.assertEqual(estado_1, 201)
        self.assertEqual(estado_2, 200)
        self.assertEqual(partida_1["id_partida"], partida_2["id_partida"])


if __name__ == "__main__":
    unittest.main()
