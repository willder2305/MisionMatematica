import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from db import obtener_conexion
from services.security_service import limpiar_rate_limit


PASSWORD = "Password123"
CORREO_ADMIN = f"demo.rutas.admin.{int(time.time())}@test.local"
CORREO_ESTUDIANTE = f"demo.rutas.estudiante.{int(time.time())}@test.local"


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
    respuesta = client.post("/api/auth/register", json={
        "nombres": "Demo",
        "apellidos": "Rutas",
        "correo": correo,
        "password": PASSWORD,
        "rol": rol,
    })
    payload = respuesta.get_json()
    assert respuesta.status_code == 201, payload
    return payload["data"]["access_token"]


def main():
    limpiar_rate_limit()
    app = crear_app()
    client = app.test_client()
    _cleanup(CORREO_ADMIN, CORREO_ESTUDIANTE)

    try:
        sin_auth_secciones = client.get("/api/secciones")
        assert sin_auth_secciones.status_code == 401, sin_auth_secciones.get_json()
        print("secciones sin auth: OK")

        sin_auth_grados = client.get("/api/grados")
        assert sin_auth_grados.status_code == 401, sin_auth_grados.get_json()
        print("grados sin auth: OK")

        sin_auth_admin = client.get("/api/admin/usuarios")
        assert sin_auth_admin.status_code == 401, sin_auth_admin.get_json()
        print("admin sin auth: OK")

        sin_auth_temas = client.get("/api/temas?grado=1")
        assert sin_auth_temas.status_code == 401, sin_auth_temas.get_json()
        print("temas sin auth: OK")

        sin_auth_plantillas = client.get("/api/plantillas")
        assert sin_auth_plantillas.status_code == 401, sin_auth_plantillas.get_json()
        print("plantillas sin auth: OK")

        token_estudiante = _registrar(client, CORREO_ESTUDIANTE, "estudiante")
        estudiante_secciones = client.get("/api/secciones", headers={"Authorization": f"Bearer {token_estudiante}"})
        assert estudiante_secciones.status_code == 403, estudiante_secciones.get_json()
        print("estudiante sin permiso admin/docente: OK")

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_estudiante}"})
        data_me = me.get_json()
        assert me.status_code == 200, data_me
        usuario = data_me["data"]["usuario"]
        assert usuario["rol"] == "estudiante", usuario
        assert "onboarding_completado" in usuario, usuario
        print("auth me retorna rol y onboarding: OK")

        token_admin = _registrar(client, CORREO_ADMIN, "administrador")
        admin_secciones = client.get("/api/secciones", headers={"Authorization": f"Bearer {token_admin}"})
        assert admin_secciones.status_code == 200, admin_secciones.get_json()
        print("admin consulta secciones: OK")
    finally:
        _cleanup(CORREO_ADMIN, CORREO_ESTUDIANTE)
        limpiar_rate_limit()


if __name__ == "__main__":
    main()
