from functools import wraps

from flask import g, jsonify, request

from db import obtener_conexion
from services.jwt_service import TokenError, decodificar_token


def _usuario_por_id(id_usuario):
    # Consulta el usuario activo asociado al token recibido.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.id_usuario, u.nombres, u.apellidos, u.correo, u.estado,
                   u.correo_verificado, u.onboarding_completado, r.nombre AS rol
            FROM usuarios u
            INNER JOIN roles r ON r.id_rol = u.id_rol
            WHERE u.id_usuario = %s
            """,
            (id_usuario,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()


def usuario_actual():
    # Devuelve el usuario autenticado disponible durante la peticion actual.
    return getattr(g, "usuario_actual", None)


def login_requerido(fn):
    # Protege una ruta validando token Bearer y usuario activo.
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Autenticación requerida.", "errors": {}}), 401
        token = auth_header.replace("Bearer ", "", 1).strip()
        try:
            payload = decodificar_token(token, tipo="access")
        except TokenError:
            return jsonify({"success": False, "message": "Token inválido o expirado.", "errors": {}}), 401
        usuario = _usuario_por_id(payload["sub"])
        if not usuario or usuario["estado"] != "activo":
            return jsonify({"success": False, "message": "Usuario no autorizado.", "errors": {}}), 401
        g.usuario_actual = usuario
        return fn(*args, **kwargs)

    return wrapper


def cargar_usuario_opcional():
    # Carga usuario si hay Bearer valido; deja la peticion anonima si no existe token.
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "", 1).strip()
    try:
        payload = decodificar_token(token, tipo="access")
    except TokenError:
        return None
    usuario = _usuario_por_id(payload["sub"])
    if usuario and usuario["estado"] == "activo":
        g.usuario_actual = usuario
        return usuario
    return None


def roles_requeridos(*roles):
    # Restringe una ruta autenticada a uno o varios roles backend.
    def decorator(fn):
        @wraps(fn)
        @login_requerido
        def wrapper(*args, **kwargs):
            usuario = usuario_actual()
            if usuario["rol"] not in roles:
                return jsonify({"success": False, "message": "Permisos insuficientes.", "errors": {}}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
