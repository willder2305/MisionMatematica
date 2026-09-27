import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion


def _cleanup(correos):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        for correo in correos:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            if usuario:
                cursor.execute("DELETE FROM docente_grados WHERE id_usuario_docente = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM perfiles_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM perfiles_docente WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (usuario["id_usuario"],))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def _grado():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_grado FROM grados WHERE codigo_grado = '4P' LIMIT 1")
        return cursor.fetchone()["id_grado"]
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
    return payload["data"]["access_token"]


def main():
    marca = int(time.time())
    correo_estudiante = f"onboarding.estudiante.{marca}@test.local"
    correo_docente = f"onboarding.docente.{marca}@test.local"
    _cleanup([correo_estudiante, correo_docente])

    app = crear_app()
    client = app.test_client()
    id_grado = _grado()

    token_estudiante = _registrar(client, correo_estudiante, "estudiante")
    estudiante = client.post(
        "/api/onboarding",
        headers={"Authorization": f"Bearer {token_estudiante}"},
        json={"modalidad": "cuenta_propia", "id_grado": id_grado, "personaje": "femenino"},
    )
    payload_estudiante = estudiante.get_json()
    assert estudiante.status_code == 200, payload_estudiante
    assert payload_estudiante["data"]["perfil"]["personaje"] == "femenino", payload_estudiante
    print("onboarding estudiante: OK")

    token_docente = _registrar(client, correo_docente, "docente")
    docente = client.post(
        "/api/onboarding",
        headers={"Authorization": f"Bearer {token_docente}"},
        json={"institucion": "Escuela Demo", "grados": [id_grado]},
    )
    payload_docente = docente.get_json()
    assert docente.status_code == 200, payload_docente
    assert len(payload_docente["data"]["perfil"]["grados"]) == 1, payload_docente
    print("onboarding docente: OK")

    _cleanup([correo_estudiante, correo_docente])


if __name__ == "__main__":
    main()
