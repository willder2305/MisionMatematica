from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.asignaciones_service import (
    actualizar_asignacion,
    cambiar_estado_asignacion,
    crear_asignacion,
    listar_contexto_asignaciones,
    listar_asignaciones,
)
from services.auth_context import login_requerido, usuario_actual


asignaciones_bp = Blueprint("asignaciones_bp", __name__, url_prefix="/api/asignaciones")


def _codigo_http(codigo):
    # Traduce codigos internos de asignaciones a HTTP.
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
    # Respuesta JSON uniforme del modulo.
    return jsonify({
        "success": codigo in ("creado", "consultado", "actualizado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Evita exponer detalles internos de MySQL.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


@asignaciones_bp.route("", methods=["GET"])
@login_requerido
def obtener_asignaciones():
    try:
        return _respuesta(*listar_asignaciones(usuario_actual()))
    except Error:
        return _error_servidor()


@asignaciones_bp.route("/contexto", methods=["GET"])
@login_requerido
def contexto_asignaciones():
    try:
        return _respuesta(*listar_contexto_asignaciones(usuario_actual()))
    except Error:
        return _error_servidor()


@asignaciones_bp.route("", methods=["POST"])
@login_requerido
def guardar_asignacion():
    try:
        return _respuesta(*crear_asignacion(usuario_actual(), request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@asignaciones_bp.route("/<int:id_asignacion>", methods=["PUT"])
@login_requerido
def editar_asignacion(id_asignacion):
    try:
        return _respuesta(*actualizar_asignacion(usuario_actual(), id_asignacion, request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@asignaciones_bp.route("/<int:id_asignacion>/estado", methods=["PATCH"])
@login_requerido
def estado_asignacion(id_asignacion):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_asignacion(usuario_actual(), id_asignacion, datos.get("estado")))
    except Error:
        return _error_servidor()
