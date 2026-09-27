from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import roles_requeridos, usuario_actual
from services.instituciones_service import (
    buscar_instituciones,
    listar_disponibilidad_secciones,
    obtener_o_crear_institucion,
)
from db import obtener_conexion


instituciones_bp = Blueprint("instituciones_bp", __name__, url_prefix="/api/instituciones")


def _codigo_http(codigo):
    # Traduce codigos internos de instituciones a HTTP.
    return {
        "creado": 201,
        "consultado": 200,
        "datos_invalidos": 400,
        "no_encontrado": 404,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Construye una respuesta JSON uniforme para React.
    return jsonify({
        "success": codigo in ("creado", "consultado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Evita exponer detalles tecnicos de MySQL.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


@instituciones_bp.route("", methods=["GET"])
@roles_requeridos("docente", "administrador")
def buscar():
    try:
        return _respuesta(*buscar_instituciones(request.args.get("q") or ""))
    except Error:
        return _error_servidor()


@instituciones_bp.route("", methods=["POST"])
@roles_requeridos("docente", "administrador")
def crear_o_reutilizar():
    try:
        datos = request.get_json(silent=True) or {}
        nombre = datos.get("nombre") or ""
        if not nombre.strip():
            return _respuesta("datos_invalidos", "Ingrese el nombre de la institución.", None, {"nombre": "Obligatorio."})

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            institucion = obtener_o_crear_institucion(nombre, cursor, datos.get("descripcion"))
            conexion.commit()
            return _respuesta("creado", "Institución disponible correctamente.", institucion, {})
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()
    except Error:
        return _error_servidor()


@instituciones_bp.route("/<int:id_institucion>/secciones-disponibles", methods=["GET"])
@roles_requeridos("docente")
def secciones_disponibles(id_institucion):
    try:
        return _respuesta(*listar_disponibilidad_secciones(usuario_actual()["id_usuario"], id_institucion))
    except Error:
        return _error_servidor()
