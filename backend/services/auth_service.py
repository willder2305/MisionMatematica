import secrets
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db import obtener_conexion
from services.jwt_service import TokenError, crear_token, decodificar_token, hash_token


ROLES_VALIDOS = ("administrador", "docente", "estudiante")
ROLES_REGISTRO_PUBLICO = ("docente", "estudiante")


def _serializar_usuario(fila):
    # Expone datos seguros del usuario sin hash ni tokens internos.
    if not fila:
        return None
    return {
        "id_usuario": fila["id_usuario"],
        "nombres": fila["nombres"],
        "apellidos": fila["apellidos"],
        "correo": fila["correo"],
        "rol": fila["rol"],
        "estado": fila["estado"],
        "correo_verificado": bool(fila["correo_verificado"]),
        "onboarding_completado": bool(fila["onboarding_completado"]),
        "ultimo_acceso": fila["ultimo_acceso"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("ultimo_acceso") else None,
    }


def _usuario_por_correo(correo, cursor):
    # Busca usuario por correo incluyendo password_hash para login.
    cursor.execute(
        """
        SELECT u.*, r.nombre AS rol
        FROM usuarios u
        INNER JOIN roles r ON r.id_rol = u.id_rol
        WHERE u.correo = %s
        """,
        (correo,),
    )
    return cursor.fetchone()


def _usuario_por_id(id_usuario, cursor):
    # Busca usuario por id para construir respuestas autenticadas.
    cursor.execute(
        """
        SELECT u.*, r.nombre AS rol
        FROM usuarios u
        INNER JOIN roles r ON r.id_rol = u.id_rol
        WHERE u.id_usuario = %s
        """,
        (id_usuario,),
    )
    return cursor.fetchone()


def _id_rol(nombre_rol, cursor):
    # Obtiene el id interno del rol sin confiar en valores enviados por cliente.
    cursor.execute("SELECT id_rol FROM roles WHERE nombre = %s", (nombre_rol,))
    fila = cursor.fetchone()
    return fila["id_rol"] if fila else None


def _validar_registro(datos):
    # Valida campos minimos para crear usuario con contrasena segura.
    errores = {}
    nombres = (datos.get("nombres") or "").strip()
    apellidos = (datos.get("apellidos") or "").strip()
    correo = (datos.get("correo") or "").strip().lower()
    password = datos.get("password") or ""
    rol = (datos.get("rol") or "estudiante").strip().lower()

    if len(nombres) < 2:
        errores["nombres"] = "Ingrese nombres validos."
    if len(apellidos) < 2:
        errores["apellidos"] = "Ingrese apellidos validos."
    if "@" not in correo or "." not in correo:
        errores["correo"] = "Ingrese un correo valido."
    if len(password) < 8:
        errores["password"] = "La contrasena debe tener al menos 8 caracteres."
    if rol not in ROLES_REGISTRO_PUBLICO:
        errores["rol"] = "Solo puede registrar una cuenta de estudiante o docente."
    return {"nombres": nombres, "apellidos": apellidos, "correo": correo, "password": password, "rol": rol}, errores


def _guardar_refresh_token(id_usuario, token, payload, cursor):
    # Persiste refresh token revocable usando hash y expiracion.
    expira = datetime.fromtimestamp(payload["exp"])
    cursor.execute(
        """
        INSERT INTO refresh_tokens (id_usuario, token_hash, jti, fecha_expiracion)
        VALUES (%s, %s, %s, %s)
        """,
        (id_usuario, hash_token(token), payload["jti"], expira),
    )


def _crear_tokens(usuario, cursor):
    # Genera access/refresh y almacena el refresh revocable.
    access_token, _ = crear_token(usuario, tipo="access")
    refresh_token, refresh_payload = crear_token(usuario, tipo="refresh")
    _guardar_refresh_token(usuario["id_usuario"], refresh_token, refresh_payload, cursor)
    return access_token, refresh_token


def registrar_usuario(datos):
    # Crea usuario con hash de password y devuelve tokens iniciales.
    datos_limpios, errores = _validar_registro(datos)
    if errores:
        return "datos_invalidos", "Revise los datos de registro.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if _usuario_por_correo(datos_limpios["correo"], cursor):
            return "duplicado", "El correo ya está registrado.", None, {"correo": "Correo duplicado."}
        id_rol = _id_rol(datos_limpios["rol"], cursor)
        if not id_rol:
            return "datos_invalidos", "Rol no disponible.", None, {"rol": "Rol no configurado."}

        cursor.execute(
            """
            INSERT INTO usuarios
                (nombres, apellidos, correo, password_hash, id_rol, estado, correo_verificado, onboarding_completado)
            VALUES (%s, %s, %s, %s, %s, 'activo', 0, 0)
            """,
            (
                datos_limpios["nombres"],
                datos_limpios["apellidos"],
                datos_limpios["correo"],
                generate_password_hash(datos_limpios["password"]),
                id_rol,
            ),
        )
        usuario = _usuario_por_id(cursor.lastrowid, cursor)
        access_token, refresh_token = _crear_tokens(usuario, cursor)
        conexion.commit()
        return "creado", "Usuario registrado correctamente.", {
            "usuario": _serializar_usuario(usuario),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def iniciar_sesion(datos):
    # Valida correo/contrasena y entrega tokens si el usuario esta activo.
    correo = (datos.get("correo") or "").strip().lower()
    password = datos.get("password") or ""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        usuario = _usuario_por_correo(correo, cursor)
        if not usuario or not check_password_hash(usuario["password_hash"], password):
            return "credenciales_invalidas", "Correo o contraseña inválidos.", None, {}
        if usuario["estado"] != "activo":
            return "estado_incompatible", "Usuario no activo.", None, {}
        cursor.execute(
            "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id_usuario = %s",
            (usuario["id_usuario"],),
        )
        access_token, refresh_token = _crear_tokens(usuario, cursor)
        conexion.commit()
        usuario = _usuario_por_id(usuario["id_usuario"], cursor)
        return "consultado", "Sesión iniciada correctamente.", {
            "usuario": _serializar_usuario(usuario),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def refrescar_sesion(refresh_token):
    # Valida refresh token activo, lo rota y devuelve tokens nuevos.
    try:
        payload = decodificar_token(refresh_token, tipo="refresh")
    except TokenError:
        return "no_autorizado", "Token de actualización inválido o expirado.", None, {}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT *
            FROM refresh_tokens
            WHERE token_hash = %s
              AND jti = %s
              AND estado = 'activo'
              AND fecha_expiracion > CURRENT_TIMESTAMP
            """,
            (hash_token(refresh_token), payload["jti"]),
        )
        token_db = cursor.fetchone()
        if not token_db:
            return "no_autorizado", "Refresh token revocado.", None, {}
        usuario = _usuario_por_id(payload["sub"], cursor)
        if not usuario or usuario["estado"] != "activo":
            return "no_autorizado", "Usuario no autorizado.", None, {}
        cursor.execute(
            "UPDATE refresh_tokens SET estado = 'revocado', fecha_revocacion = CURRENT_TIMESTAMP WHERE id_refresh_token = %s",
            (token_db["id_refresh_token"],),
        )
        access_token, nuevo_refresh = _crear_tokens(usuario, cursor)
        conexion.commit()
        return "consultado", "Sesión renovada correctamente.", {
            "usuario": _serializar_usuario(usuario),
            "access_token": access_token,
            "refresh_token": nuevo_refresh,
        }, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cerrar_sesion(refresh_token):
    # Revoca el refresh token recibido; el access token vence por expiracion.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if refresh_token:
            cursor.execute(
                """
                UPDATE refresh_tokens
                SET estado = 'revocado', fecha_revocacion = CURRENT_TIMESTAMP
                WHERE token_hash = %s
                """,
                (hash_token(refresh_token),),
            )
        conexion.commit()
        return "actualizado", "Sesión cerrada correctamente.", {}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def solicitar_recuperacion(datos):
    # Crea token de recuperacion sin revelar si el correo existe.
    correo = (datos.get("correo") or "").strip().lower()
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        usuario = _usuario_por_correo(correo, cursor) if correo else None
        token_plano = None
        if usuario:
            token_plano = secrets.token_urlsafe(32)
            cursor.execute(
                """
                INSERT INTO recuperaciones_contrasena (id_usuario, token_hash, fecha_expiracion, estado)
                VALUES (%s, %s, %s, 'pendiente')
                """,
                (usuario["id_usuario"], hash_token(token_plano), datetime.utcnow() + timedelta(hours=1)),
            )
        conexion.commit()
        data = {"dev_token": token_plano} if Config.APP_ENV == "development" and token_plano else {}
        return "consultado", "Si el correo existe, se enviarán instrucciones de recuperación.", data, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def restablecer_contrasena(datos):
    # Cambia la contrasena usando un token valido de un solo uso.
    token = (datos.get("token") or "").strip()
    nueva = datos.get("password") or ""
    if len(nueva) < 8:
        return "datos_invalidos", "Revise la nueva contraseña.", None, {"password": "Mínimo 8 caracteres."}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT *
            FROM recuperaciones_contrasena
            WHERE token_hash = %s
              AND estado = 'pendiente'
              AND fecha_expiracion > CURRENT_TIMESTAMP
            """,
            (hash_token(token),),
        )
        recuperacion = cursor.fetchone()
        if not recuperacion:
            return "datos_invalidos", "Token inválido o expirado.", None, {"token": "Token inválido."}
        cursor.execute(
            "UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s",
            (generate_password_hash(nueva), recuperacion["id_usuario"]),
        )
        cursor.execute(
            "UPDATE recuperaciones_contrasena SET estado = 'usado', fecha_uso = CURRENT_TIMESTAMP WHERE id_recuperacion = %s",
            (recuperacion["id_recuperacion"],),
        )
        cursor.execute(
            "UPDATE refresh_tokens SET estado = 'revocado', fecha_revocacion = CURRENT_TIMESTAMP WHERE id_usuario = %s",
            (recuperacion["id_usuario"],),
        )
        conexion.commit()
        return "actualizado", "Contraseña restablecida correctamente.", {}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def crear_verificacion_correo(id_usuario):
    # Genera token de verificacion para integrarlo con SMTP cuando haya credenciales.
    token_plano = secrets.token_urlsafe(32)
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO verificaciones_correo (id_usuario, token_hash, fecha_expiracion, estado)
            VALUES (%s, %s, %s, 'pendiente')
            """,
            (id_usuario, hash_token(token_plano), datetime.utcnow() + timedelta(hours=24)),
        )
        conexion.commit()
        return token_plano
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def verificar_correo(datos):
    # Marca correo como verificado usando token de un solo uso.
    token = (datos.get("token") or "").strip()
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT *
            FROM verificaciones_correo
            WHERE token_hash = %s
              AND estado = 'pendiente'
              AND fecha_expiracion > CURRENT_TIMESTAMP
            """,
            (hash_token(token),),
        )
        verificacion = cursor.fetchone()
        if not verificacion:
            return "datos_invalidos", "Token inválido o expirado.", None, {"token": "Token inválido."}
        cursor.execute(
            "UPDATE usuarios SET correo_verificado = 1 WHERE id_usuario = %s",
            (verificacion["id_usuario"],),
        )
        cursor.execute(
            "UPDATE verificaciones_correo SET estado = 'usado', fecha_uso = CURRENT_TIMESTAMP WHERE id_verificacion = %s",
            (verificacion["id_verificacion"],),
        )
        conexion.commit()
        return "actualizado", "Correo verificado correctamente.", {}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()
