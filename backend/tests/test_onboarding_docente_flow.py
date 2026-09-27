import time
import unittest

from app import crear_app
from db import obtener_conexion
from services.security_service import limpiar_rate_limit


PASSWORD = "Password123"


class OnboardingDocenteFlowTest(unittest.TestCase):
    def setUp(self):
        limpiar_rate_limit()
        self.app = crear_app()
        self.client = self.app.test_client()
        self.ids_usuario = []
        self.ids_institucion = []
        self.marca = time.time_ns()

    def tearDown(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            for id_usuario in self.ids_usuario:
                cursor.execute("SELECT id_grupo FROM grupos WHERE id_docente = %s", (id_usuario,))
                ids_grupo = [fila["id_grupo"] for fila in cursor.fetchall()]
                if ids_grupo:
                    formato = ",".join(["%s"] * len(ids_grupo))
                    cursor.execute(f"DELETE FROM pines_acceso WHERE id_grupo IN ({formato})", tuple(ids_grupo))
                    cursor.execute(f"DELETE FROM grupo_secciones WHERE id_grupo IN ({formato})", tuple(ids_grupo))
                    cursor.execute(f"DELETE FROM grupos WHERE id_grupo IN ({formato})", tuple(ids_grupo))
                cursor.execute("DELETE FROM docente_secciones WHERE id_docente = %s", (id_usuario,))
                cursor.execute("DELETE FROM docente_grados WHERE id_usuario_docente = %s", (id_usuario,))
                cursor.execute("DELETE FROM perfiles_docente WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))

            for id_institucion in self.ids_institucion:
                cursor.execute(
                    """
                    SELECT s.id_seccion
                    FROM secciones s
                    INNER JOIN institucion_grados ig ON ig.id_institucion_grado = s.id_institucion_grado
                    WHERE ig.id_institucion = %s
                    """,
                    (id_institucion,),
                )
                ids_seccion = [fila["id_seccion"] for fila in cursor.fetchall()]
                if ids_seccion:
                    formato = ",".join(["%s"] * len(ids_seccion))
                    cursor.execute(f"DELETE FROM pines_acceso WHERE id_seccion IN ({formato})", tuple(ids_seccion))
                    cursor.execute(f"DELETE FROM grupo_secciones WHERE id_seccion IN ({formato})", tuple(ids_seccion))
                    cursor.execute(f"DELETE FROM docente_secciones WHERE id_seccion IN ({formato})", tuple(ids_seccion))
                    cursor.execute(f"DELETE FROM secciones WHERE id_seccion IN ({formato})", tuple(ids_seccion))
                cursor.execute("DELETE FROM institucion_grados WHERE id_institucion = %s", (id_institucion,))
                cursor.execute("DELETE FROM instituciones WHERE id_institucion = %s", (id_institucion,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    def _headers_docente(self, sufijo="docente"):
        respuesta = self.client.post("/api/auth/register", json={
            "nombres": "QA",
            "apellidos": "Docente",
            "correo": f"onboarding.{sufijo}.{self.marca}@test.local",
            "password": PASSWORD,
            "rol": "docente",
        })
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 201, payload)
        self.ids_usuario.append(payload["data"]["usuario"]["id_usuario"])
        return {"Authorization": f"Bearer {payload['data']['access_token']}"}, payload["data"]["usuario"]["id_usuario"]

    def _id_grados_base(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT codigo_grado, id_grado FROM grados WHERE codigo_grado IN ('4P','5P','6P')")
            return {fila["codigo_grado"]: fila["id_grado"] for fila in cursor.fetchall()}
        finally:
            cursor.close()
            conexion.close()

    def _crear_institucion(self, headers, nombre):
        respuesta = self.client.post("/api/instituciones", headers=headers, json={"nombre": nombre})
        payload = respuesta.get_json()
        self.assertEqual(respuesta.status_code, 201, payload)
        id_institucion = payload["data"]["id_institucion"]
        if id_institucion not in self.ids_institucion:
            self.ids_institucion.append(id_institucion)
        return payload["data"]

    def _conteos_docente(self, id_usuario):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM docente_grados
                WHERE id_usuario_docente = %s AND estado = 'activo'
                """,
                (id_usuario,),
            )
            grados = cursor.fetchone()["total"]
            cursor.execute(
                """
                SELECT s.nombre_seccion
                FROM docente_secciones ds
                INNER JOIN secciones s ON s.id_seccion = ds.id_seccion
                WHERE ds.id_docente = %s AND ds.estado = 'activo'
                ORDER BY s.nombre_seccion
                """,
                (id_usuario,),
            )
            secciones = [fila["nombre_seccion"] for fila in cursor.fetchall()]
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM pines_acceso p
                INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
                WHERE gr.id_docente = %s AND p.estado = 'activo'
                """,
                (id_usuario,),
            )
            pines = cursor.fetchone()["total"]
            return grados, secciones, pines
        finally:
            cursor.close()
            conexion.close()

    def test_buscar_crear_y_reutilizar_institucion(self):
        headers, _ = self._headers_docente("buscar")
        nombre = f"Colegio Prueba Onboarding {self.marca}"

        vacia = self.client.get("/api/instituciones", headers=headers)
        self.assertEqual(vacia.status_code, 200, vacia.get_json())

        creada = self._crear_institucion(headers, nombre)
        reutilizada = self._crear_institucion(headers, f"  {nombre.upper()}  ")
        self.assertEqual(creada["id_institucion"], reutilizada["id_institucion"])

        busqueda = self.client.get("/api/instituciones", headers=headers, query_string={"q": "prueba onboarding"})
        self.assertEqual(busqueda.status_code, 200, busqueda.get_json())
        self.assertTrue(any(item["id_institucion"] == creada["id_institucion"] for item in busqueda.get_json()["data"]))

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM institucion_grados WHERE id_institucion = %s", (creada["id_institucion"],))
            self.assertEqual(cursor.fetchone()["total"], 3)
        finally:
            cursor.close()
            conexion.close()

    def test_onboarding_docente_a_b_c_d_e_idempotencia(self):
        headers, id_docente = self._headers_docente("abcd")
        institucion = self._crear_institucion(headers, f"Colegio Docente ABCD {self.marca}")
        grados = self._id_grados_base()
        payload = {
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"], grados["5P"], grados["6P"]],
            "secciones_por_grado": {
                str(grados["4P"]): ["A", "B"],
                str(grados["5P"]): ["C"],
                str(grados["6P"]): ["D"],
            },
        }

        primera = self.client.post("/api/onboarding", headers=headers, json=payload)
        segunda = self.client.post("/api/onboarding", headers=headers, json=payload)

        self.assertEqual(primera.status_code, 200, primera.get_json())
        self.assertEqual(segunda.status_code, 200, segunda.get_json())
        grados_total, secciones, pines = self._conteos_docente(id_docente)
        self.assertEqual(grados_total, 3)
        self.assertEqual(secciones, ["A", "B", "C", "D"])
        self.assertEqual(pines, 4)

    def test_onboarding_docente_crea_unica_si_no_hay_secciones(self):
        headers, id_docente = self._headers_docente("unica")
        institucion = self._crear_institucion(headers, f"Colegio Docente Unica {self.marca}")
        grados = self._id_grados_base()
        payload = {
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): []},
        }

        respuesta = self.client.post("/api/onboarding", headers=headers, json=payload)

        self.assertEqual(respuesta.status_code, 200, respuesta.get_json())
        grados_total, secciones, pines = self._conteos_docente(id_docente)
        self.assertEqual(grados_total, 1)
        self.assertEqual(secciones, ["Única"])
        self.assertEqual(pines, 1)

    def test_exclusividad_docente_seccion_misma_institucion(self):
        headers_juan, _ = self._headers_docente("exclusivo.juan")
        headers_maria, id_maria = self._headers_docente("exclusivo.maria")
        institucion = self._crear_institucion(headers_juan, f"Colegio Exclusivo {self.marca}")
        grados = self._id_grados_base()

        primera = self.client.post("/api/onboarding", headers=headers_juan, json={
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["A"]},
        })
        conflicto = self.client.post("/api/onboarding", headers=headers_maria, json={
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["A"]},
        })
        disponible = self.client.post("/api/onboarding", headers=headers_maria, json={
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["B"]},
        })

        self.assertEqual(primera.status_code, 200, primera.get_json())
        self.assertEqual(conflicto.status_code, 409, conflicto.get_json())
        self.assertIn("ya está asignada", conflicto.get_json()["message"])
        self.assertEqual(disponible.status_code, 200, disponible.get_json())
        _, secciones_maria, _ = self._conteos_docente(id_maria)
        self.assertEqual(secciones_maria, ["B"])

    def test_exclusividad_permite_misma_seccion_en_otra_institucion_y_bloquea_unica(self):
        headers_juan, _ = self._headers_docente("exclusivo.unica.juan")
        headers_maria, _ = self._headers_docente("exclusivo.unica.maria")
        inst_uno = self._crear_institucion(headers_juan, f"Colegio Unica Uno {self.marca}")
        inst_dos = self._crear_institucion(headers_maria, f"Colegio Unica Dos {self.marca}")
        grados = self._id_grados_base()

        base = self.client.post("/api/onboarding", headers=headers_juan, json={
            "id_institucion": inst_uno["id_institucion"],
            "grados": [grados["5P"]],
            "secciones_por_grado": {str(grados["5P"]): []},
        })
        conflicto_unica = self.client.post("/api/onboarding", headers=headers_maria, json={
            "id_institucion": inst_uno["id_institucion"],
            "grados": [grados["5P"]],
            "secciones_por_grado": {str(grados["5P"]): []},
        })
        otra_institucion = self.client.post("/api/onboarding", headers=headers_maria, json={
            "id_institucion": inst_dos["id_institucion"],
            "grados": [grados["5P"]],
            "secciones_por_grado": {str(grados["5P"]): []},
        })

        self.assertEqual(base.status_code, 200, base.get_json())
        self.assertEqual(conflicto_unica.status_code, 409, conflicto_unica.get_json())
        self.assertIn("Única", conflicto_unica.get_json()["message"])
        self.assertEqual(otra_institucion.status_code, 200, otra_institucion.get_json())

    def test_onboarding_docente_rechaza_payload_invalido(self):
        headers, _ = self._headers_docente("invalidos")
        institucion = self._crear_institucion(headers, f"Colegio Docente Invalidos {self.marca}")
        grados = self._id_grados_base()

        seccion_e = self.client.post("/api/onboarding", headers=headers, json={
            "id_institucion": institucion["id_institucion"],
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["E"]},
        })
        sin_institucion = self.client.post("/api/onboarding", headers=headers, json={
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["A"]},
        })
        inexistente = self.client.post("/api/onboarding", headers=headers, json={
            "id_institucion": 99999999,
            "grados": [grados["4P"]],
            "secciones_por_grado": {str(grados["4P"]): ["A"]},
        })

        self.assertEqual(seccion_e.status_code, 400, seccion_e.get_json())
        self.assertEqual(sin_institucion.status_code, 400, sin_institucion.get_json())
        self.assertEqual(inexistente.status_code, 404, inexistente.get_json())


if __name__ == "__main__":
    unittest.main()
