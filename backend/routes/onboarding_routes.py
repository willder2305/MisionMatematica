from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import login_requerido, usuario_actual
from services.onboarding_service import completar_onboarding, obtener_personajes_iniciales_onboarding, obtener_perfil_onboarding


onboarding_bp = Blueprint("onboarding_bp", __name__, url_prefix="/api/onboarding")


def _codigo_http(codigo):
    # Traduce codigos internos de onboarding a codigos HTTP.
    return {
        "consultado": 200,
        "actualizado": 200,
        "datos_invalidos": 400,
        "no_autorizado": 403,
        "no_encontrado": 404,
        "conflicto": 409,
        "configuracion_invalida": 422,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Devuelve JSON uniforme como el resto de rutas.
    return jsonify({
        "success": codigo in ("consultado", "actualizado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Oculta errores tecnicos de MySQL.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


@onboarding_bp.route("", methods=["GET"])
@login_requerido
def obtener_onboarding():
    try:
        return _respuesta(*obtener_perfil_onboarding(usuario_actual()))
    except Error:
        return _error_servidor()


@onboarding_bp.route("/personajes-iniciales", methods=["GET"])
@login_requerido
def personajes_iniciales():
    try:
        return _respuesta(*obtener_personajes_iniciales_onboarding(usuario_actual()))
    except Error:
        return _error_servidor()


@onboarding_bp.route("", methods=["POST"])
@login_requerido
def guardar_onboarding():
    try:
        return _respuesta(*completar_onboarding(usuario_actual(), request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()
