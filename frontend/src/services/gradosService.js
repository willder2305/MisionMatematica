import api from "./apiClient";

/**
 * Funcion: extraerDatos
 *
 * Descripcion:
 * Normaliza la respuesta recibida desde Flask para entregar al componente el cuerpo JSON uniforme.
 *
 * Es llamada desde:
 * Todas las funciones de gradosService.js despues de ejecutar axios.
 *
 * Llama a:
 * No llama endpoints; lee response.data.
 *
 * Parametros:
 * response recibido desde axios.
 *
 * Resultado:
 * Devuelve success, message, data y errors enviados por el backend.
 *
 * Manejo de errores:
 * No maneja errores porque axios los propaga al catch de cada funcion.
 */
const extraerDatos = (response) => response.data;

/**
 * Funcion: manejarError
 *
 * Descripcion:
 * Convierte errores de axios en errores legibles para GradosPage o SeccionesPage.
 *
 * Es llamada desde:
 * obtenerGrados(), obtenerOpcionesGrados(), obtenerGradoPorId(), crearGrado(), actualizarGrado(),
 * cambiarEstadoGrado().
 *
 * Llama a:
 * No llama servicios externos; usa error.response si el backend respondio.
 *
 * Parametros:
 * error generado por axios.
 *
 * Resultado:
 * Lanza un Error con message y errors para que la interfaz los muestre.
 *
 * Manejo de errores:
 * Si no hay respuesta del backend, usa un mensaje claro de conexion.
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
 * Funcion: obtenerGrados
 *
 * Descripcion:
 * Consume GET /api/grados para consultar grados con total de secciones.
 *
 * Es llamada desde:
 * cargarGrados() en src/pages/GradosPage.jsx.
 *
 * Llama a:
 * GET /grados mediante el cliente Axios compartido.
 *
 * Parametros:
 * filtros opcional con estado activo o inactivo.
 *
 * Resultado:
 * Devuelve success, message y data con la lista de grados.
 *
 * Manejo de errores:
 * Propaga un Error con mensaje y errores del backend.
 */
export const obtenerGrados = async (filtros = {}) => {
  try {
    const response = await api.get("/grados", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: obtenerOpcionesGrados
 *
 * Descripcion:
 * Consume GET /api/grados/opciones para cargar solo grados activos en el selector de secciones.
 *
 * Es llamada desde:
 * cargarGrados() en src/pages/SeccionesPage.jsx mediante seccionesService.js.
 *
 * Llama a:
 * GET /grados/opciones mediante el cliente Axios compartido.
 *
 * Parametros:
 * No recibe parametros.
 *
 * Resultado:
 * Devuelve success, message y data con id, codigo y nombre de grados activos.
 *
 * Manejo de errores:
 * Propaga un Error con mensaje y errores del backend.
 */
export const obtenerOpcionesGrados = async () => {
  try {
    const response = await api.get("/grados/opciones");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: obtenerGradoPorId
 *
 * Descripcion:
 * Consume GET /api/grados/<id> para consultar un grado especifico.
 *
 * Es llamada desde:
 * GradosPage.jsx cuando se necesita revisar un registro puntual o desde pruebas manuales.
 *
 * Llama a:
 * GET /grados/{idGrado} mediante el cliente Axios compartido.
 *
 * Parametros:
 * idGrado identificador del grado.
 *
 * Resultado:
 * Devuelve success, message y data con el grado solicitado.
 *
 * Manejo de errores:
 * Propaga un Error si el grado no existe o falla la conexion.
 */
export const obtenerGradoPorId = async (idGrado) => {
  try {
    const response = await api.get(`/grados/${idGrado}`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: crearGrado
 *
 * Descripcion:
 * Consume POST /api/grados para crear un grado.
 *
 * Es llamada desde:
 * guardarGrado() en src/pages/GradosPage.jsx cuando no hay grado seleccionado.
 *
 * Llama a:
 * POST /grados mediante el cliente Axios compartido.
 *
 * Parametros:
 * datos con codigo_grado, nombre_grado, descripcion, orden_visualizacion y estado.
 *
 * Resultado:
 * Devuelve success, message y data con el grado creado.
 *
 * Manejo de errores:
 * Propaga errores de validacion o duplicado para mostrarlos en la pagina.
 */
export const crearGrado = async (datos) => {
  try {
    const response = await api.post("/grados", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: actualizarGrado
 *
 * Descripcion:
 * Consume PUT /api/grados/<id> para actualizar un grado existente.
 *
 * Es llamada desde:
 * guardarGrado() en src/pages/GradosPage.jsx cuando hay grado seleccionado.
 *
 * Llama a:
 * PUT /grados/{idGrado} mediante el cliente Axios compartido.
 *
 * Parametros:
 * idGrado y datos editados del formulario.
 *
 * Resultado:
 * Devuelve success, message y data con el grado actualizado.
 *
 * Manejo de errores:
 * Propaga errores de validacion, duplicado o inexistencia.
 */
export const actualizarGrado = async (idGrado, datos) => {
  try {
    const response = await api.put(`/grados/${idGrado}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: cambiarEstadoGrado
 *
 * Descripcion:
 * Consume PATCH /api/grados/<id>/estado para activar o desactivar un grado.
 *
 * Es llamada desde:
 * cambiarEstado() en src/pages/GradosPage.jsx.
 *
 * Llama a:
 * PATCH /grados/{idGrado}/estado mediante el cliente Axios compartido.
 *
 * Parametros:
 * idGrado y estado nuevo.
 *
 * Resultado:
 * Devuelve success, message y data con el grado actualizado.
 *
 * Manejo de errores:
 * Propaga errores de estado invalido, inexistencia o conexion.
 */
export const cambiarEstadoGrado = async (idGrado, estado) => {
  try {
    const response = await api.patch(`/grados/${idGrado}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
