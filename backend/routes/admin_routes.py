from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from mysql.connector import Error

from services.auditoria_service import listar_auditoria_admin
from services.admin_service import (
    actualizar_ejercicio_admin,
    actualizar_regla_admin,
    actualizar_tema_admin,
    cambiar_estado_ejercicio_admin,
    cambiar_estado_regla_admin,
    cambiar_estado_tema_admin,
    cambiar_estado_usuario,
    cambiar_rol_usuario,
    crear_ejercicio_admin,
    crear_tema_admin,
    listar_ejercicios_admin,
    listar_catalogos_reportes_admin,
    listar_reglas_admin,
    listar_temas_admin,
    listar_usuarios,
    obtener_reporte_institucional_admin,
    obtener_panel_admin,
)
from services.auth_context import roles_requeridos, usuario_actual
from services.report_export_service import exportar_reporte


admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


def _codigo_http(codigo):
    # Traduce codigos internos de administracion a HTTP.
    return {
        "creado": 201,
        "actualizado": 200,
        "consultado": 200,
        "datos_invalidos": 400,
        "no_autorizado": 403,
        "no_existe": 404,
        "conflicto": 409,
    }.get(codigo, 400)


def _respuesta(codigo, mensaje, data=None, errors=None):
    # Mantiene el formato uniforme de la API.
    return jsonify({
        "success": codigo in ("creado", "actualizado", "consultado"),
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), _codigo_http(codigo)


def _error_servidor():
    # Evita exponer trazas o consultas SQL al frontend.
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "data": None,
        "errors": {},
    }), 500


def _metadata_reporte_global(args):
    # Anota fecha y filtros legibles en ambos formatos de exportación.
    etiquetas = {
        "modalidad": "Modalidad", "id_institucion": "Institución", "id_grado_base": "Grado",
        "id_tema": "Tema", "buscar_estudiante": "Estudiante", "fecha_inicio": "Desde", "fecha_fin": "Hasta",
    }
    filtros = [f"{etiquetas[clave]}: {args.get(clave)}" for clave in etiquetas if args.get(clave)]
    return f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Filtros: {'; '.join(filtros) if filtros else 'Todos'}"


@admin_bp.route("/panel", methods=["GET"])
@roles_requeridos("administrador")
def panel_admin():
    try:
        return _respuesta(*obtener_panel_admin())
    except Error:
        return _error_servidor()


@admin_bp.route("/usuarios", methods=["GET"])
@roles_requeridos("administrador")
def usuarios_admin():
    try:
        filtros = {
            "rol": request.args.get("rol"),
            "estado": request.args.get("estado"),
            "busqueda": request.args.get("busqueda"),
        }
        return _respuesta(*listar_usuarios(filtros))
    except Error:
        return _error_servidor()


@admin_bp.route("/usuarios/<int:id_usuario>/estado", methods=["PATCH"])
@roles_requeridos("administrador")
def estado_usuario_admin(id_usuario):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_usuario(id_usuario, datos.get("estado"), usuario_actual()["id_usuario"]))
    except Error:
        return _error_servidor()


@admin_bp.route("/usuarios/<int:id_usuario>/rol", methods=["PATCH"])
@roles_requeridos("administrador")
def rol_usuario_admin(id_usuario):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_rol_usuario(id_usuario, datos.get("rol"), usuario_actual()["id_usuario"]))
    except Error:
        return _error_servidor()


@admin_bp.route("/temas", methods=["GET"])
@roles_requeridos("administrador")
def temas_admin():
    try:
        filtros = {
            "id_grado": request.args.get("id_grado", type=int),
            "estado": request.args.get("estado"),
        }
        return _respuesta(*listar_temas_admin(filtros))
    except Error:
        return _error_servidor()


@admin_bp.route("/temas", methods=["POST"])
@roles_requeridos("administrador")
def crear_tema():
    try:
        return _respuesta(*crear_tema_admin(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@admin_bp.route("/temas/<int:id_tema>", methods=["PUT"])
@roles_requeridos("administrador")
def actualizar_tema(id_tema):
    try:
        return _respuesta(*actualizar_tema_admin(id_tema, request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@admin_bp.route("/temas/<int:id_tema>/estado", methods=["PATCH"])
@roles_requeridos("administrador")
def estado_tema(id_tema):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_tema_admin(id_tema, datos.get("estado")))
    except Error:
        return _error_servidor()


@admin_bp.route("/ejercicios", methods=["GET"])
@roles_requeridos("administrador")
def ejercicios_admin():
    try:
        filtros = {
            "id_tema": request.args.get("id_tema", type=int),
            "id_nivel": request.args.get("id_nivel", type=int),
            "estado": request.args.get("estado"),
        }
        return _respuesta(*listar_ejercicios_admin(filtros))
    except Error:
        return _error_servidor()


@admin_bp.route("/ejercicios", methods=["POST"])
@roles_requeridos("administrador")
def crear_ejercicio():
    try:
        return _respuesta(*crear_ejercicio_admin(request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@admin_bp.route("/ejercicios/<int:id_ejercicio>", methods=["PUT"])
@roles_requeridos("administrador")
def actualizar_ejercicio(id_ejercicio):
    try:
        return _respuesta(*actualizar_ejercicio_admin(id_ejercicio, request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@admin_bp.route("/ejercicios/<int:id_ejercicio>/estado", methods=["PATCH"])
@roles_requeridos("administrador")
def estado_ejercicio(id_ejercicio):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_ejercicio_admin(id_ejercicio, datos.get("estado")))
    except Error:
        return _error_servidor()


@admin_bp.route("/reglas", methods=["GET"])
@roles_requeridos("administrador")
def reglas_admin():
    try:
        return _respuesta(*listar_reglas_admin())
    except Error:
        return _error_servidor()


@admin_bp.route("/reglas/<int:id_regla>", methods=["PUT"])
@roles_requeridos("administrador")
def actualizar_regla(id_regla):
    try:
        return _respuesta(*actualizar_regla_admin(id_regla, request.get_json(silent=True) or {}))
    except Error:
        return _error_servidor()


@admin_bp.route("/reglas/<int:id_regla>/estado", methods=["PATCH"])
@roles_requeridos("administrador")
def estado_regla(id_regla):
    try:
        datos = request.get_json(silent=True) or {}
        return _respuesta(*cambiar_estado_regla_admin(id_regla, datos.get("estado")))
    except Error:
        return _error_servidor()


@admin_bp.route("/auditoria", methods=["GET"])
@roles_requeridos("administrador")
def auditoria_admin():
    try:
        filtros = {
            "accion": request.args.get("accion"),
            "entidad": request.args.get("entidad"),
            "resultado": request.args.get("resultado"),
            "limite": request.args.get("limite", type=int),
        }
        return _respuesta(*listar_auditoria_admin(filtros))
    except Error:
        return _error_servidor()


@admin_bp.route("/reportes/filtros", methods=["GET"])
@roles_requeridos("administrador")
def reportes_filtros_admin():
    try:
        return _respuesta(*listar_catalogos_reportes_admin(request.args))
    except Error:
        return _error_servidor()


@admin_bp.route("/reportes/institucional", methods=["GET"])
@roles_requeridos("administrador")
def reporte_institucional_admin():
    try:
        return _respuesta(*obtener_reporte_institucional_admin(request.args))
    except Error:
        return _error_servidor()


@admin_bp.route("/reportes/institucional/exportar/<formato>", methods=["GET"])
@roles_requeridos("administrador")
def exportar_reporte_institucional_admin(formato):
    """Descarga el reporte institucional filtrado sin ampliar permisos del administrador."""
    try:
        if formato not in ("pdf", "xlsx"):
            return _respuesta("datos_invalidos", "Formato de exportación no permitido.", None, {})
        codigo, mensaje, reporte, errores = obtener_reporte_institucional_admin(request.args)
        if codigo != "consultado":
            return _respuesta(codigo, mensaje, reporte, errores)
        columnas = [
            ("estudiante", "Estudiante"), ("modalidad", "Modalidad"), ("institucion", "Institución"),
            ("docente", "Docente"), ("grado", "Grado"), ("seccion", "Sección"),
            ("asignacion", "Asignación"), ("tema", "Tema"), ("intentos", "Intentos"),
            ("correctos", "Correctos"), ("incorrectos", "Incorrectos"), ("precision", "Acierto"),
            ("mejora", "Mejora"), ("partidas_completadas", "Partidas"), ("nivel_actual", "Nivel actual"),
            ("ultima_actividad", "Última actividad"),
        ]
        archivo = exportar_reporte(
            formato,
            "Misión Matemática / Reporte global de estudiantes",
            columnas,
            reporte.get("filas", []),
            "reporte_estudiantes",
            _metadata_reporte_global(request.args),
        )
        if not archivo:
            return _respuesta("datos_invalidos", "No hay datos para exportar.", None, {})
        contenido, mimetype, nombre = archivo
        return send_file(contenido, mimetype=mimetype, as_attachment=True, download_name=nombre)
    except Error:
        return _error_servidor()


@admin_bp.route("/reportes/estudiantes", methods=["GET"])
@roles_requeridos("administrador")
def reporte_estudiantes_admin():
    """Ruta canónica del reporte global; conserva la ruta institucional previa."""
    try:
        return _respuesta(*obtener_reporte_institucional_admin(request.args))
    except Error:
        return _error_servidor()


@admin_bp.route("/reportes/estudiantes/<formato>", methods=["GET"])
@roles_requeridos("administrador")
def exportar_reporte_estudiantes_admin(formato):
    """Exporta el reporte global aplicando los filtros visibles actuales."""
    return exportar_reporte_institucional_admin("xlsx" if formato == "excel" else formato)
