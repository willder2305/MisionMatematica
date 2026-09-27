from flask import Blueprint, jsonify, request
from mysql.connector import Error
from models.grado import Grado
from services.auth_context import login_requerido, roles_requeridos

# Blueprint: grados_bp
# Descripcion:
#   Agrupa las rutas REST del CRUD de grados bajo el prefijo /api/grados.
#
# Es llamado desde:
#   backend/app.py cuando Flask registra los Blueprints de la aplicacion.
#
# Llama a:
#   Las funciones de este archivo, que a su vez llaman al modelo Grado.
#
# Retorna:
#   Un Blueprint listo para registrarse en Flask.
#
# Manejo de errores:
#   Cada ruta usa try/except para responder JSON uniforme sin exponer detalles tecnicos.
grados_bp = Blueprint("grados_bp", __name__, url_prefix="/api/grados")


# Funcion: respuesta_error_servidor
# Descripcion:
#   Construye una respuesta uniforme para errores internos del CRUD de grados.
#
# Es llamada desde:
#   Los bloques except de las rutas de este archivo.
#
# Llama a:
#   jsonify() para generar la respuesta JSON.
#
# Parametros:
#   No recibe parametros.
#
# Retorna:
#   JSON con success false y codigo HTTP 500.
#
# Manejo de errores:
#   Oculta errores tecnicos de MySQL, rutas internas y stack traces.
def respuesta_error_servidor():
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


# Funcion: codigo_http_para_resultado
# Descripcion:
#   Traduce codigos internos del modelo Grado a codigos HTTP.
#
# Es llamada desde:
#   crear_grado(), actualizar_grado(), cambiar_estado_grado() y eliminar_grado().
#
# Llama a:
#   No llama otros servicios; usa un diccionario local.
#
# Parametros:
#   codigo: texto retornado por el modelo Grado.
#
# Retorna:
#   Codigo HTTP numerico apropiado para la respuesta REST.
#
# Manejo de errores:
#   Si recibe un codigo desconocido, retorna 400 de forma conservadora.
def codigo_http_para_resultado(codigo):
    return {
        "creado": 201,
        "actualizado": 200,
        "eliminado": 200,
        "datos_invalidos": 400,
        "no_existe": 404,
        "duplicado": 409,
        "con_relaciones": 409,
    }.get(codigo, 400)


# Funcion: construir_respuesta
# Descripcion:
#   Construye respuestas JSON uniformes para operaciones de escritura del CRUD de grados.
#
# Es llamada desde:
#   Las rutas POST, PUT, PATCH y DELETE de /api/grados.
#
# Llama a:
#   codigo_http_para_resultado() y jsonify().
#
# Parametros:
#   codigo, mensaje, data y errors retornados por el modelo Grado.
#
# Retorna:
#   Tupla Flask con JSON y codigo HTTP.
#
# Manejo de errores:
#   Marca success en true solo para resultados exitosos y conserva errores por campo si existen.
def construir_respuesta(codigo, mensaje, data, errors):
    exitoso = codigo in ("creado", "actualizado", "eliminado")
    return jsonify({
        "success": exitoso,
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), codigo_http_para_resultado(codigo)


# Funcion: obtener_grados
# Descripcion:
#   Consulta todos los grados registrados con total de secciones y filtro opcional por estado.
#
# Es llamada desde:
#   obtenerGrados() en frontend/src/services/gradosService.js y desde la pagina GradosPage.jsx.
#
# Llama a:
#   Grado.obtener_todos() para consultar MySQL mediante el modelo.
#
# Parametros:
#   Query param opcional estado con valores activo o inactivo.
#
# Retorna:
#   JSON con lista de grados y codigo HTTP 200.
#
# Manejo de errores:
#   Si el filtro es invalido retorna 400; si MySQL falla retorna 500 uniforme.
@grados_bp.route("", methods=["GET"])
@login_requerido
def obtener_grados():
    try:
        estado = request.args.get("estado")
        if estado and estado not in ("activo", "inactivo"):
            return jsonify({
                "success": False,
                "message": "El filtro estado debe ser activo o inactivo.",
                "errors": {"estado": "Valor no permitido."},
            }), 400

        grados = Grado.obtener_todos(estado)
        return jsonify({
            "success": True,
            "message": "Grados obtenidos correctamente.",
            "data": grados,
        }), 200
    except Error:
        return respuesta_error_servidor()


# Funcion: obtener_opciones_grados
# Descripcion:
#   Consulta solo grados activos para usarlos como opciones del formulario de secciones.
#
# Es llamada desde:
#   obtenerOpcionesGrados() en frontend/src/services/gradosService.js y el selector de SeccionForm.
#
# Llama a:
#   Grado.obtener_opciones_activas() para consultar MySQL.
#
# Parametros:
#   No recibe parametros.
#
# Retorna:
#   JSON con id_grado, codigo_grado y nombre_grado de grados activos.
#
# Manejo de errores:
#   Si MySQL falla retorna 500 uniforme sin exponer detalles tecnicos.
@grados_bp.route("/opciones", methods=["GET"])
@login_requerido
def obtener_opciones_grados():
    try:
        grados = Grado.obtener_opciones_activas()
        return jsonify({
            "success": True,
            "message": "Opciones de grados obtenidas correctamente.",
            "data": grados,
        }), 200
    except Error:
        return respuesta_error_servidor()


# Funcion: obtener_grado
# Descripcion:
#   Consulta un grado especifico por su identificador.
#
# Es llamada desde:
#   obtenerGradoPorId() en frontend/src/services/gradosService.js o desde Postman.
#
# Llama a:
#   Grado.obtener_por_id() para consultar MySQL con total de secciones.
#
# Parametros:
#   id_grado recibido desde la URL.
#
# Retorna:
#   JSON con el grado y codigo HTTP 200, o 404 si no existe.
#
# Manejo de errores:
#   Si MySQL falla retorna 500 uniforme sin exponer detalles tecnicos.
@grados_bp.route("/<int:id_grado>", methods=["GET"])
@login_requerido
def obtener_grado(id_grado):
    try:
        grado = Grado.obtener_por_id(id_grado)
        if not grado:
            return jsonify({
                "success": False,
                "message": "El grado solicitado no existe.",
                "errors": {},
            }), 404

        return jsonify({
            "success": True,
            "message": "Grado obtenido correctamente.",
            "data": grado,
        }), 200
    except Error:
        return respuesta_error_servidor()


# Funcion: crear_grado
# Descripcion:
#   Recibe JSON, valida datos y crea un nuevo grado en MySQL.
#
# Es llamada desde:
#   crearGrado() en frontend/src/services/gradosService.js cuando GradosPage guarda un formulario nuevo.
#
# Llama a:
#   Grado.crear() para validar, revisar duplicados y ejecutar INSERT.
#
# Parametros:
#   JSON con codigo_grado, nombre_grado, descripcion, orden_visualizacion y estado.
#
# Retorna:
#   JSON uniforme con HTTP 201, 400, 409 o 500 segun corresponda.
#
# Manejo de errores:
#   El modelo hace rollback si falla la escritura; la ruta retorna 500 controlado si MySQL falla.
@grados_bp.route("", methods=["POST"])
@roles_requeridos("docente", "administrador")
def crear_grado():
    try:
        datos = request.get_json(silent=True) or {}
        return construir_respuesta(*Grado.crear(datos))
    except Error:
        return respuesta_error_servidor()


# Funcion: actualizar_grado
# Descripcion:
#   Actualiza los datos completos de un grado existente.
#
# Es llamada desde:
#   actualizarGrado() en frontend/src/services/gradosService.js cuando GradosPage guarda una edicion.
#
# Llama a:
#   Grado.actualizar() para validar existencia, duplicados y ejecutar UPDATE.
#
# Parametros:
#   id_grado desde la URL y JSON con campos editables del grado.
#
# Retorna:
#   JSON uniforme con HTTP 200, 400, 404, 409 o 500 segun corresponda.
#
# Manejo de errores:
#   El modelo hace rollback si falla la escritura; la ruta retorna 500 controlado si MySQL falla.
@grados_bp.route("/<int:id_grado>", methods=["PUT"])
@roles_requeridos("docente", "administrador")
def actualizar_grado(id_grado):
    try:
        datos = request.get_json(silent=True) or {}
        return construir_respuesta(*Grado.actualizar(id_grado, datos))
    except Error:
        return respuesta_error_servidor()


# Funcion: cambiar_estado_grado
# Descripcion:
#   Activa o desactiva un grado sin eliminar sus secciones relacionadas.
#
# Es llamada desde:
#   cambiarEstadoGrado() en frontend/src/services/gradosService.js al presionar Activar o Desactivar.
#
# Llama a:
#   Grado.cambiar_estado() para validar y actualizar MySQL.
#
# Parametros:
#   id_grado desde URL y JSON con estado activo o inactivo.
#
# Retorna:
#   JSON uniforme con HTTP 200, 400, 404 o 500 segun corresponda.
#
# Manejo de errores:
#   El modelo hace rollback si falla la escritura; la ruta retorna 500 controlado si MySQL falla.
@grados_bp.route("/<int:id_grado>/estado", methods=["PATCH"])
@roles_requeridos("docente", "administrador")
def cambiar_estado_grado(id_grado):
    try:
        datos = request.get_json(silent=True) or {}
        return construir_respuesta(*Grado.cambiar_estado(id_grado, datos.get("estado")))
    except Error:
        return respuesta_error_servidor()

