from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import login_requerido, usuario_actual
from services.auth_service import (
    cerrar_sesion,
    iniciar_sesion,
    refrescar_sesion,
    registrar_usuario,
    restablecer_contrasena,
    solicitar_recuperacion,
    verificar_correo,
)


auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


def _codigo_http(codigo):
    # Traduce codigos internos del servicio auth a HTTP.
    return {
        "creado": 201,
        "consultado": 200,
        "actualizado": 200,
        "datos_invalidos": 400,
        "credenciales_invalidas": 401,
        "no_autorizado": 401,
        "estado_incompatible": 403,
        "configuracion_faltante": 501,
        "duplicado": 409,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Mantiene el formato JSON usado por el resto del backend.
    return jsonify({
        "success": codigo in ("creado", "consultado", "actualizado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Evita exponer detalles internos ante errores MySQL.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        return _respuesta(*registrar_usuario(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        return _respuesta(*iniciar_sesion(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cerrar_sesion(datos.get("refresh_token")))
    except Error:
        return _error_servidor()


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*refrescar_sesion(datos.get("refresh_token") or ""))
    except Error:
        return _error_servidor()


@auth_bp.route("/me", methods=["GET"])
@login_requerido
def me():
    return _respuesta("consultado", "Usuario autenticado.", {"usuario": usuario_actual()}, {})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        return _respuesta(*solicitar_recuperacion(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        return _respuesta(*restablecer_contrasena(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    try:
        return _respuesta(*verificar_correo(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()
