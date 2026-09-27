import uuid
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion


def _cleanup_usuario(correo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        if usuario:
            cursor.execute("SELECT id_partida FROM partidas_juego WHERE id_usuario = %s", (usuario["id_usuario"],))
            for partida in cursor.fetchall():
                cursor.execute(
                    """
                    UPDATE partidas_juego
                    SET id_ejercicio_actual = NULL,
                        id_ejercicio_generado_actual = NULL
                    WHERE id_partida = %s
                    """,
                    (partida["id_partida"],),
                )
                cursor.execute("DELETE FROM decisiones_agente WHERE id_partida = %s", (partida["id_partida"],))
                cursor.execute("DELETE FROM intentos_juego WHERE id_partida = %s", (partida["id_partida"],))
                cursor.execute("DELETE FROM ejercicios_generados WHERE id_partida = %s", (partida["id_partida"],))
                cursor.execute("DELETE FROM partidas_juego WHERE id_partida = %s", (partida["id_partida"],))
            cursor.execute("DELETE FROM movimientos_monedas WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM usuario_items WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM preferencias_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM monederos WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_asignacion_tema_estudiante WHERE id_estudiante = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_personal_tema WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_personal_catalogo WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM progreso_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM estudiantes_grupos WHERE id_usuario_estudiante = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (usuario["id_usuario"],))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def _fetchone(sql, params=()):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


def _fetchall(sql, params=()):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def _cleanup(id_partida):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE partidas_juego
            SET id_ejercicio_actual = NULL,
                id_ejercicio_generado_actual = NULL
            WHERE id_partida = %s
            """,
            (id_partida,),
        )
        cursor.execute(
            "DELETE FROM decisiones_agente WHERE id_partida = %s",
            (id_partida,),
        )
        cursor.execute(
            "DELETE FROM intentos_juego WHERE id_partida = %s",
            (id_partida,),
        )
        cursor.execute(
            "DELETE FROM ejercicios_generados WHERE id_partida = %s",
            (id_partida,),
        )
        cursor.execute(
            "DELETE FROM partidas_juego WHERE id_partida = %s",
            (id_partida,),
        )
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def _ejercicio_generado(id_ejercicio_generado):
    return _fetchone(
        """
        SELECT eg.*, p.nombre AS nombre_plantilla, n.codigo AS codigo_nivel
        FROM ejercicios_generados eg
        INNER JOIN plantillas_ejercicios p ON p.id_plantilla = eg.id_plantilla
        INNER JOIN niveles_dificultad n ON n.id_nivel = eg.id_nivel
        WHERE eg.id_ejercicio_generado = %s
        """,
        (id_ejercicio_generado,),
    )


def _responder(client, token, id_partida, pregunta, respuesta):
    respuesta_http = client.post(
        f"/api/juego/partidas/{id_partida}/respuesta",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_ejercicio_generado": pregunta["id_ejercicio_generado"],
            "respuesta": str(respuesta),
            "request_id": str(uuid.uuid4()),
            "tiempo_respuesta_ms": 1000,
        },
    )
    payload = respuesta_http.get_json()
    assert respuesta_http.status_code == 200, payload
    assert payload["success"], payload
    return payload["data"]


def _registrar_estudiante(client, correo):
    respuesta = client.post(
        "/api/auth/register",
        json={
            "nombres": "Demo",
            "apellidos": "Juego",
            "correo": correo,
            "password": "Password123",
            "rol": "estudiante",
        },
    )
    payload = respuesta.get_json()
    assert respuesta.status_code == 201, payload
    return payload["data"]["access_token"]


def main():
    app = crear_app()
    client = app.test_client()
    id_partida = None
    correo_demo = f"juego.estudiante.{int(time.time())}@test.local"
    _cleanup_usuario(correo_demo)

    grado_tema = _fetchone(
        """
        SELECT g.id_grado, t.id_tema
        FROM grados g
        INNER JOIN temas t ON t.id_grado = g.id_grado
        WHERE g.codigo_grado = '4P'
          AND t.nombre_tema = 'Multiplicacion'
        LIMIT 1
        """
    )
    assert grado_tema, "No existe tema Multiplicacion para 4P."

    try:
        token = _registrar_estudiante(client, correo_demo)
        onboarding = client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "modalidad": "cuenta_propia",
                "id_grado": grado_tema["id_grado"],
                "personaje": "masculino",
            },
        )
        payload_onboarding = onboarding.get_json()
        assert onboarding.status_code == 200, payload_onboarding

        inicio = client.post(
            "/api/juego/partidas",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "personaje": "masculino",
                "mapa": "bosque",
                "id_grado": grado_tema["id_grado"],
                "id_tema": grado_tema["id_tema"],
            },
        )
        payload_inicio = inicio.get_json()
        assert inicio.status_code == 201, payload_inicio
        assert payload_inicio["success"], payload_inicio

        id_partida = payload_inicio["data"]["partida"]["id_partida"]
        pregunta = payload_inicio["data"]["pregunta_actual"]

        print(f"Partida demo: {id_partida}")
        for numero in range(1, 4):
            generado = _ejercicio_generado(pregunta["id_ejercicio_generado"])
            assert generado["explicacion_pasos"], "El ejercicio generado debe guardar su procedimiento."
            print(
                f"Pregunta {numero}: {generado['nombre_plantilla']} | "
                f"{generado['codigo_nivel']} | {generado['enunciado']} = {generado['respuesta_correcta']}"
            )
            data = _responder(client, token, id_partida, pregunta, generado["respuesta_correcta"])
            assert data["resultado"]["explicacion_pasos"] is None, "Un acierto no debe revelar procedimiento."
            pregunta = data["siguiente_pregunta"]

        assert data["agente"]["accion"] == "aumentar", data["agente"]
        assert pregunta["nivel"]["codigo"] == "intermedio", pregunta
        print("AGENTE: facil -> intermedio")

        for numero in range(4, 6):
            generado = _ejercicio_generado(pregunta["id_ejercicio_generado"])
            respuesta_erronea = int(generado["respuesta_correcta"]) + 1
            print(
                f"Pregunta {numero}: {generado['nombre_plantilla']} | "
                f"{generado['codigo_nivel']} | {generado['enunciado']} != {respuesta_erronea}"
            )
            data = _responder(client, token, id_partida, pregunta, respuesta_erronea)
            pasos = data["resultado"]["explicacion_pasos"]
            assert pasos and 1 <= len(pasos) <= 4, "Un error debe devolver pasos breves."
            assert generado["respuesta_correcta"] in " ".join(pasos), "El procedimiento debe llegar a la respuesta correcta."
            pregunta = data["siguiente_pregunta"]

        assert data["agente"]["accion"] == "reducir", data["agente"]
        assert pregunta["nivel"]["codigo"] == "facil", pregunta
        print("AGENTE: intermedio -> facil")

        final = _ejercicio_generado(pregunta["id_ejercicio_generado"])
        print(
            f"Pregunta 6: {final['nombre_plantilla']} | "
            f"{final['codigo_nivel']} | {final['enunciado']}"
        )

        conteos = _fetchall(
            """
            SELECT 'intentos' AS tabla, COUNT(*) AS total FROM intentos_juego WHERE id_partida = %s
            UNION ALL
            SELECT 'generados', COUNT(*) FROM ejercicios_generados WHERE id_partida = %s
            UNION ALL
            SELECT 'decisiones', COUNT(*) FROM decisiones_agente WHERE id_partida = %s
            """,
            (id_partida, id_partida, id_partida),
        )
        for conteo in conteos:
            print(f"{conteo['tabla']}: {conteo['total']}")

        progreso = client.get("/api/estudiante/progreso", headers={"Authorization": f"Bearer {token}"})
        payload_progreso = progreso.get_json()
        assert progreso.status_code == 200, payload_progreso
        assert payload_progreso["data"]["progreso"]["total_ejercicios"] == 5, payload_progreso
        assert payload_progreso["data"]["progreso"]["total_aciertos"] == 3, payload_progreso
        assert payload_progreso["data"]["temas"][0]["cambios_dificultad"] >= 2, payload_progreso
        print("progreso estudiante: OK")

        historial = client.get("/api/estudiante/historial", headers={"Authorization": f"Bearer {token}"})
        payload_historial = historial.get_json()
        assert historial.status_code == 200, payload_historial
        assert payload_historial["data"]["historial"][0]["id_partida"] == id_partida, payload_historial
        print("historial estudiante: OK")

        panel = client.get("/api/estudiante/panel", headers={"Authorization": f"Bearer {token}"})
        payload_panel = panel.get_json()
        assert panel.status_code == 200, payload_panel
        assert payload_panel["data"]["historial_reciente"][0]["id_partida"] == id_partida, payload_panel
        print("panel estudiante: OK")
    finally:
        if id_partida:
            _cleanup(id_partida)
        _cleanup_usuario(correo_demo)


if __name__ == "__main__":
    main()
