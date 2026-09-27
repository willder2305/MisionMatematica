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

export const obtenerPlantillas = async (filtros = {}) => {
  try {
    const response = await api.get("/plantillas", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerNivelesPlantillas = async () => {
  try {
    const response = await api.get("/plantillas/niveles");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const crearPlantilla = async (datos) => {
  try {
    const response = await api.post("/plantillas", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarPlantilla = async (idPlantilla, datos) => {
  try {
    const response = await api.put(`/plantillas/${idPlantilla}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoPlantilla = async (idPlantilla, estado) => {
  try {
    const response = await api.patch(`/plantillas/${idPlantilla}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const probarPlantilla = async (idPlantilla, cantidad = 3) => {
  try {
    const response = await api.post(`/plantillas/${idPlantilla}/probar`, { cantidad });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
