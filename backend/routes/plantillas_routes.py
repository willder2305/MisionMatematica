from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import roles_requeridos
from services.plantillas_service import (
    actualizar_plantilla,
    cambiar_estado_plantilla,
    crear_plantilla,
    listar_niveles,
    listar_plantillas,
    probar_generacion,
)


plantillas_bp = Blueprint("plantillas_bp", __name__, url_prefix="/api/plantillas")


# Devuelve un error uniforme si falla MySQL o el generador.
def respuesta_error_servidor():
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


def codigo_http(codigo):
    return {
        "creado": 201,
        "actualizado": 200,
        "consultado": 200,
        "datos_invalidos": 400,
        "no_existe": 404,
    }.get(codigo, 400)


def responder(codigo, mensaje, data=None, errors=None):
    return jsonify({
        "success": codigo in ("creado", "actualizado", "consultado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), codigo_http(codigo)


# Lista plantillas filtrables por grado, tema o estado.
@plantillas_bp.route("", methods=["GET"])
@roles_requeridos("docente", "administrador")
def obtener_plantillas():
    try:
        filtros = {
            "id_grado": request.args.get("grado", type=int),
            "id_tema": request.args.get("tema", type=int),
            "estado": request.args.get("estado"),
        }
        return jsonify({
            "success": True,
            "message": "Plantillas consultadas correctamente.",
            "data": listar_plantillas(filtros),
            "errors": {},
        }), 200
    except Error:
        return respuesta_error_servidor()


# Devuelve niveles activos para crear o editar plantillas.
@plantillas_bp.route("/niveles", methods=["GET"])
@roles_requeridos("docente", "administrador")
def obtener_niveles():
    try:
        return jsonify({
            "success": True,
            "message": "Niveles consultados correctamente.",
            "data": listar_niveles(),
            "errors": {},
        }), 200
    except Error:
        return respuesta_error_servidor()


# Crea una plantilla nueva despues de validar su configuracion.
@plantillas_bp.route("", methods=["POST"])
@roles_requeridos("docente", "administrador")
def crear():
    try:
        datos = request.get_json(silent=True) or {}
        return responder(*crear_plantilla(datos))
    except Error:
        return respuesta_error_servidor()


# Edita una plantilla existente sin alterar ejercicios ya generados.
@plantillas_bp.route("/<int:id_plantilla>", methods=["PUT"])
@roles_requeridos("docente", "administrador")
def actualizar(id_plantilla):
    try:
        datos = request.get_json(silent=True) or {}
        return responder(*actualizar_plantilla(id_plantilla, datos))
    except Error:
        return respuesta_error_servidor()


# Cambia el estado de publicacion de una plantilla.
@plantillas_bp.route("/<int:id_plantilla>/estado", methods=["PATCH"])
@roles_requeridos("docente", "administrador")
def cambiar_estado(id_plantilla):
    try:
        datos = request.get_json(silent=True) or {}
        return responder(*cambiar_estado_plantilla(id_plantilla, datos.get("estado")))
    except Error:
        return respuesta_error_servidor()


# Genera ejemplos temporales para revisar una plantilla desde administracion.
@plantillas_bp.route("/<int:id_plantilla>/probar", methods=["POST"])
@roles_requeridos("docente", "administrador")
def probar_plantilla(id_plantilla):
    try:
        datos = request.get_json(silent=True) or {}
        codigo, mensaje, data, errors = probar_generacion(id_plantilla, datos.get("cantidad", 3))
        exitoso = codigo == "consultado"
        return jsonify({
            "success": exitoso,
            "message": mensaje,
            "data": data,
            "errors": errors,
        }), 200 if exitoso else 404
    except (Error, ValueError):
        return respuesta_error_servidor()
