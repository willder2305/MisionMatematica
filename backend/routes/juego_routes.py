import logging

from flask import Blueprint, jsonify, request
from mysql.connector import Error
from models.partida_juego import PartidaJuego
from services.auth_context import login_requerido, usuario_actual
from services.juego_adaptativo_service import (
    iniciar_partida_adaptativa,
    continuar_partida_adaptativa,
    obtener_contexto_juego_estudiante,
    obtener_partida_adaptativa,
    responder_partida_adaptativa,
)


juego_bp = Blueprint("juego_bp", __name__, url_prefix="/api/juego")
logger = logging.getLogger(__name__)


def _contexto_inicio_log(datos=None):
    # Registra solo identificadores tecnicos; no incluye tokens ni respuestas correctas.
    datos = datos or {}
    usuario = usuario_actual() or {}
    return {
        "endpoint": request.path,
        "usuario": usuario.get("id_usuario"),
        "asignacion": datos.get("id_asignacion"),
        "grado": datos.get("id_grado"),
        "tema": datos.get("id_tema"),
        "request_id": datos.get("request_id"),
    }


# Funcion: respuesta_error_servidor
# Descripcion:
#   Construye una respuesta uniforme para errores internos del modulo de juego.
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
#   Oculta errores tecnicos de MySQL y evita enviar stack traces al frontend.
def respuesta_error_servidor():
    return jsonify({
        "success": False,
        "message": "Ocurrio un error interno al procesar la solicitud.",
        "errors": {},
    }), 500


# Funcion: codigo_http_para_resultado
# Descripcion:
#   Traduce codigos internos del modelo PartidaJuego a codigos HTTP REST.
#
# Es llamada desde:
#   construir_respuesta() para responder operaciones de juego.
#
# Llama a:
#   No llama servicios externos; consulta un diccionario local.
#
# Parametros:
#   codigo: texto interno retornado por el modelo.
#
# Retorna:
#   Codigo HTTP numerico.
#
# Manejo de errores:
#   Si recibe un codigo desconocido, responde 400 de forma conservadora.
def codigo_http_para_resultado(codigo):
    return {
        "creado": 201,
        "actualizado": 200,
        "consultado": 200,
        "datos_invalidos": 400,
        "configuracion_incompleta": 409,
        "no_autorizado": 403,
        "no_existe": 404,
        "estado_incompatible": 409,
        "saldo_insuficiente": 409,
    }.get(codigo, 400)


# Verifica que la partida pertenezca al usuario autenticado antes de modificarla.
def validar_propietario_partida(id_partida, id_usuario):
    partida = obtener_partida_adaptativa(id_partida)
    if not partida:
        return "no_existe", "La partida solicitada no existe.", None, {}
    if partida.get("id_usuario") != id_usuario:
        return "no_autorizado", "No puede acceder a una partida de otro usuario.", None, {}
    return "consultado", "Partida consultada correctamente.", partida, {}


# Funcion: construir_respuesta
# Descripcion:
#   Construye el formato JSON uniforme de exito o error para el modulo de juego.
#
# Es llamada desde:
#   iniciar_partida(), consultar_partida(), registrar_correcto(), registrar_error() y salir_partida().
#
# Llama a:
#   codigo_http_para_resultado() y jsonify().
#
# Parametros:
#   codigo, mensaje, data y errors retornados por el modelo.
#
# Retorna:
#   Tupla Flask con cuerpo JSON y codigo HTTP.
#
# Manejo de errores:
#   Considera exitosos solo los codigos de creacion, actualizacion o consulta.
def construir_respuesta(codigo, mensaje, data=None, errors=None):
    exitoso = codigo in ("creado", "actualizado", "consultado")
    return jsonify({
        "success": exitoso,
        "message": mensaje,
        "data": data,
        "errors": errors or {},
    }), codigo_http_para_resultado(codigo)


# Funcion: iniciar_partida
# Descripcion:
#   Recibe tema o asignacion; backend resuelve grado y dificultad antes de crear la partida.
#
# Es llamada desde:
#   iniciarPartida() en frontend/src/services/juegoService.js.
#
# Llama a:
#   iniciar_partida_adaptativa() para validar, insertar y seleccionar ejercicio.
#
# Parametros:
#   JSON con id_tema para juego personal o id_asignacion para actividad docente.
#
# Retorna:
#   JSON con la partida creada y codigo HTTP 201, o errores 400/500.
#
# Manejo de errores:
#   Captura errores MySQL y devuelve una respuesta uniforme sin stack trace.
@juego_bp.route("/partidas", methods=["POST"])
@login_requerido
def iniciar_partida():
    datos = {}
    try:
        datos = request.get_json(silent=True) or {}
        usuario = usuario_actual()
        if usuario["rol"] != "estudiante":
            return construir_respuesta("no_autorizado", "Solo un estudiante puede iniciar partidas.", None, {})
        datos["id_usuario_autenticado"] = usuario["id_usuario"]
        return construir_respuesta(*iniciar_partida_adaptativa(datos))
    except Error:
        logger.exception("Error MySQL al iniciar partida", extra={"contexto_juego": _contexto_inicio_log(datos)})
        return respuesta_error_servidor()


@juego_bp.route("/contexto", methods=["GET"])
@login_requerido
def contexto_juego():
    try:
        return construir_respuesta(*obtener_contexto_juego_estudiante(usuario_actual()))
    except Error:
        return respuesta_error_servidor()
    except Exception:
        logger.exception("Error inesperado al obtener contexto de juego", extra={"contexto_juego": _contexto_inicio_log()})
        return respuesta_error_servidor()


# Funcion: consultar_partida
# Descripcion:
#   Consulta el estado actual de una partida adaptativa para sincronizar React.
#
# Es llamada desde:
#   obtenerPartida() en frontend/src/services/juegoService.js y pruebas manuales.
#
# Llama a:
#   obtener_partida_adaptativa().
#
# Parametros:
#   id_partida recibido desde la URL.
#
# Retorna:
#   JSON con la partida y HTTP 200, o HTTP 404 si no existe.
#
# Manejo de errores:
#   Captura errores de base de datos y retorna HTTP 500 controlado.
@juego_bp.route("/partidas/<int:id_partida>", methods=["GET"])
@login_requerido
def consultar_partida(id_partida):
    try:
        codigo, mensaje, partida, errors = validar_propietario_partida(id_partida, usuario_actual()["id_usuario"])
        return construir_respuesta(codigo, mensaje, partida, errors)
    except Error:
        return respuesta_error_servidor()


# Recibe la respuesta del estudiante y delega evaluacion, agente y siguiente pregunta.
@juego_bp.route("/partidas/<int:id_partida>/respuesta", methods=["POST"])
@login_requerido
def responder_partida(id_partida):
    try:
        datos = request.get_json(silent=True) or {}
        return construir_respuesta(*responder_partida_adaptativa(id_partida, datos, usuario_actual()["id_usuario"]))
    except Error:
        return respuesta_error_servidor()


@juego_bp.route("/partidas/<int:id_partida>/continuar", methods=["POST"])
@login_requerido
def continuar_partida(id_partida):
    # React solo confirma la accion; el backend valida saldo, estado y propiedad.
    try:
        usuario = usuario_actual()
        if usuario["rol"] != "estudiante":
            return construir_respuesta("no_autorizado", "Solo un estudiante puede continuar partidas.", None, {})
        datos = request.get_json(silent=True) or {}
        return construir_respuesta(*continuar_partida_adaptativa(id_partida, datos, usuario["id_usuario"]))
    except Error:
        return respuesta_error_servidor()


# Funcion: registrar_correcto
# Descripcion:
#   Registra un acierto temporal y avanza exactamente una casilla sin pasar de 10.
#
# Es llamada desde:
#   registrarCorrecto() en frontend/src/services/juegoService.js.
#
# Llama a:
#   PartidaJuego.registrar_correcto().
#
# Parametros:
#   id_partida recibido desde la URL.
#
# Retorna:
#   JSON con la partida actualizada.
#
# Manejo de errores:
#   Devuelve 409 si la partida ya finalizo y 500 controlado si falla MySQL.
@juego_bp.route("/partidas/<int:id_partida>/correcto", methods=["POST"])
@login_requerido
def registrar_correcto(id_partida):
    # Se conserva la ruta para clientes antiguos, pero no permite completar partidas sin intentos validos.
    return construir_respuesta("estado_incompatible", "Registra respuestas mediante el endpoint de respuesta.", None, {})


# Funcion: registrar_error
# Descripcion:
#   Registra un error temporal sin modificar la casilla actual.
#
# Es llamada desde:
#   registrarError() en frontend/src/services/juegoService.js.
#
# Llama a:
#   PartidaJuego.registrar_error().
#
# Parametros:
#   id_partida recibido desde la URL.
#
# Retorna:
#   JSON con la partida actualizada.
#
# Manejo de errores:
#   Devuelve 409 si la partida ya finalizo y 500 controlado si falla MySQL.
@juego_bp.route("/partidas/<int:id_partida>/error", methods=["POST"])
@login_requerido
def registrar_error(id_partida):
    # Se conserva la ruta para clientes antiguos, pero no altera vidas ni errores fuera del flujo validado.
    return construir_respuesta("estado_incompatible", "Registra respuestas mediante el endpoint de respuesta.", None, {})


# Funcion: salir_partida
# Descripcion:
#   Marca una partida en curso como abandonada despues de confirmacion del frontend.
#
# Es llamada desde:
#   salirPartida() en frontend/src/services/juegoService.js.
#
# Llama a:
#   PartidaJuego.abandonar().
#
# Parametros:
#   id_partida recibido desde la URL.
#
# Retorna:
#   JSON con estado abandonada y fecha_fin.
#
# Manejo de errores:
#   Devuelve 409 para partidas ya finalizadas y 500 controlado si falla MySQL.
@juego_bp.route("/partidas/<int:id_partida>/salir", methods=["POST"])
@login_requerido
def salir_partida(id_partida):
    try:
        codigo, mensaje, _, errors = validar_propietario_partida(id_partida, usuario_actual()["id_usuario"])
        if codigo != "consultado":
            return construir_respuesta(codigo, mensaje, None, errors)
        return construir_respuesta(*PartidaJuego.abandonar(id_partida))
    except Error:
        return respuesta_error_servidor()
