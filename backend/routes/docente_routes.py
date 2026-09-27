from flask import Blueprint, jsonify, request, send_file
from mysql.connector import Error

from services.auth_context import roles_requeridos, usuario_actual
from services.reportes_docente_service import (
    listar_estudiantes_docente,
    obtener_decisiones_agente,
    obtener_panel_docente,
    obtener_reporte_agente,
)
from services.report_export_service import exportar_reporte


docente_bp = Blueprint("docente_bp", __name__, url_prefix="/api/docente")


def _codigo_http(codigo):
    # Traduce codigos internos de reportes a HTTP.
    return {
        "consultado": 200,
        "datos_invalidos": 400,
        "no_autorizado": 403,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Mantiene respuesta uniforme para frontend.
    return jsonify({
        "success": codigo == "consultado",
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Oculta detalles internos de MySQL ante errores de reporte.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


@docente_bp.route("/panel", methods=["GET"])
@roles_requeridos("docente", "administrador")
def panel_docente():
    try:
        return _respuesta(*obtener_panel_docente(usuario_actual()))
    except Error:
        return _error_servidor()


@docente_bp.route("/estudiantes", methods=["GET"])
@roles_requeridos("docente", "administrador")
def estudiantes_docente():
    try:
        return _respuesta(*listar_estudiantes_docente(usuario_actual()))
    except Error:
        return _error_servidor()


@docente_bp.route("/reportes/agente", methods=["GET"])
@roles_requeridos("docente", "administrador")
def reporte_agente():
    try:
        return _respuesta(*obtener_reporte_agente(usuario_actual(), request.args))
    except Error:
        return _error_servidor()


@docente_bp.route("/reportes/agente/decisiones", methods=["GET"])
@roles_requeridos("docente", "administrador")
def decisiones_agente():
    try:
        limite = request.args.get("limite", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        return _respuesta(*obtener_decisiones_agente(usuario_actual(), request.args, limite=limite, offset=offset))
    except Error:
        return _error_servidor()


@docente_bp.route("/reportes/agente/exportar/<formato>", methods=["GET"])
@roles_requeridos("docente", "administrador")
def exportar_reporte_agente(formato):
    """Descarga el reporte docente ya filtrado y autorizado como PDF o XLSX."""
    try:
        if formato not in ("pdf", "xlsx"):
            return _respuesta("datos_invalidos", "Formato de exportación no permitido.", None, {})
        codigo, mensaje, reporte, errores = obtener_reporte_agente(usuario_actual(), request.args)
        if codigo != "consultado":
            return _respuesta(codigo, mensaje, reporte, errores)
        columnas = [
            ("estudiante", "Estudiante"), ("grado", "Grado"), ("tema", "Tema"),
            ("intentos", "Intentos"), ("aciertos", "Aciertos"), ("errores", "Errores"),
            ("porcentaje_aciertos", "Porcentaje"), ("nivel_actual", "Nivel"),
            ("ultima_practica", "Última actividad"),
        ]
        archivo = exportar_reporte(formato, "Reporte docente", columnas, reporte.get("temas_dificultad", []), "reporte_docente")
        if not archivo:
            return _respuesta("datos_invalidos", "No hay datos para exportar.", None, {})
        contenido, mimetype, nombre = archivo
        return send_file(contenido, mimetype=mimetype, as_attachment=True, download_name=nombre)
    except Error:
        return _error_servidor()
