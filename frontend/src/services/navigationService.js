export const navegarInternamente = (ruta, opciones = {}) => {
  // Cambia rutas internas sin recargar React y avisa a App para renderizar la vista nueva.
  const { replace = false } = opciones;
  const rutaActual = `${window.location.pathname}${window.location.search}`;
  if (rutaActual === ruta) return;
  const metodo = replace ? "replaceState" : "pushState";
  window.history[metodo]({}, "", ruta);
  window.dispatchEvent(new CustomEvent("mm:navigation", { detail: { path: ruta } }));
};
