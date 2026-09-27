import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion
from services.security_service import limpiar_rate_limit
from werkzeug.security import generate_password_hash


PASSWORD = "Password123"
CORREO_ADMIN = f"demo.audit.admin.{int(time.time())}@test.local"
CORREO_ESTUDIANTE = f"demo.audit.estudiante.{int(time.time())}@test.local"


def _cleanup(*correos):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        for correo in correos:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            usuario = cursor.fetchone()
            if usuario:
                cursor.execute("DELETE FROM bitacora_acciones WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM recuperaciones_contrasena WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM verificaciones_correo WHERE id_usuario = %s", (usuario["id_usuario"],))
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (usuario["id_usuario"],))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def _registrar(client, correo, rol):
    if rol == "administrador":
        return _crear_administrador_controlado(client, correo)

    respuesta = client.post("/api/auth/register", json={
        "nombres": "Demo",
        "apellidos": "Auditoria",
        "correo": correo,
        "password": PASSWORD,
        "rol": rol,
    })
    payload = respuesta.get_json()
    assert respuesta.status_code == 201, payload
    return payload["data"]["access_token"], payload["data"]["usuario"]["id_usuario"]


def _crear_administrador_controlado(client, correo):
    """Crea el administrador de QA sin usar el endpoint público de registro."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'administrador'")
        rol = cursor.fetchone()
        assert rol, "No existe el rol administrador"
        cursor.execute(
            """
            INSERT INTO usuarios (nombres, apellidos, correo, password_hash, id_rol, estado, correo_verificado, onboarding_completado)
            VALUES ('Demo', 'Auditoria', %s, %s, %s, 'activo', 1, 1)
            """,
            (correo, generate_password_hash(PASSWORD), rol["id_rol"]),
        )
        id_usuario = cursor.lastrowid
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()

    respuesta = client.post("/api/auth/login", json={"correo": correo, "password": PASSWORD})
    payload = respuesta.get_json()
    assert respuesta.status_code == 200, payload
    return payload["data"]["access_token"], id_usuario


def main():
    limpiar_rate_limit()
    app = crear_app()
    client = app.test_client()
    _cleanup(CORREO_ADMIN, CORREO_ESTUDIANTE)

    try:
        token_admin, _ = _registrar(client, CORREO_ADMIN, "administrador")
        _, id_estudiante = _registrar(client, CORREO_ESTUDIANTE, "estudiante")

        cambio = client.patch(
            f"/api/admin/usuarios/{id_estudiante}/estado",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"estado": "inactivo"},
        )
        assert cambio.status_code == 200, cambio.get_json()
        print("accion auditada: OK")

        auditoria = client.get(
            "/api/admin/auditoria?entidad=estado&resultado=exitoso&limite=20",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        data = auditoria.get_json()
        assert auditoria.status_code == 200, data
        assert any(evento["ruta"].endswith(f"/usuarios/{id_estudiante}/estado") for evento in data["data"]), data
        print("consulta auditoria: OK")

        limitado = None
        for _ in range(11):
            limitado = client.post("/api/auth/login", json={"correo": "nadie@test.local", "password": "x"})
        assert limitado.status_code == 429, limitado.get_json()
        print("rate limit auth: OK")
    finally:
        _cleanup(CORREO_ADMIN, CORREO_ESTUDIANTE)
        limpiar_rate_limit()


if __name__ == "__main__":
    main()
