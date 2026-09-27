import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje = error.response?.data?.message || "No fue posible comunicarse con el servidor.";
  throw new Error(mensaje);
};

export const obtenerGrupos = async () => {
  try {
    const response = await api.get("/grupos");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerSeccionesGrupo = async (idGrupo) => {
  try {
    const response = await api.get(`/grupos/${idGrupo}/secciones`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerPinesGrupo = async (idGrupo) => {
  try {
    const response = await api.get(`/grupos/${idGrupo}/pines`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerCodigosSecciones = async () => {
  try {
    const response = await api.get("/codigos/secciones");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerCodigosGradosUnicos = async () => {
  try {
    const response = await api.get("/codigos/grados-unicos");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const generarPinGrupo = async (idGrupo, datos = {}) => {
  try {
    const response = await api.post(`/grupos/${idGrupo}/pines`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoPin = async (idPin, estado) => {
  try {
    const response = await api.patch(`/pines/${idPin}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const regenerarPin = async (idPin) => {
  try {
    const response = await api.post(`/pines/${idPin}/regenerar`);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const validarPin = async (pin) => {
  try {
    const response = await api.post("/pines/validar", { pin });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const ingresarConPin = async (pin) => {
  try {
    const response = await api.post("/pines/ingresar", { pin });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const validarActualizacionGrado = async (pin) => {
  try {
    const response = await api.post("/pines/actualizar-grado/validar", { pin });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const confirmarActualizacionGrado = async (pin) => {
  try {
    const response = await api.post("/pines/actualizar-grado/confirmar", { pin });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
