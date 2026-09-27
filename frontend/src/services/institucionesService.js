import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje = error.response?.data?.message || "No fue posible comunicarse con el servidor.";
  const errorControlado = new Error(mensaje);
  errorControlado.errors = error.response?.data?.errors || {};
  throw errorControlado;
};

export const buscarInstituciones = async (texto = "") => {
  try {
    const response = await api.get("/instituciones", { params: { q: texto } });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const crearOReutilizarInstitucion = async (nombre) => {
  try {
    const response = await api.post("/instituciones", { nombre });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerSeccionesDisponiblesInstitucion = async (idInstitucion) => {
  try {
    const response = await api.get(`/instituciones/${idInstitucion}/secciones-disponibles`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
