import api from "./apiClient";

const extraerDatos = (response) => response.data;

const manejarError = (error) => {
  const mensaje =
    error.response?.data?.message ||
    "No fue posible comunicarse con el servidor. Verifique que el backend este en ejecucion.";
  throw new Error(mensaje);
};

const manejarErrorDescarga = async (error) => {
  if (error.response?.data instanceof Blob) {
    try {
      const datos = JSON.parse(await error.response.data.text());
      throw new Error(datos.message || "No fue posible generar el reporte solicitado.");
    } catch (errorBlob) {
      if (errorBlob.message !== "Unexpected token o in JSON at position 1") {
        throw errorBlob;
      }
    }
  }
  manejarError(error);
};

const descargarArchivo = async (ruta, filtros) => {
  try {
    const response = await api.get(ruta, { params: filtros, responseType: "blob" });
    const disposition = response.headers["content-disposition"] || "";
    const coincidencia = disposition.match(/filename="?([^";]+)"?/i);
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(response.data);
    enlace.download = coincidencia?.[1] || "reporte";
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    URL.revokeObjectURL(enlace.href);
  } catch (error) {
    await manejarErrorDescarga(error);
  }
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

/** Descarga el reporte del docente conservando filtros y autorización del backend. */
export const exportarReporteAgente = (formato, filtros = {}) => descargarArchivo(`/docente/reportes/agente/exportar/${formato}`, filtros);
