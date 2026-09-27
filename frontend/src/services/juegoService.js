import api from "./apiClient";

/**
 * Funcion: extraerDatos
 *
 * Descripcion:
 * Normaliza la respuesta recibida desde Flask para entregar el cuerpo JSON uniforme.
 *
 * Es llamada desde:
 * Todas las funciones exportadas por juegoService.js.
 *
 * Llama a:
 * No llama endpoints; lee response.data.
 *
 * Parametros:
 * response retornado por axios.
 *
 * Resultado:
 * Devuelve success, message, data y errors.
 *
 * Manejo de errores:
 * No captura errores; axios los propaga al catch de cada funcion.
 */
const extraerDatos = (response) => response.data;

/**
 * Funcion: manejarError
 *
 * Descripcion:
 * Convierte errores de axios en errores legibles para JuegoPage.
 *
 * Es llamada desde:
 * iniciarPartida(), obtenerPartida(), registrarCorrecto(), registrarError() y salirPartida().
 *
 * Llama a:
 * No llama servicios externos; lee error.response cuando existe.
 *
 * Parametros:
 * error generado por axios.
 *
 * Resultado:
 * Lanza un Error con message y errors.
 *
 * Manejo de errores:
 * Si el backend no responde, usa un mensaje de conexion claro.
 */
const manejarError = (error) => {
  const mensaje =
    error.response?.data?.message ||
    "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  const errorControlado = new Error(mensaje);
  errorControlado.errors = error.response?.data?.errors || {};
  throw errorControlado;
};

/**
 * Funcion: iniciarPartida
 *
 * Descripcion:
 * Consume POST /api/juego/partidas para crear una partida en casilla inicial.
 *
 * Es llamada desde:
 * confirmarPersonaje() en JuegoPage.jsx.
 *
 * Llama a:
 * POST /juego/partidas mediante el cliente Axios compartido.
 *
 * Parametros:
 * datos con personaje y mapa.
 *
 * Resultado:
 * Devuelve la partida creada por Flask.
 *
 * Manejo de errores:
 * Propaga errores de validacion o conexion para mostrarlos en la pantalla.
 */
export const iniciarPartida = async (datos) => {
  try {
    const response = await api.post("/juego/partidas", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerContextoJuego = async () => {
  try {
    const response = await api.get("/juego/contexto");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: obtenerPartida
 *
 * Descripcion:
 * Consume GET /api/juego/partidas/<id> para consultar el estado persistido.
 *
 * Es llamada desde:
 * Pruebas de sincronizacion y JuegoPage.jsx si necesita refrescar estado.
 *
 * Llama a:
 * GET /juego/partidas/{idPartida}.
 *
 * Parametros:
 * idPartida identificador de la partida.
 *
 * Resultado:
 * Devuelve la partida consultada.
 *
 * Manejo de errores:
 * Propaga 404 o errores de conexion.
 */
export const obtenerPartida = async (idPartida) => {
  try {
    const response = await api.get(`/juego/partidas/${idPartida}`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const responderPregunta = async (idPartida, datos) => {
  try {
    const response = await api.post(`/juego/partidas/${idPartida}/respuesta`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

// React confirma la continuacion; el backend valida el costo y conserva la misma partida.
export const continuarPartida = async (idPartida, requestId) => {
  try {
    const response = await api.post(`/juego/partidas/${idPartida}/continuar`, { request_id: requestId });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: registrarCorrecto
 *
 * Descripcion:
 * Consume POST /correcto para registrar un acierto y avanzar una casilla en backend.
 *
 * Es llamada desde:
 * manejarRespuestaCorrecta() en JuegoPage.jsx.
 *
 * Llama a:
 * POST /juego/partidas/{idPartida}/correcto.
 *
 * Parametros:
 * idPartida identificador de la partida.
 *
 * Resultado:
 * Devuelve la partida con casilla actualizada.
 *
 * Manejo de errores:
 * Propaga 409 si la partida ya finalizo o errores de conexion.
 */
export const registrarCorrecto = async (idPartida) => {
  try {
    const response = await api.post(`/juego/partidas/${idPartida}/correcto`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: registrarError
 *
 * Descripcion:
 * Consume POST /error para registrar un error sin avanzar de casilla.
 *
 * Es llamada desde:
 * manejarRespuestaIncorrecta() en JuegoPage.jsx.
 *
 * Llama a:
 * POST /juego/partidas/{idPartida}/error.
 *
 * Parametros:
 * idPartida identificador de la partida.
 *
 * Resultado:
 * Devuelve la partida con total_errores incrementado.
 *
 * Manejo de errores:
 * Propaga 409 si la partida ya finalizo o errores de conexion.
 */
export const registrarError = async (idPartida) => {
  try {
    const response = await api.post(`/juego/partidas/${idPartida}/error`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: salirPartida
 *
 * Descripcion:
 * Consume POST /salir para marcar una partida como abandonada.
 *
 * Es llamada desde:
 * confirmarSalida() en JuegoPage.jsx.
 *
 * Llama a:
 * POST /juego/partidas/{idPartida}/salir.
 *
 * Parametros:
 * idPartida identificador de la partida.
 *
 * Resultado:
 * Devuelve la partida con estado abandonada.
 *
 * Manejo de errores:
 * Propaga errores de estado incompatible o conexion.
 */
export const salirPartida = async (idPartida) => {
  try {
    const response = await api.post(`/juego/partidas/${idPartida}/salir`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
