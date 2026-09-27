import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion


def _query(sql, params=(), fetchone=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        resultado = cursor.fetchone() if fetchone else cursor.fetchall()
        conexion.commit()
        return resultado
    finally:
        cursor.close()
        conexion.close()


def _limpiar_partidas_usuario(cursor, id_usuario):
    cursor.execute("SELECT id_partida FROM partidas_juego WHERE id_usuario = %s", (id_usuario,))
    for partida in cursor.fetchall():
        id_partida = partida["id_partida"]
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
        cursor.execute("DELETE FROM partidas_juego WHERE id_partida = %s", (id_partida,))


def _cleanup(correos):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if correos:
            placeholders = ", ".join(["%s"] * len(correos))
            cursor.execute(f"SELECT id_usuario FROM usuarios WHERE correo IN ({placeholders})", tuple(correos))
            for usuario in cursor.fetchall():
                _limpiar_partidas_usuario(cursor, usuario["id_usuario"])

        for correo in correos:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            if not usuario:
                continue
            cursor.execute("SELECT id_grupo FROM grupos WHERE id_docente = %s", (usuario["id_usuario"],))
            for grupo in cursor.fetchall():
                cursor.execute("SELECT id_asignacion FROM asignaciones WHERE id_grupo = %s", (grupo["id_grupo"],))
                for asignacion in cursor.fetchall():
                    cursor.execute("DELETE FROM asignacion_ejercicios WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                    cursor.execute("DELETE FROM asignacion_temas WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                    cursor.execute("DELETE FROM asignaciones WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                cursor.execute("DELETE FROM estudiantes_grupos WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM pines_acceso WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM grupo_secciones WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM grupos WHERE id_grupo = %s", (grupo["id_grupo"],))
            cursor.execute("DELETE FROM estudiantes_grupos WHERE id_usuario_estudiante = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_tema_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM docente_grados WHERE id_usuario_docente = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM perfiles_docente WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (usuario["id_usuario"],))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def _registrar(client, correo, rol):
    respuesta = client.post("/api/auth/register", json={
        "nombres": "Demo",
        "apellidos": rol.title(),
        "correo": correo,
        "password": "Password123",
        "rol": rol,
    })
    payload = respuesta.get_json()
    assert respuesta.status_code == 201, payload
    return payload["data"]["access_token"], payload["data"]["usuario"]["id_usuario"]


def _ejercicio_generado(id_ejercicio_generado):
    return _query(
        """
        SELECT eg.*, n.codigo AS codigo_nivel
        FROM ejercicios_generados eg
        INNER JOIN niveles_dificultad n ON n.id_nivel = eg.id_nivel
        WHERE eg.id_ejercicio_generado = %s
        """,
        (id_ejercicio_generado,),
        fetchone=True,
    )


def _responder(client, token, id_partida, pregunta, respuesta):
    respuesta_http = client.post(
        f"/api/juego/partidas/{id_partida}/respuesta",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_ejercicio_generado": pregunta["id_ejercicio_generado"],
            "respuesta": str(respuesta),
            "request_id": str(uuid.uuid4()),
            "tiempo_respuesta_ms": 1200,
        },
    )
    payload = respuesta_http.get_json()
    assert respuesta_http.status_code == 200, payload
    return payload["data"]


def main():
    marca = int(time.time())
    correo_docente = f"reportes.docente.{marca}@test.local"
    correo_estudiante = f"reportes.estudiante.{marca}@test.local"
    _cleanup([correo_docente, correo_estudiante])

    app = crear_app()
    client = app.test_client()
    grado_tema = _query(
        """
        SELECT g.id_grado, t.id_tema
        FROM grados g
        INNER JOIN temas t ON t.id_grado = g.id_grado
        WHERE g.codigo_grado = '4P'
          AND t.nombre_tema = 'Multiplicacion'
        LIMIT 1
        """,
        fetchone=True,
    )
    nivel = _query("SELECT id_nivel FROM niveles_dificultad WHERE codigo = 'facil' LIMIT 1", fetchone=True)
    assert grado_tema and nivel, "Faltan datos base para la demo."

    try:
        token_docente, _ = _registrar(client, correo_docente, "docente")
        docente_onboarding = client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={"institucion": "Escuela Reportes", "grados": [grado_tema["id_grado"]]},
        )
        assert docente_onboarding.status_code == 200, docente_onboarding.get_json()

        grupo = client.post(
            "/api/grupos",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={"id_grado": grado_tema["id_grado"], "nombre": f"Grupo Reportes {marca}", "descripcion": "Demo"},
        )
        id_grupo = grupo.get_json()["data"]["id_grupo"]
        assert grupo.status_code == 201, grupo.get_json()

        asignacion = client.post(
            "/api/asignaciones",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={
                "id_grupo": id_grupo,
                "nombre": f"Reporte agente {marca}",
                "instrucciones": "Actividad para reporte docente.",
                "tipo": "generacion_automatica",
                "id_nivel_inicial": nivel["id_nivel"],
                "cantidad_preguntas": 5,
                "fecha_inicio": "2026-01-01T08:00",
                "fecha_limite": None,
                "obligatoria": True,
                "estado": "activa",
                "temas": [grado_tema["id_tema"]],
            },
        )
        id_asignacion = asignacion.get_json()["data"]["id_asignacion"]
        assert asignacion.status_code == 201, asignacion.get_json()

        token_estudiante, id_estudiante = _registrar(client, correo_estudiante, "estudiante")
        pin_res = client.post(f"/api/grupos/{id_grupo}/pines", headers={"Authorization": f"Bearer {token_docente}"}, json={})
        pin = pin_res.get_json()["data"]["pin"]
        ingreso = client.post("/api/pines/ingresar", headers={"Authorization": f"Bearer {token_estudiante}"}, json={"pin": pin})
        assert ingreso.status_code == 201, ingreso.get_json()
        estudiante_onboarding = client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token_estudiante}"},
            json={"modalidad": "grupo_educativo", "personaje": "masculino"},
        )
        assert estudiante_onboarding.status_code == 200, estudiante_onboarding.get_json()

        inicio = client.post(
            "/api/juego/partidas",
            headers={"Authorization": f"Bearer {token_estudiante}"},
            json={
                "personaje": "masculino",
                "mapa": "bosque",
                "id_asignacion": id_asignacion,
                "id_grado": grado_tema["id_grado"],
                "id_tema": grado_tema["id_tema"],
            },
        )
        payload_inicio = inicio.get_json()
        assert inicio.status_code == 201, payload_inicio
        id_partida = payload_inicio["data"]["partida"]["id_partida"]
        pregunta = payload_inicio["data"]["pregunta_actual"]

        for _ in range(3):
            generado = _ejercicio_generado(pregunta["id_ejercicio_generado"])
            data = _responder(client, token_estudiante, id_partida, pregunta, generado["respuesta_correcta"])
            pregunta = data["siguiente_pregunta"]

        for _ in range(2):
            generado = _ejercicio_generado(pregunta["id_ejercicio_generado"])
            respuesta_erronea = int(generado["respuesta_correcta"]) + 1
            data = _responder(client, token_estudiante, id_partida, pregunta, respuesta_erronea)
            pregunta = data["siguiente_pregunta"]

        panel = client.get("/api/docente/panel", headers={"Authorization": f"Bearer {token_docente}"})
        assert panel.status_code == 200, panel.get_json()
        assert panel.get_json()["data"]["total_estudiantes"] >= 1, panel.get_json()
        print("panel docente: OK")

        estudiantes = client.get("/api/docente/estudiantes", headers={"Authorization": f"Bearer {token_docente}"})
        payload_estudiantes = estudiantes.get_json()
        assert estudiantes.status_code == 200, payload_estudiantes
        assert any(item["id_usuario"] == id_estudiante for item in payload_estudiantes["data"]), payload_estudiantes
        print("estudiantes docente: OK")

        reporte = client.get(
            "/api/docente/reportes/agente",
            headers={"Authorization": f"Bearer {token_docente}"},
            query_string={"id_grupo": id_grupo, "id_estudiante": id_estudiante, "id_asignacion": id_asignacion},
        )
        payload_reporte = reporte.get_json()
        assert reporte.status_code == 200, payload_reporte
        assert payload_reporte["data"]["resumen"]["intentos"] == 5, payload_reporte
        assert payload_reporte["data"]["decisiones_por_accion"], payload_reporte
        print("reporte agente: OK")

        decisiones = client.get(
            "/api/docente/reportes/agente/decisiones",
            headers={"Authorization": f"Bearer {token_docente}"},
            query_string={"id_grupo": id_grupo, "id_estudiante": id_estudiante, "id_asignacion": id_asignacion},
        )
        payload_decisiones = decisiones.get_json()
        assert decisiones.status_code == 200, payload_decisiones
        assert payload_decisiones["data"]["total"] == 5, payload_decisiones
        assert payload_decisiones["data"]["decisiones"][0]["pregunta"], payload_decisiones
        print("decisiones agente: OK")
    finally:
        _cleanup([correo_docente, correo_estudiante])


if __name__ == "__main__":
    main()
