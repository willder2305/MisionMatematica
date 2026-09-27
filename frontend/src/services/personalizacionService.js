import api from "./apiClient";

const datos = (respuesta) => respuesta.data;

const manejarError = (error) => {
  const respuesta = error.response?.data || {};
  const errorControlado = new Error(respuesta.message || "No fue posible actualizar tu personalizacion.");
  errorControlado.code = respuesta.code;
  errorControlado.data = respuesta.data;
  throw errorControlado;
};

export const obtenerTienda = async () => {
  try {
    return datos(await api.get("/estudiante/tienda"));
  } catch (error) {
    manejarError(error);
  }
};

export const comprarItem = async (idItem) => {
  try {
    return datos(await api.post("/estudiante/tienda/comprar", { id_item: idItem }));
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarPersonaje = async (personaje) => {
  try {
    return datos(await api.put("/estudiante/personalizacion/personaje", { personaje }));
  } catch (error) {
    manejarError(error);
  }
};

export const actualizarMapa = async (modoMapa, mapa = null) => {
  try {
    return datos(await api.put("/estudiante/personalizacion/mapa", { modo_mapa: modoMapa, mapa }));
  } catch (error) {
    manejarError(error);
  }
};
