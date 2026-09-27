import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje =
    error.response?.data?.message ||
    "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  throw new Error(mensaje);
};

export const obtenerPanelDocente = async () => {
  try {
    const response = await api.get("/docente/panel");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerEstudiantesDocente = async () => {
  try {
    const response = await api.get("/docente/estudiantes");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerReporteAgente = async (filtros = {}) => {
  try {
    const response = await api.get("/docente/reportes/agente", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerDecisionesAgente = async (filtros = {}) => {
  try {
    const response = await api.get("/docente/reportes/agente/decisiones", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
