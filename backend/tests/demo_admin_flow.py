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


def _cleanup(correos, nombre_tema):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_tema FROM temas WHERE nombre_tema = %s", (nombre_tema,))
        for tema in cursor.fetchall():
            cursor.execute("SELECT id_ejercicio FROM ejercicios WHERE id_tema = %s", (tema["id_tema"],))
            for ejercicio in cursor.fetchall():
                cursor.execute("DELETE FROM opciones_ejercicio WHERE id_ejercicio = %s", (ejercicio["id_ejercicio"],))
                cursor.execute("DELETE FROM ejercicios WHERE id_ejercicio = %s", (ejercicio["id_ejercicio"],))
            cursor.execute("DELETE FROM temas WHERE id_tema = %s", (tema["id_tema"],))

        for correo in correos:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            if not usuario:
                continue
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
    correo_admin = f"admin.fase8.{marca}@test.local"
    correo_estudiante = f"admin.estudiante.{marca}@test.local"
    nombre_tema = f"Tema Admin Demo {marca}"
    _cleanup([correo_admin, correo_estudiante], nombre_tema)

    app = crear_app()
    client = app.test_client()
    grado = _query("SELECT id_grado FROM grados WHERE codigo_grado = '4P' LIMIT 1", fetchone=True)
    nivel = _query("SELECT id_nivel FROM niveles_dificultad WHERE codigo = 'facil' LIMIT 1", fetchone=True)
    regla = _query("SELECT * FROM reglas_adaptativas ORDER BY prioridad ASC LIMIT 1", fetchone=True)
    assert grado and nivel and regla, "Faltan datos base para la demo admin."

    try:
        token_admin, id_admin = _registrar(client, correo_admin, "administrador")
        token_estudiante, id_estudiante = _registrar(client, correo_estudiante, "estudiante")
        assert token_admin and token_estudiante

        panel = client.get("/api/admin/panel", headers={"Authorization": f"Bearer {token_admin}"})
        assert panel.status_code == 200, panel.get_json()
        assert panel.get_json()["data"]["usuarios"] >= 2, panel.get_json()
        print("panel admin: OK")

        usuarios = client.get("/api/admin/usuarios", headers={"Authorization": f"Bearer {token_admin}"})
        payload_usuarios = usuarios.get_json()
        assert usuarios.status_code == 200, payload_usuarios
        assert any(usuario["id_usuario"] == id_estudiante for usuario in payload_usuarios["data"]), payload_usuarios
        print("usuarios admin: OK")

        estado_usuario = client.patch(
            f"/api/admin/usuarios/{id_estudiante}/estado",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"estado": "inactivo"},
        )
        assert estado_usuario.status_code == 200, estado_usuario.get_json()
        print("estado usuario: OK")

        rol_usuario = client.patch(
            f"/api/admin/usuarios/{id_estudiante}/rol",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"rol": "docente"},
        )
        assert rol_usuario.status_code == 200, rol_usuario.get_json()
        print("rol usuario: OK")

        tema = client.post(
            "/api/admin/temas",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "id_grado": grado["id_grado"],
                "nombre_tema": nombre_tema,
                "descripcion": "Tema temporal para demo admin.",
                "estado": "activo",
            },
        )
        payload_tema = tema.get_json()
        assert tema.status_code == 201, payload_tema
        id_tema = payload_tema["data"]["id_tema"]
        print("crear tema: OK")

        temas = client.get("/api/admin/temas", headers={"Authorization": f"Bearer {token_admin}"})
        assert any(item["id_tema"] == id_tema for item in temas.get_json()["data"]), temas.get_json()
        print("listar temas: OK")

        ejercicio = client.post(
            "/api/admin/ejercicios",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "id_tema": id_tema,
                "id_nivel": nivel["id_nivel"],
                "enunciado": "Cuanto es 2 + 2?",
                "tipo_respuesta": "seleccion_multiple",
                "respuesta_correcta": "4",
                "opciones": ["3", "4", "5"],
                "explicacion": "2 + 2 = 4.",
                "pista": "Suma dos pares.",
                "estado": "publicado",
            },
        )
        payload_ejercicio = ejercicio.get_json()
        assert ejercicio.status_code == 201, payload_ejercicio
        id_ejercicio = payload_ejercicio["data"]["id_ejercicio"]
        print("crear ejercicio: OK")

        ejercicios = client.get(
            "/api/admin/ejercicios",
            headers={"Authorization": f"Bearer {token_admin}"},
            query_string={"id_tema": id_tema},
        )
        assert any(item["id_ejercicio"] == id_ejercicio for item in ejercicios.get_json()["data"]), ejercicios.get_json()
        print("listar ejercicios: OK")

        reglas = client.get("/api/admin/reglas", headers={"Authorization": f"Bearer {token_admin}"})
        payload_reglas = reglas.get_json()
        assert reglas.status_code == 200, payload_reglas
        assert payload_reglas["data"], payload_reglas
        print("listar reglas: OK")

        regla_actualizada = client.put(
            f"/api/admin/reglas/{regla['id_regla']}",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "nombre": regla["nombre"],
                "descripcion": (regla.get("descripcion") or "") + " ",
                "prioridad": regla["prioridad"],
                "parametros_json": regla["parametros_json"],
                "accion": regla["accion"],
                "estado": regla["estado"],
            },
        )
        assert regla_actualizada.status_code == 200, regla_actualizada.get_json()
        print("actualizar regla: OK")

        _query(
            """
            UPDATE reglas_adaptativas
            SET descripcion = %s
            WHERE id_regla = %s
            """,
            (regla.get("descripcion"), regla["id_regla"]),
        )
    finally:
        _cleanup([correo_admin, correo_estudiante], nombre_tema)


if __name__ == "__main__":
    main()
