import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje =
    error.response?.data?.message ||
    "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  throw new Error(mensaje);
};

export const obtenerPanelEstudiante = async () => {
  try {
    const response = await api.get("/estudiante/panel");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerProgresoEstudiante = async () => {
  try {
    const response = await api.get("/estudiante/progreso");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerHistorialEstudiante = async ({ limite = 20, offset = 0 } = {}) => {
  try {
    const response = await api.get("/estudiante/historial", { params: { limite, offset } });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
