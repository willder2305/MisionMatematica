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

export const obtenerTemasPorGrado = async (idGrado) => {
  try {
    const response = await api.get("/temas", { params: { grado: idGrado } });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
