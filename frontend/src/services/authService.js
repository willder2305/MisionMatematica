import api from "./apiClient";
import { guardarSesion, limpiarSesion, obtenerRefreshToken } from "./sessionService";

export { guardarSesion, limpiarSesion, obtenerAccessToken, obtenerRefreshToken, obtenerUsuarioLocal } from "./sessionService";

export const registrar = async (datos) => {
  const response = await api.post("/auth/register", datos);
  if (response.data?.success) guardarSesion(response.data.data);
  return response.data;
};

export const login = async (datos) => {
  const response = await api.post("/auth/login", datos);
  if (response.data?.success) guardarSesion(response.data.data);
  return response.data;
};

export const solicitarRecuperacionPassword = async (correo) => {
  const response = await api.post("/auth/forgot-password", { correo });
  return response.data;
};

export const logout = async () => {
  const refreshToken = obtenerRefreshToken();
  try {
    await api.post("/auth/logout", { refresh_token: refreshToken });
  } finally {
    limpiarSesion();
  }
};

export const obtenerMe = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};
