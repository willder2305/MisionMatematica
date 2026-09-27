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

export const obtenerPanelAdmin = async () => {
  try {
    const response = await api.get("/admin/panel");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerUsuariosAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/usuarios", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoUsuarioAdmin = async (idUsuario, estado) => {
  try {
    const response = await api.patch(`/admin/usuarios/${idUsuario}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarRolUsuarioAdmin = async (idUsuario, rol) => {
  try {
    const response = await api.patch(`/admin/usuarios/${idUsuario}/rol`, { rol });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerTemasAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/temas", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const crearTemaAdmin = async (datos) => {
  try {
    const response = await api.post("/admin/temas", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarTemaAdmin = async (idTema, datos) => {
  try {
    const response = await api.put(`/admin/temas/${idTema}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoTemaAdmin = async (idTema, estado) => {
  try {
    const response = await api.patch(`/admin/temas/${idTema}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerEjerciciosAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/ejercicios", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const crearEjercicioAdmin = async (datos) => {
  try {
    const response = await api.post("/admin/ejercicios", datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarEjercicioAdmin = async (idEjercicio, datos) => {
  try {
    const response = await api.put(`/admin/ejercicios/${idEjercicio}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoEjercicioAdmin = async (idEjercicio, estado) => {
  try {
    const response = await api.patch(`/admin/ejercicios/${idEjercicio}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerReglasAdmin = async () => {
  try {
    const response = await api.get("/admin/reglas");
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerAuditoriaAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/auditoria", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerCatalogosReportesAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/reportes/filtros", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const obtenerReporteInstitucionalAdmin = async (filtros = {}) => {
  try {
    const response = await api.get("/admin/reportes/institucional", { params: filtros });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarReglaAdmin = async (idRegla, datos) => {
  try {
    const response = await api.put(`/admin/reglas/${idRegla}`, datos);
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};

export const cambiarEstadoReglaAdmin = async (idRegla, estado) => {
  try {
    const response = await api.patch(`/admin/reglas/${idRegla}/estado`, { estado });
    return extraerDatos(response);
  } catch (error) {
    manejarError(error);
  }
};
