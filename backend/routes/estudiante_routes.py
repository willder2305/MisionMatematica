import logging

from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.asignaciones_service import listar_asignaciones_estudiante
from services.auth_context import roles_requeridos, usuario_actual
from services.juego_adaptativo_service import obtener_contexto_juego_estudiante
from services.progreso_service import (
    obtener_historial_estudiante,
    obtener_panel_estudiante,
    obtener_progreso_estudiante,
)
from services.personalizacion_service import (
    actualizar_mapa_estudiante,
    actualizar_personaje_estudiante,
    comprar_item_estudiante,
    obtener_saldo_estudiante,
    obtener_tienda_estudiante,
)


estudiante_bp = Blueprint("estudiante_bp", __name__, url_prefix="/api/estudiante")
logger = logging.getLogger(__name__)


def _codigo_http(codigo):
    # Traduce codigos internos del modulo estudiante a HTTP.
    return {
        "consultado": 200,
        "articulo_ya_adquirido": 409,
        "datos_invalidos": 400,
        "no_autorizado": 403,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Mantiene el formato JSON uniforme de la API.
    return jsonify({
        "success": codigo == "consultado",
        "code": codigo,
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Oculta detalles internos ante errores de MySQL.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


@estudiante_bp.route("/panel", methods=["GET"])
@roles_requeridos("estudiante")
def panel():
    try:
        return _respuesta(*obtener_panel_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/progreso", methods=["GET"])
@roles_requeridos("estudiante")
def progreso():
    try:
        return _respuesta(*obtener_progreso_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/historial", methods=["GET"])
@roles_requeridos("estudiante")
def historial():
    try:
        limite = request.args.get("limite", default=20, type=int)
        offset = request.args.get("offset", default=0, type=int)
        return _respuesta(*obtener_historial_estudiante(usuario_actual(), limite=limite, offset=offset))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/temas", methods=["GET"])
@roles_requeridos("estudiante")
def temas():
    try:
        codigo, mensaje, data, errors = obtener_contexto_juego_estudiante(usuario_actual())
        temas_data = {"temas": (data or {}).get("temas", [])} if data else None
        return _respuesta(codigo, mensaje, temas_data, errors)
    except Error:
        return _error_servidor()


@estudiante_bp.route("/asignaciones", methods=["GET"])
@roles_requeridos("estudiante")
def asignaciones():
    try:
        return _respuesta(*listar_asignaciones_estudiante(usuario_actual()))
    except Error:
        logger.exception("Error MySQL al listar asignaciones del estudiante")
        return _error_servidor()


@estudiante_bp.route("/tienda", methods=["GET"])
@roles_requeridos("estudiante")
def tienda():
    # Entrega catalogo e inventario con precios y saldo calculados por backend.
    try:
        return _respuesta(*obtener_tienda_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/monedas", methods=["GET"])
@roles_requeridos("estudiante")
def monedas():
    # El saldo solo se consulta desde el monedero del estudiante autenticado.
    try:
        return _respuesta(*obtener_saldo_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/inventario", methods=["GET"])
@roles_requeridos("estudiante")
def inventario():
    # Reutiliza el mismo contrato para evitar dos fuentes de verdad del inventario.
    try:
        return _respuesta(*obtener_tienda_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/tienda/comprar", methods=["POST"])
@roles_requeridos("estudiante")
def comprar():
    # La compra recibe solo el id del item; nunca precio ni usuario desde React.
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*comprar_item_estudiante(usuario_actual(), datos.get("id_item")))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/personalizacion", methods=["GET"])
@roles_requeridos("estudiante")
def personalizacion():
    try:
        return _respuesta(*obtener_tienda_estudiante(usuario_actual()))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/personalizacion/personaje", methods=["PUT"])
@roles_requeridos("estudiante")
def actualizar_personaje():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*actualizar_personaje_estudiante(usuario_actual(), datos.get("personaje")))
    except Error:
        return _error_servidor()


@estudiante_bp.route("/personalizacion/mapa", methods=["PUT"])
@roles_requeridos("estudiante")
def actualizar_mapa():
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*actualizar_mapa_estudiante(usuario_actual(), datos.get("modo_mapa"), datos.get("mapa")))
    except Error:
        return _error_servidor()
