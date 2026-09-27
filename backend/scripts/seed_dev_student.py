"""Crea o verifica el estudiante local de QA sin exponerlo a produccion."""

import argparse
import sys
from pathlib import Path

# Permite ejecutar este archivo directamente desde la carpeta backend.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from werkzeug.security import generate_password_hash

from config import Config
from db import obtener_conexion


TEST_EMAIL = "estudiante500@mision.test"
TEST_PASSWORD = "Mision500!"
TEST_ROLE = "estudiante"
TEST_GRADE_CODE = "6P"
INITIAL_BALANCE = 500
INITIAL_REFERENCE = "seed:estudiante500:saldo_inicial"
INITIAL_DESCRIPTION = "Saldo inicial para usuario de pruebas."


def require_non_production():
    """Evita crear una credencial conocida cuando el entorno es de produccion."""
    if Config.APP_ENV.strip().lower() == "production":
        raise RuntimeError("El seed de QA no puede ejecutarse con APP_ENV=production.")


def _required_id(cursor, query, value, label):
    """Busca una referencia obligatoria y falla con contexto si falta el catalogo base."""
    cursor.execute(query, (value,))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No existe {label}: {value}.")
    return row["id"]


def _create_or_update_student(cursor, role_id):
    """Mantiene el usuario QA activo con la misma funcion de hash usada por autenticacion."""
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s FOR UPDATE", (TEST_EMAIL,))
    user = cursor.fetchone()
    password_hash = generate_password_hash(TEST_PASSWORD)
    if user:
        cursor.execute(
            """
            UPDATE usuarios
            SET nombres = 'Estudiante', apellidos = '500', password_hash = %s, id_rol = %s,
                estado = 'activo', correo_verificado = 1, onboarding_completado = 1
            WHERE id_usuario = %s
            """,
            (password_hash, role_id, user["id_usuario"]),
        )
        return user["id_usuario"]

    cursor.execute(
        """
        INSERT INTO usuarios
            (nombres, apellidos, correo, password_hash, id_rol, estado, correo_verificado, onboarding_completado)
        VALUES ('Estudiante', '500', %s, %s, %s, 'activo', 1, 1)
        """,
        (TEST_EMAIL, password_hash, role_id),
    )
    return cursor.lastrowid


def _set_initial_balance(cursor, user_id, reset_balance):
    """Registra el abono inicial una sola vez; el reinicio es siempre una accion manual."""
    cursor.execute(
        "INSERT IGNORE INTO monederos (id_usuario, saldo_monedas) VALUES (%s, 0)",
        (user_id,),
    )
    cursor.execute("SELECT saldo_monedas FROM monederos WHERE id_usuario = %s FOR UPDATE", (user_id,))
    current_balance = int(cursor.fetchone()["saldo_monedas"])
    cursor.execute(
        "SELECT id_movimiento FROM movimientos_monedas WHERE referencia = %s LIMIT 1",
        (INITIAL_REFERENCE,),
    )
    already_seeded = cursor.fetchone() is not None

    if already_seeded and not reset_balance:
        return current_balance

    amount = INITIAL_BALANCE - current_balance
    reference = INITIAL_REFERENCE if not already_seeded else "seed:estudiante500:saldo_restaurado"
    description = INITIAL_DESCRIPTION if not already_seeded else "Saldo restaurado manualmente para usuario de pruebas."
    cursor.execute(
        "UPDATE monederos SET saldo_monedas = %s WHERE id_usuario = %s",
        (INITIAL_BALANCE, user_id),
    )
    cursor.execute(
        """
        INSERT INTO movimientos_monedas
            (id_usuario, tipo, cantidad, saldo_anterior, saldo_nuevo, referencia, descripcion)
        VALUES (%s, 'ajuste_pruebas', %s, %s, %s, %s, %s)
        """,
        (user_id, amount, current_balance, INITIAL_BALANCE, reference, description),
    )
    return INITIAL_BALANCE


def seed_student(reset_balance=False):
    """Crea el perfil independiente Sexto, inventario inicial y saldo QA dentro de una transaccion."""
    require_non_production()
    connection = obtener_conexion()
    cursor = connection.cursor(dictionary=True)
    try:
        role_id = _required_id(cursor, "SELECT id_rol AS id FROM roles WHERE nombre = %s", TEST_ROLE, "rol")
        grade_id = _required_id(cursor, "SELECT id_grado AS id FROM grados WHERE codigo_grado = %s", TEST_GRADE_CODE, "grado")
        user_id = _create_or_update_student(cursor, role_id)
        cursor.execute(
            """
            INSERT INTO perfiles_estudiante
                (id_usuario, id_grado, id_institucion, id_institucion_grado, id_seccion, modalidad, personaje)
            VALUES (%s, %s, NULL, NULL, NULL, 'cuenta_propia', 'masculino')
            ON DUPLICATE KEY UPDATE id_grado = VALUES(id_grado), id_institucion = NULL,
                id_institucion_grado = NULL, id_seccion = NULL, modalidad = 'cuenta_propia', personaje = 'masculino'
            """,
            (user_id, grade_id),
        )
        cursor.execute(
            """
            INSERT INTO usuario_items (id_usuario, id_item)
            SELECT %s, id_item FROM tienda_items WHERE es_inicial = 1 AND estado = 'activo'
            ON DUPLICATE KEY UPDATE estado = 'activo'
            """,
            (user_id,),
        )
        cursor.execute(
            """
            INSERT INTO preferencias_estudiante (id_usuario, personaje_key, modo_mapa, mapa_key, ultimo_mapa_key)
            VALUES (%s, 'masculino', 'aleatorio', NULL, NULL)
            ON DUPLICATE KEY UPDATE personaje_key = 'masculino', modo_mapa = 'aleatorio', mapa_key = NULL
            """,
            (user_id,),
        )
        balance = _set_initial_balance(cursor, user_id, reset_balance)
        connection.commit()
        return {"email": TEST_EMAIL, "user_id": user_id, "balance": balance}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main():
    """Expone un reinicio deliberado de saldo sin hacerlo en cada ejecucion normal."""
    parser = argparse.ArgumentParser(description="Crea el estudiante local de QA para Mision Matematica.")
    parser.add_argument("--reset-balance", action="store_true", help="Restablece manualmente el saldo a 500 monedas.")
    args = parser.parse_args()
    result = seed_student(reset_balance=args.reset_balance)
    print(f"Usuario QA listo: {result['email']} (saldo: {result['balance']} monedas)")


if __name__ == "__main__":
    main()
