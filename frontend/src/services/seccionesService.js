import api from "./apiClient";
import { obtenerOpcionesGrados } from "./gradosService";

/**
 * Funcion: extraerDatos
 *
 * Descripcion:
 * Normaliza la respuesta recibida desde Flask para entregar al componente solo el cuerpo JSON.
 *
 * Es llamada desde:
 * Todas las funciones de este servicio despues de ejecutar axios.
 *
 * Llama a:
 * No llama endpoints; solamente lee response.data.
 *
 * Resultado:
 * Devuelve el objeto JSON uniforme enviado por el backend.
 *
 * Manejo de errores:
 * No maneja errores directamente porque axios los propaga al bloque catch de cada funcion.
 */
const extraerDatos = (response) => response.data;

/**
 * Funcion: manejarError
 *
 * Descripcion:
 * Convierte errores de axios en errores legibles para SeccionesPage.
 *
 * Es llamada desde:
 * obtenerSecciones(), obtenerSeccionPorId(), crearSeccion(), actualizarSeccion(),
 * cambiarEstadoSeccion() y obtenerGrados().
 *
 * Llama a:
 * No llama servicios externos; utiliza la respuesta de axios si existe.
 *
 * Resultado:
 * Lanza un Error con el mensaje del backend o con un mensaje de conexion.
 *
 * Manejo de errores:
 * Siempre propaga el error para que SeccionesPage muestre el mensaje visible.
 */
const manejarError = (error) => {
  const mensaje = error.response?.data?.message || "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  throw new Error(mensaje);
};

/**
 * Funcion: obtenerSecciones
 *
 * Descripcion:
 * Consume el endpoint GET /api/secciones para consultar las secciones registradas.
 *
 * Es llamada desde:
 * cargarSecciones() en src/pages/SeccionesPage.jsx.
 *
 * Llama a:
 * GET /secciones mediante axios.
 *
 * Resultado:
 * Devuelve success, message y data con la lista de secciones.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const obtenerSecciones = async (estado = "") => {
  try {
    const response = await api.get("/secciones", {
      params: estado ? { estado } : {},
    });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: obtenerSeccionPorId
 *
 * Descripcion:
 * Consume el endpoint GET /api/secciones/<id> para consultar una seccion especifica.
 *
 * Es llamada desde:
 * SeccionesPage.jsx cuando se necesita refrescar o revisar un registro puntual.
 *
 * Llama a:
 * GET /secciones/{idSeccion} mediante axios.
 *
 * Resultado:
 * Devuelve success, message y data con una seccion.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const obtenerSeccionPorId = async (idSeccion) => {
  try {
    const response = await api.get(`/secciones/${idSeccion}`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: crearSeccion
 *
 * Descripcion:
 * Consume el endpoint POST /api/secciones para crear una seccion.
 *
 * Es llamada desde:
 * guardarSeccion() en src/pages/SeccionesPage.jsx.
 *
 * Llama a:
 * POST /secciones mediante axios y envia id_grado, nombre_seccion, descripcion y estado.
 *
 * Resultado:
 * Devuelve success, message y data con la seccion creada.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const crearSeccion = async (datos) => {
  try {
    const response = await api.post("/secciones", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: actualizarSeccion
 *
 * Descripcion:
 * Consume el endpoint PUT /api/secciones/<id> para actualizar una seccion existente.
 *
 * Es llamada desde:
 * guardarSeccion() en src/pages/SeccionesPage.jsx cuando hay una seccion seleccionada.
 *
 * Llama a:
 * PUT /secciones/{idSeccion} mediante axios y envia los datos editados.
 *
 * Resultado:
 * Devuelve success, message y data con la seccion actualizada.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const actualizarSeccion = async (idSeccion, datos) => {
  try {
    const response = await api.put(`/secciones/${idSeccion}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: cambiarEstadoSeccion
 *
 * Descripcion:
 * Consume el endpoint PATCH /api/secciones/<id>/estado para activar o desactivar una seccion.
 *
 * Es llamada desde:
 * cambiarEstado() en src/pages/SeccionesPage.jsx.
 *
 * Llama a:
 * PATCH /secciones/{idSeccion}/estado mediante axios y envia el nuevo estado.
 *
 * Resultado:
 * Devuelve success, message y data con la seccion actualizada.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const cambiarEstadoSeccion = async (idSeccion, estado) => {
  try {
    const response = await api.patch(`/secciones/${idSeccion}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

/**
 * Funcion: obtenerGrados
 *
 * Descripcion:
 * Delega en obtenerOpcionesGrados() para cargar el selector obligatorio de grados activos.
 *
 * Es llamada desde:
 * cargarGrados() en src/pages/SeccionesPage.jsx.
 *
 * Llama a:
 * GET /grados/opciones mediante src/services/gradosService.js.
 *
 * Resultado:
 * Devuelve success, message y data con la lista de grados activos.
 *
 * Manejo de errores:
 * Propaga un Error con el mensaje del backend para que la pagina lo muestre.
 */
export const obtenerGrados = async () => {
  return obtenerOpcionesGrados();
};

