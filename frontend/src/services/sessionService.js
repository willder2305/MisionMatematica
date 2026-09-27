const ACCESS_TOKEN_KEY = "mm_access_token";
const REFRESH_TOKEN_KEY = "mm_refresh_token";
const USUARIO_KEY = "mm_usuario";

export const obtenerAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);

export const obtenerRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const emitirSesionActualizada = () => {
  window.dispatchEvent(new CustomEvent("mm:auth-updated", { detail: { usuario: obtenerUsuarioLocal() } }));
};

export const emitirSesionInvalida = () => {
  window.dispatchEvent(new CustomEvent("mm:auth-invalid"));
};

export const guardarSesion = (data) => {
  // Persiste solo los datos recibidos para conservar tokens vigentes entre recargas.
  if (!data) return;
  if (data.access_token) localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  if (data.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  if (data.usuario) {
    localStorage.setItem(USUARIO_KEY, JSON.stringify(data.usuario));
    emitirSesionActualizada();
  }
};

export const obtenerUsuarioLocal = () => {
  // Recupera el usuario cacheado; si el JSON esta corrupto, fuerza una sesion limpia.
  const valor = localStorage.getItem(USUARIO_KEY);
  if (!valor) return null;
  try {
    return JSON.parse(valor);
  } catch {
    limpiarSesion();
    return null;
  }
};

export const limpiarSesion = () => {
  // Elimina credenciales locales unicamente cuando el refresh token ya no es recuperable.
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USUARIO_KEY);
  emitirSesionInvalida();
};

export const esRutaPublica = (ruta = window.location.pathname) => (
  ["/", "/login", "/registro", "/recuperar-password"].includes(ruta)
);

export const redirigirALoginSiCorresponde = () => {
  // Evita enviar al login desde pantallas publicas para no crear ciclos de navegacion.
  if (!esRutaPublica()) {
    window.history.replaceState({}, "", "/login");
    window.dispatchEvent(new CustomEvent("mm:navigation", { detail: { path: "/login" } }));
  }
};
