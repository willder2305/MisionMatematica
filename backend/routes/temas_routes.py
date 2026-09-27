from flask import Blueprint, jsonify, request
from mysql.connector import Error

from services.auth_context import login_requerido
from services.temas_service import obtener_temas_por_grado


temas_bp = Blueprint("temas_bp", __name__, url_prefix="/api/temas")


# Devuelve un error uniforme cuando MySQL falla.
def respuesta_error_servidor():
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


# Lista los temas activos disponibles para el grado seleccionado.
@temas_bp.route("", methods=["GET"])
@login_requerido
def listar_temas():
    try:
        id_grado = request.args.get("grado", type=int)
        if not id_grado:
            return jsonify({
                "success": False,
                "message": "El parametro grado es obligatorio.",
                "data": [],
                "errors": {"grado": "Seleccione un grado valido."},
            }), 400

        return jsonify({
            "success": True,
            "message": "Temas consultados correctamente.",
            "data": obtener_temas_por_grado(id_grado),
            "errors": {},
        }), 200
    except Error:
        return respuesta_error_servidor()
