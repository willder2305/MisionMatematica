from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import login_requerido, usuario_actual
from services.grupos_service import (
    cambiar_estado_pin,
    confirmar_actualizacion_grado,
    crear_pin,
    ingresar_con_pin,
    listar_codigos_grados_unicos,
    listar_codigos_secciones,
    listar_grupos,
    listar_pines_grupo,
    listar_secciones_grupo,
    regenerar_pin,
    validar_actualizacion_grado,
    validar_pin,
)


grupos_bp = Blueprint("grupos_bp", __name__, url_prefix="/api")


def _codigo_http(codigo):
    # Traduce codigos internos de grupos/PIN a HTTP.
    return {
        "creado": 201,
        "consultado": 200,
        "actualizado": 200,
        "datos_invalidos": 400,
        "no_autorizado": 403,
        "no_existe": 404,
        "duplicado": 409,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Respuesta JSON uniforme.
    return jsonify({
        "success": codigo in ("creado", "consultado", "actualizado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Oculta detalles de MySQL ante fallos internos.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


@grupos_bp.route("/grupos", methods=["GET"])
@login_requerido
def obtener_grupos():
    try:
        return _respuesta(*listar_grupos(usuario_actual()))
    except Error:
        return _error_servidor()


@grupos_bp.route("/grupos/<int:id_grupo>/secciones", methods=["GET"])
@login_requerido
def obtener_secciones_grupo(id_grupo):
    try:
        return _respuesta(*listar_secciones_grupo(usuario_actual(), id_grupo))
    except Error:
        return _error_servidor()


@grupos_bp.route("/grupos/<int:id_grupo>/pines", methods=["GET"])
@login_requerido
def obtener_pines_grupo(id_grupo):
    try:
        return _respuesta(*listar_pines_grupo(usuario_actual(), id_grupo))
    except Error:
        return _error_servidor()


@grupos_bp.route("/grupos/<int:id_grupo>/pines", methods=["POST"])
@login_requerido
def generar_pin_grupo(id_grupo):
    try:
        return _respuesta(*crear_pin(usuario_actual(), id_grupo, request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@grupos_bp.route("/codigos/secciones", methods=["GET"])
@login_requerido
def obtener_codigos_secciones():
    try:
        return _respuesta(*listar_codigos_secciones(usuario_actual()))
    except Error:
        return _error_servidor()


@grupos_bp.route("/codigos/grados-unicos", methods=["GET"])
@login_requerido
def obtener_codigos_grados_unicos():
    try:
        return _respuesta(*listar_codigos_grados_unicos(usuario_actual()))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/<int:id_pin>/estado", methods=["PATCH"])
@login_requerido
def estado_pin(id_pin):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_pin(usuario_actual(), id_pin, datos.get("estado")))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/<int:id_pin>/regenerar", methods=["POST"])
@login_requerido
def regenerar_pin_route(id_pin):
    try:
        return _respuesta(*regenerar_pin(usuario_actual(), id_pin))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/validar", methods=["POST"])
@login_requerido
def validar_pin_route():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*validar_pin(datos.get("pin") or ""))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/ingresar", methods=["POST"])
@login_requerido
def ingresar_pin_route():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*ingresar_con_pin(usuario_actual(), datos.get("pin") or ""))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/actualizar-grado/validar", methods=["POST"])
@login_requerido
def validar_actualizacion_grado_route():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*validar_actualizacion_grado(usuario_actual(), datos.get("pin") or ""))
    except Error:
        return _error_servidor()


@grupos_bp.route("/pines/actualizar-grado/confirmar", methods=["POST"])
@login_requerido
def confirmar_actualizacion_grado_route():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*confirmar_actualizacion_grado(usuario_actual(), datos.get("pin") or ""))
    except Error:
        return _error_servidor()
