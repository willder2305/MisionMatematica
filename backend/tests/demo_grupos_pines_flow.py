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


def _cleanup(correos):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        for correo in correos:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            if not usuario:
                continue
            cursor.execute("SELECT id_grupo FROM grupos WHERE id_docente = %s", (usuario["id_usuario"],))
            grupos = cursor.fetchall()
            for grupo in grupos:
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
    correo_docente = f"grupo.docente.{marca}@test.local"
    correo_estudiante = f"grupo.estudiante.{marca}@test.local"
    _cleanup([correo_docente, correo_estudiante])

    app = crear_app()
    client = app.test_client()
    id_grado = _query("SELECT id_grado FROM grados WHERE codigo_grado = '4P' LIMIT 1", fetchone=True)["id_grado"]

    token_docente, id_docente = _registrar(client, correo_docente, "docente")
    grupo = client.post(
        "/api/grupos",
        headers={"Authorization": f"Bearer {token_docente}"},
        json={"id_grado": id_grado, "nombre": f"Grupo Demo {marca}", "descripcion": "Demo PIN"},
    )
    payload_grupo = grupo.get_json()
    assert grupo.status_code == 201, payload_grupo
    id_grupo = payload_grupo["data"]["id_grupo"]
    assert payload_grupo["data"]["id_docente"] == id_docente, payload_grupo
    print("crear grupo: OK")

    pin_res = client.post(
        f"/api/grupos/{id_grupo}/pines",
        headers={"Authorization": f"Bearer {token_docente}"},
        json={},
    )
    payload_pin = pin_res.get_json()
    assert pin_res.status_code == 201, payload_pin
    pin = payload_pin["data"]["pin"]
    assert len(pin) == 6 and pin.isdigit(), payload_pin
    print("generar PIN: OK", pin)

    token_estudiante, id_estudiante = _registrar(client, correo_estudiante, "estudiante")
    validar = client.post(
        "/api/pines/validar",
        headers={"Authorization": f"Bearer {token_estudiante}"},
        json={"pin": pin},
    )
    assert validar.status_code == 200, validar.get_json()
    print("validar PIN: OK")

    ingreso = client.post(
        "/api/pines/ingresar",
        headers={"Authorization": f"Bearer {token_estudiante}"},
        json={"pin": pin},
    )
    assert ingreso.status_code == 201, ingreso.get_json()
    vinculo = _query(
        """
        SELECT *
        FROM estudiantes_grupos
        WHERE id_usuario_estudiante = %s
          AND id_grupo = %s
          AND estado = 'activo'
        """,
        (id_estudiante, id_grupo),
        fetchone=True,
    )
    assert vinculo, "No se creo estudiantes_grupos."
    print("ingresar estudiante: OK")

    regen = client.post(
        f"/api/pines/{payload_pin['data']['id_pin']}/regenerar",
        headers={"Authorization": f"Bearer {token_docente}"},
    )
    assert regen.status_code == 201, regen.get_json()
    assert regen.get_json()["data"]["pin"] != pin, regen.get_json()
    print("regenerar PIN: OK")

    _cleanup([correo_docente, correo_estudiante])


if __name__ == "__main__":
    main()
