import sys
import time
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
            _limpiar_partidas_usuario(cursor, usuario["id_usuario"])
            cursor.execute("SELECT id_grupo FROM grupos WHERE id_docente = %s", (usuario["id_usuario"],))
            for grupo in cursor.fetchall():
                cursor.execute(
                    """
                    SELECT id_asignacion
                    FROM asignaciones
                    WHERE id_grupo = %s
                    """,
                    (grupo["id_grupo"],),
                )
                for asignacion in cursor.fetchall():
                    cursor.execute("DELETE FROM asignacion_ejercicios WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                    cursor.execute("DELETE FROM asignacion_temas WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                    cursor.execute("DELETE FROM asignaciones WHERE id_asignacion = %s", (asignacion["id_asignacion"],))
                cursor.execute("DELETE FROM estudiantes_grupos WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM pines_acceso WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM grupo_secciones WHERE id_grupo = %s", (grupo["id_grupo"],))
                cursor.execute("DELETE FROM grupos WHERE id_grupo = %s", (grupo["id_grupo"],))
            cursor.execute("DELETE FROM estudiantes_grupos WHERE id_usuario_estudiante = %s", (usuario["id_usuario"],))
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


def main():
    marca = int(time.time())
    correo_docente = f"asignacion.docente.{marca}@test.local"
    correo_estudiante = f"asignacion.estudiante.{marca}@test.local"
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
    assert grado_tema and nivel, "Faltan grado, tema o nivel demo."

    try:
        token_docente, id_docente = _registrar(client, correo_docente, "docente")
        docente_onboarding = client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={"institucion": "Escuela Demo", "grados": [grado_tema["id_grado"]]},
        )
        assert docente_onboarding.status_code == 200, docente_onboarding.get_json()

        grupo = client.post(
            "/api/grupos",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={"id_grado": grado_tema["id_grado"], "nombre": f"Grupo Asignacion {marca}", "descripcion": "Demo"},
        )
        payload_grupo = grupo.get_json()
        assert grupo.status_code == 201, payload_grupo
        id_grupo = payload_grupo["data"]["id_grupo"]
        assert payload_grupo["data"]["id_docente"] == id_docente, payload_grupo
        print("grupo docente: OK")

        asignacion = client.post(
            "/api/asignaciones",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={
                "id_grupo": id_grupo,
                "nombre": f"Multiplicacion demo {marca}",
                "instrucciones": "Resolver ejercicios generados por el agente.",
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
        payload_asignacion = asignacion.get_json()
        assert asignacion.status_code == 201, payload_asignacion
        id_asignacion = payload_asignacion["data"]["id_asignacion"]
        print("crear asignacion: OK")

        token_estudiante, _ = _registrar(client, correo_estudiante, "estudiante")
        pin_res = client.post(
            f"/api/grupos/{id_grupo}/pines",
            headers={"Authorization": f"Bearer {token_docente}"},
            json={},
        )
        pin = pin_res.get_json()["data"]["pin"]
        ingreso = client.post(
            "/api/pines/ingresar",
            headers={"Authorization": f"Bearer {token_estudiante}"},
            json={"pin": pin},
        )
        assert ingreso.status_code == 201, ingreso.get_json()
        estudiante_onboarding = client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token_estudiante}"},
            json={"modalidad": "grupo_educativo", "personaje": "femenino"},
        )
        assert estudiante_onboarding.status_code == 200, estudiante_onboarding.get_json()
        print("estudiante grupo: OK")

        actividades = client.get("/api/estudiante/asignaciones", headers={"Authorization": f"Bearer {token_estudiante}"})
        payload_actividades = actividades.get_json()
        assert actividades.status_code == 200, payload_actividades
        assert payload_actividades["data"][0]["id_asignacion"] == id_asignacion, payload_actividades
        print("actividad visible: OK")

        partida = client.post(
            "/api/juego/partidas",
            headers={"Authorization": f"Bearer {token_estudiante}"},
            json={
                "personaje": "femenino",
                "mapa": "bosque",
                "id_asignacion": id_asignacion,
                "id_grado": grado_tema["id_grado"],
                "id_tema": grado_tema["id_tema"],
            },
        )
        payload_partida = partida.get_json()
        assert partida.status_code == 201, payload_partida
        assert payload_partida["data"]["partida"]["id_asignacion"] == id_asignacion, payload_partida
        print("partida asignada: OK")
    finally:
        _cleanup([correo_docente, correo_estudiante])


if __name__ == "__main__":
    main()
