import axios from "axios";
import {
  guardarSesion,
  limpiarSesion,
  obtenerAccessToken,
  obtenerRefreshToken,
  redirigirALoginSiCorresponde,
} from "./sessionService";

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";
export const API_TIMEOUT_MS = 15000;

let refreshPromise = null;

const endpointsAuthSinRefresh = [
  "/auth/login",
  "/auth/register",
  "/auth/logout",
  "/auth/refresh",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
];

/**
 * Configuracion: apiClient
 *
 * Descripcion:
 * Centraliza las solicitudes HTTP realizadas desde React hacia Flask.
 *
 * Es utilizado desde:
 * gradosService.js, seccionesService.js y demas servicios de frontend.
 *
 * Backend:
 * Usa VITE_API_URL cuando existe; si no, apunta a http://127.0.0.1:5000/api.
 *
 * Manejo de credenciales:
 * No activa withCredentials porque el proyecto no usa cookies o sesiones en esta fase.
 *
 * Renovacion:
 * Si un access token vence, intenta /auth/refresh una vez y reintenta la peticion original.
 */
const api = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT_MS,
  headers: {
    "Content-Type": "application/json",
  },
});

const esEndpointAuthSinReintento = (url = "") => endpointsAuthSinRefresh.some((endpoint) => url.includes(endpoint));

const refrescarSesion = async () => {
  // Rota el refresh token activo y actualiza localStorage antes de reintentar la peticion fallida.
  const refreshToken = obtenerRefreshToken();
  if (!refreshToken) {
    throw new Error("No existe refresh token para recuperar la sesion.");
  }

  const response = await axios.post(
    `${API_URL}/auth/refresh`,
    { refresh_token: refreshToken },
    { timeout: API_TIMEOUT_MS, headers: { "Content-Type": "application/json" } },
  );

  if (!response.data?.success || !response.data?.data?.access_token) {
    throw new Error(response.data?.message || "No fue posible renovar la sesion.");
  }

  guardarSesion(response.data.data);
  return response.data.data.access_token;
};

api.interceptors.request.use((config) => {
  const token = obtenerAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    if (
      status !== 401
      || !originalRequest
      || originalRequest._retry
      || esEndpointAuthSinReintento(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      refreshPromise = refreshPromise || refrescarSesion().finally(() => {
        refreshPromise = null;
      });
      const nuevoAccessToken = await refreshPromise;
      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${nuevoAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      limpiarSesion();
      redirigirALoginSiCorresponde();
      return Promise.reject(refreshError);
    }
  },
);

export default api;
