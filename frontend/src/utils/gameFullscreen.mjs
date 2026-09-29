/** Obtiene las APIs estandar y WebKit sin asumir soporte por tipo de dispositivo. */
export const obtenerApiFullscreen = (documento = globalThis.document) => {
  const raiz = documento?.documentElement;
  const solicitar = raiz?.requestFullscreen || raiz?.webkitRequestFullscreen;
  const salir = documento?.exitFullscreen || documento?.webkitExitFullscreen;

  return {
    soportado: typeof solicitar === "function",
    solicitar,
    salir,
    elementoActual: () => documento?.fullscreenElement || documento?.webkitFullscreenElement || null,
  };
};

/** Determina landscape por la consulta del navegador y, como respaldo, por el viewport real. */
export const esViewportLandscape = ({ coincideMedia = false, ancho = 0, alto = 0 } = {}) => (
  Boolean(coincideMedia) || (Number(ancho) > Number(alto))
);

/** Evita mostrar alertas cuando fullscreen nunca se obtuvo o la salida fue intencional. */
export const debeMostrarAvisoSalidaFullscreen = ({
  juegoActivo,
  fullscreenNativoIngresado,
  fullscreenNativoAnterior,
  fullscreenNativoActivo,
  salidaIntencional,
}) => (
  Boolean(
    juegoActivo
    && fullscreenNativoIngresado
    && fullscreenNativoAnterior
    && !fullscreenNativoActivo
    && !salidaIntencional,
  )
);

/** Selecciona el modo visual seguro cuando la API no existe o no logra activarse. */
export const resolverModoFullscreen = ({ soportado, fullscreenNativoActivo }) => (
  soportado && fullscreenNativoActivo ? "native" : "pseudo"
);
