"""Crea o normaliza el único administrador activo del sistema.

El secreto generado se imprime solo cuando se crea la cuenta canónica por
primera vez. No se guarda en archivos, variables de entorno ni bitácoras.
"""

import argparse
import json
import secrets
import string
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import obtener_conexion  # noqa: E402


CORREO_ADMIN = "admin@misionmatematica.com"


def _contrasena_segura():
    # Garantiza longitud y variedad sin persistir el valor plano.
    alfabeto = string.ascii_letters + string.digits + "!@#$%^&*-_"
    while True:
        valor = "".join(secrets.choice(alfabeto) for _ in range(20))
        if all(any(caracter in grupo for caracter in valor) for grupo in (string.ascii_lowercase, string.ascii_uppercase, string.digits)):
            return valor


def asegurar_administrador(restablecer_contrasena=False):
    """Deja una cuenta administrativa canónica activa y desactiva duplicados."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    contrasena_generada = None
    try:
        cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'administrador' LIMIT 1")
        rol = cursor.fetchone()
        if not rol:
            raise RuntimeError("No existe el rol administrador en la base de datos.")

        cursor.execute("SELECT * FROM usuarios WHERE correo = %s LIMIT 1", (CORREO_ADMIN,))
        administrador = cursor.fetchone()
        if administrador:
            if restablecer_contrasena:
                contrasena_generada = _contrasena_segura()
            cursor.execute(
                """
                UPDATE usuarios
                SET nombres = 'Administrador', apellidos = 'Misión Matemática',
                    id_rol = %s, estado = 'activo',
                    password_hash = COALESCE(%s, password_hash)
                WHERE id_usuario = %s
                """,
                (rol["id_rol"], generate_password_hash(contrasena_generada) if contrasena_generada else None, administrador["id_usuario"]),
            )
            id_admin = administrador["id_usuario"]
        else:
            contrasena_generada = _contrasena_segura()
            cursor.execute(
                """
                INSERT INTO usuarios
                    (nombres, apellidos, correo, password_hash, id_rol, estado, correo_verificado, onboarding_completado)
                VALUES ('Administrador', 'Misión Matemática', %s, %s, %s, 'activo', 1, 1)
                """,
                (CORREO_ADMIN, generate_password_hash(contrasena_generada), rol["id_rol"]),
            )
            id_admin = cursor.lastrowid

        cursor.execute(
            """
            UPDATE usuarios
            SET estado = 'inactivo'
            WHERE id_rol = %s AND estado = 'activo' AND id_usuario <> %s
            """,
            (rol["id_rol"], id_admin),
        )
        desactivados = cursor.rowcount
        cursor.execute(
            """
            INSERT INTO bitacora_acciones
                (id_usuario, accion, entidad, id_entidad, metodo, ruta, codigo_estado, resultado, detalles_json)
            VALUES (%s, 'bootstrap_administrador', 'usuarios', %s, 'SCRIPT', 'scripts/bootstrap_admin.py', 200, 'exitoso', %s)
            """,
            (id_admin, str(id_admin), json.dumps({"administradores_desactivados": desactivados})),
        )
        conexion.commit()
        return id_admin, contrasena_generada, desactivados
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normaliza el administrador único de Misión Matemática.")
    parser.add_argument("--reset-password", action="store_true", help="Genera y muestra una nueva contraseña temporal.")
    argumentos = parser.parse_args()
    id_admin, contrasena, desactivados = asegurar_administrador(argumentos.reset_password)
    print(f"Administrador canónico listo (id={id_admin}); cuentas desactivadas: {desactivados}.")
    if contrasena:
        print(f"CONTRASEÑA TEMPORAL (se muestra una sola vez): {contrasena}")
