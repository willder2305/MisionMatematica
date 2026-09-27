import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion


CORREO = f"demo.auth.{int(time.time())}@test.local"
PASSWORD = "Password123"
PASSWORD_NUEVO = "Password456"


def _cleanup(correo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        if usuario:
            cursor.execute("DELETE FROM refresh_tokens WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM recuperaciones_contrasena WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM verificaciones_correo WHERE id_usuario = %s", (usuario["id_usuario"],))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (usuario["id_usuario"],))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def main():
    app = crear_app()
    client = app.test_client()
    _cleanup(CORREO)

    registro = client.post("/api/auth/register", json={
        "nombres": "Demo",
        "apellidos": "Auth",
        "correo": CORREO,
        "password": PASSWORD,
        "rol": "estudiante",
    })
    data_registro = registro.get_json()
    assert registro.status_code == 201, data_registro
    access = data_registro["data"]["access_token"]
    refresh = data_registro["data"]["refresh_token"]
    print("registro: OK")

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200, me.get_json()
    print("me: OK")

    login = client.post("/api/auth/login", json={"correo": CORREO, "password": PASSWORD})
    data_login = login.get_json()
    assert login.status_code == 200, data_login
    print("login: OK")

    renovar = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    data_renovar = renovar.get_json()
    assert renovar.status_code == 200, data_renovar
    refresh_rotado = data_renovar["data"]["refresh_token"]
    print("refresh: OK")

    logout = client.post("/api/auth/logout", json={"refresh_token": refresh_rotado})
    assert logout.status_code == 200, logout.get_json()
    print("logout: OK")

    forgot = client.post("/api/auth/forgot-password", json={"correo": CORREO})
    data_forgot = forgot.get_json()
    assert forgot.status_code == 200, data_forgot
    token_reset = data_forgot["data"]["dev_token"]
    reset = client.post("/api/auth/reset-password", json={"token": token_reset, "password": PASSWORD_NUEVO})
    assert reset.status_code == 200, reset.get_json()
    print("reset-password: OK")

    login_nuevo = client.post("/api/auth/login", json={"correo": CORREO, "password": PASSWORD_NUEVO})
    assert login_nuevo.status_code == 200, login_nuevo.get_json()
    print("login nuevo password: OK")

    _cleanup(CORREO)


if __name__ == "__main__":
    main()
