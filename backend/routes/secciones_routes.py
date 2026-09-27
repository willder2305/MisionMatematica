from flask import Blueprint, jsonify, request
from mysql.connector import Error
from models.seccion import Seccion
from services.auth_context import roles_requeridos, usuario_actual

secciones_bp = Blueprint("secciones_bp", __name__, url_prefix="/api/secciones")


# Funcion: respuesta_error_servidor
# Descripcion:
#   Construye una respuesta uniforme cuando ocurre un error interno en el CRUD de secciones.
#
# Es llamada desde:
#   Todas las rutas Flask de este archivo dentro de sus bloques except.
#
# Llama a:
#   jsonify() para convertir la respuesta a JSON.
#
# Retorna:
#   Una respuesta JSON con success false y codigo HTTP 500.
#
# Manejo de errores:
#   No expone detalles tecnicos de MySQL al frontend.
def respuesta_error_servidor():
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


# Funcion: codigo_http_para_resultado
# Descripcion:
#   Traduce codigos internos del modelo Seccion a codigos HTTP REST.
#
# Es llamada desde:
#   Las rutas POST, PUT, PATCH y DELETE de este archivo.
#
# Llama a:
#   No llama a otros servicios; solo consulta un diccionario local.
#
# Retorna:
#   Un codigo HTTP numerico.
#
# Manejo de errores:
#   Si recibe un codigo no registrado, retorna 400 como respuesta conservadora.
def codigo_http_para_resultado(codigo):
    return {
        "creado": 201,
        "actualizado": 200,
        "eliminado": 200,
        "datos_invalidos": 400,
        "grado_no_existe": 404,
        "no_existe": 404,
        "duplicado": 409,
        "con_relaciones": 409,
    }.get(codigo, 400)


# Funcion: obtener_secciones
# Descripcion:
#   Consulta todas las secciones registradas en la base de datos, con filtro opcional por estado.
#
# Es llamada desde:
#   La funcion obtenerSecciones() en frontend/src/services/seccionesService.js.
#
# Llama a:
#   Seccion.obtener_todas() para consultar MySQL mediante el modelo Seccion.
#
# Retorna:
#   Una respuesta JSON con lista de secciones y codigo HTTP 200.
#
# Manejo de errores:
#   Si ocurre un error de base de datos, retorna un mensaje JSON uniforme con codigo HTTP 500.
@secciones_bp.route("", methods=["GET"])
@roles_requeridos("docente", "administrador")
def obtener_secciones():
    try:
        estado = request.args.get("estado")
        if estado and estado not in ("activo", "inactivo"):
            return jsonify({
                "success": False,
                "message": "El filtro estado debe ser activo o inactivo.",
                "errors": {"estado": "Valor no permitido."},
            }), 400

        secciones = Seccion.obtener_todas(estado, usuario_actual())
        return jsonify({
            "success": True,
            "message": "Secciones consultadas correctamente.",
            "data": secciones,
        }), 200
    except Error:
        return respuesta_error_servidor()


# Funcion: obtener_seccion
# Descripcion:
#   Busca una seccion especifica por su identificador.
#
# Es llamada desde:
#   La funcion obtenerSeccionPorId() en frontend/src/services/seccionesService.js o desde Postman.
#
# Llama a:
#   Seccion.obtener_por_id() para consultar MySQL.
#
# Retorna:
#   Una respuesta JSON con la seccion y codigo HTTP 200, o HTTP 404 si no existe.
#
# Manejo de errores:
#   Si ocurre un error de base de datos, retorna un mensaje JSON uniforme con codigo HTTP 500.
@secciones_bp.route("/<int:id_seccion>", methods=["GET"])
@roles_requeridos("docente", "administrador")
def obtener_seccion(id_seccion):
    try:
        seccion = Seccion.obtener_por_id(id_seccion)
        if not seccion:
            return jsonify({
                "success": False,
                "message": "La seccion solicitada no existe.",
                "errors": {},
            }), 404

        return jsonify({
            "success": True,
            "message": "Seccion consultada correctamente.",
            "data": seccion,
        }), 200
    except Error:
        return respuesta_error_servidor()


# Funcion: crear_seccion
# Descripcion:
#   Recibe datos JSON y crea una nueva seccion asociada a un grado existente.
#
# Es llamada desde:
#   crearSeccion() en frontend/src/services/seccionesService.js cuando SeccionesPage guarda un formulario nuevo.
#
# Llama a:
#   Seccion.crear() para validar y guardar el registro en MySQL.
#
# Retorna:
#   Una respuesta JSON uniforme con codigo HTTP 201, 400, 404 o 409 segun el resultado.
#
# Manejo de errores:
#   Si ocurre un error interno, el modelo hace rollback y la ruta retorna HTTP 500 sin exponer MySQL.
@secciones_bp.route("", methods=["POST"])
@roles_requeridos("docente")
def crear_seccion():
    try:
        datos = request.get_json(silent=True) or {}
        codigo, mensaje, seccion = Seccion.crear(datos, usuario_actual())
        http_status = codigo_http_para_resultado(codigo)
        return jsonify({
            "success": codigo == "creado",
            "message": mensaje,
            "data": seccion,
            "errors": {} if codigo == "creado" else {"resultado": codigo},
        }), http_status
    except Error:
        return respuesta_error_servidor()


# Funcion: actualizar_seccion
# Descripcion:
#   Actualiza los datos completos de una seccion existente.
#
# Es llamada desde:
#   actualizarSeccion() en frontend/src/services/seccionesService.js cuando SeccionesPage guarda una edicion.
#
# Llama a:
#   Seccion.actualizar() para validar duplicados, grado y estado antes de actualizar MySQL.
#
# Retorna:
#   Una respuesta JSON uniforme con codigo HTTP 200, 400, 404 o 409 segun el resultado.
#
# Manejo de errores:
#   Si ocurre un error interno, el modelo hace rollback y la ruta retorna HTTP 500 sin exponer MySQL.
@secciones_bp.route("/<int:id_seccion>", methods=["PUT"])
@roles_requeridos("docente", "administrador")
def actualizar_seccion(id_seccion):
    try:
        datos = request.get_json(silent=True) or {}
        codigo, mensaje, seccion = Seccion.actualizar(id_seccion, datos)
        http_status = codigo_http_para_resultado(codigo)
        return jsonify({
            "success": codigo == "actualizado",
            "message": mensaje,
            "data": seccion,
            "errors": {} if codigo == "actualizado" else {"resultado": codigo},
        }), http_status
    except Error:
        return respuesta_error_servidor()


# Funcion: cambiar_estado_seccion
# Descripcion:
#   Cambia el estado de una seccion a activo o inactivo sin eliminarla.
#
# Es llamada desde:
#   cambiarEstadoSeccion() en frontend/src/services/seccionesService.js al presionar el boton de estado.
#
# Llama a:
#   Seccion.cambiar_estado() para validar y actualizar el campo estado en MySQL.
#
# Retorna:
#   Una respuesta JSON uniforme con codigo HTTP 200, 400 o 404 segun el resultado.
#
# Manejo de errores:
#   Si ocurre un error interno, el modelo hace rollback y la ruta retorna HTTP 500 sin exponer MySQL.
@secciones_bp.route("/<int:id_seccion>/estado", methods=["PATCH"])
@roles_requeridos("docente", "administrador")
def cambiar_estado_seccion(id_seccion):
    try:
        datos = request.get_json(silent=True) or {}
        codigo, mensaje, seccion = Seccion.cambiar_estado(id_seccion, datos.get("estado"))
        http_status = codigo_http_para_resultado(codigo)
        return jsonify({
            "success": codigo == "actualizado",
            "message": mensaje,
            "data": seccion,
            "errors": {} if codigo == "actualizado" else {"resultado": codigo},
        }), http_status
    except Error:
        return respuesta_error_servidor()
