import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje =
    error.response?.data?.message ||
    "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  const errorControlado = new Error(mensaje);
  errorControlado.errors = error.response?.data?.errors || {};
  throw errorControlado;
};

export const obtenerAsignaciones = async () => {
  try {
    const response = await api.get("/asignaciones");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerContextoAsignaciones = async () => {
  try {
    const response = await api.get("/asignaciones/contexto");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const crearAsignacion = async (datos) => {
  try {
    const response = await api.post("/asignaciones", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarAsignacion = async (idAsignacion, datos) => {
  try {
    const response = await api.put(`/asignaciones/${idAsignacion}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoAsignacion = async (idAsignacion, estado) => {
  try {
    const response = await api.patch(`/asignaciones/${idAsignacion}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerAsignacionesEstudiante = async () => {
  try {
    const response = await api.get("/estudiante/asignaciones");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
