import { useCallback, useEffect, useRef, useState } from "react";
import {
  debeMostrarAvisoSalidaFullscreen,
  esViewportLandscape,
  obtenerApiFullscreen,
  resolverModoFullscreen,
} from "../utils/gameFullscreen.mjs";

const detectarMovil = () => (
  window.matchMedia?.("(pointer: coarse)")?.matches || window.innerWidth <= 1024
);

const leerLandscape = () => esViewportLandscape({
  coincideMedia: window.matchMedia?.("(orientation: landscape)")?.matches,
  ancho: window.visualViewport?.width || window.innerWidth,
  alto: window.visualViewport?.height || window.innerHeight,
});

/**
 * Coordina fullscreen nativo, su alternativa visual y orientación sin bloquear el juego.
 * El aviso de salida solo aparece tras una salida real de un fullscreen nativo ya confirmado.
 */
const useGameFullscreen = ({ activo, contenedorRef }) => {
  const [soportaFullscreenNativo, setSoportaFullscreenNativo] = useState(false);
  const [fullscreenNativoActivo, setFullscreenNativoActivo] = useState(false);
  const [fullscreenNativoIngresado, setFullscreenNativoIngresado] = useState(false);
  const [solicitudPendiente, setSolicitudPendiente] = useState(false);
  const [esMovil, setEsMovil] = useState(() => detectarMovil());
  const [esLandscape, setEsLandscape] = useState(() => leerLandscape());
  const [usarPseudoFullscreen, setUsarPseudoFullscreen] = useState(false);
  const [mostrarAvisoSalida, setMostrarAvisoSalida] = useState(false);
  const activoRef = useRef(activo);
  const fullscreenAnteriorRef = useRef(false);
  const fullscreenIngresadoRef = useRef(false);
  const salidaIntencionalRef = useRef(false);

  useEffect(() => {
    activoRef.current = activo;
    if (!activo) {
      fullscreenAnteriorRef.current = false;
      fullscreenIngresadoRef.current = false;
      setFullscreenNativoActivo(false);
      setFullscreenNativoIngresado(false);
      setUsarPseudoFullscreen(false);
      setMostrarAvisoSalida(false);
      return;
    }

    // El fallback visual comienza desde el inicio para que iOS y navegadores restrictivos sigan jugables.
    setUsarPseudoFullscreen(true);
  }, [activo]);

  useEffect(() => {
    const actualizarViewport = () => {
      setEsMovil(detectarMovil());
      setEsLandscape(leerLandscape());
    };
    const sincronizarFullscreen = () => {
      const api = obtenerApiFullscreen(document);
      const estaActivo = api.elementoActual() === contenedorRef.current;
      const debeAvisar = debeMostrarAvisoSalidaFullscreen({
        juegoActivo: activoRef.current,
        fullscreenNativoIngresado: fullscreenIngresadoRef.current,
        fullscreenNativoAnterior: fullscreenAnteriorRef.current,
        fullscreenNativoActivo: estaActivo,
        salidaIntencional: salidaIntencionalRef.current,
      });

      if (estaActivo) {
        fullscreenIngresadoRef.current = true;
        setFullscreenNativoIngresado(true);
        setUsarPseudoFullscreen(false);
        setMostrarAvisoSalida(false);
      } else if (activoRef.current) {
        setUsarPseudoFullscreen(true);
        if (debeAvisar) setMostrarAvisoSalida(true);
      }

      fullscreenAnteriorRef.current = estaActivo;
      setFullscreenNativoActivo(estaActivo);
    };

    const api = obtenerApiFullscreen(document);
    setSoportaFullscreenNativo(api.soportado);
    actualizarViewport();
    sincronizarFullscreen();
    window.addEventListener("resize", actualizarViewport);
    window.addEventListener("orientationchange", actualizarViewport);
    window.visualViewport?.addEventListener("resize", actualizarViewport);
    document.addEventListener("fullscreenchange", sincronizarFullscreen);
    document.addEventListener("webkitfullscreenchange", sincronizarFullscreen);

    return () => {
      window.removeEventListener("resize", actualizarViewport);
      window.removeEventListener("orientationchange", actualizarViewport);
      window.visualViewport?.removeEventListener("resize", actualizarViewport);
      document.removeEventListener("fullscreenchange", sincronizarFullscreen);
      document.removeEventListener("webkitfullscreenchange", sincronizarFullscreen);
    };
  }, [contenedorRef]);

  useEffect(() => {
    if (!activo) return undefined;

    const html = document.documentElement;
    const body = document.body;
    const root = document.getElementById("root");
    const estilosPrevios = {
      htmlOverflow: html.style.overflow,
      bodyOverflow: body.style.overflow,
      bodyOverscroll: body.style.overscrollBehavior,
      rootOverflow: root?.style.overflow || "",
    };
    html.classList.add("game-session-active");
    body.classList.add("game-session-active");
    root?.classList.add("game-session-active");
    html.style.overflow = "hidden";
    body.style.overflow = "hidden";
    body.style.overscrollBehavior = "none";
    if (root) root.style.overflow = "hidden";

    return () => {
      html.classList.remove("game-session-active");
      body.classList.remove("game-session-active");
      root?.classList.remove("game-session-active");
      html.style.overflow = estilosPrevios.htmlOverflow;
      body.style.overflow = estilosPrevios.bodyOverflow;
      body.style.overscrollBehavior = estilosPrevios.bodyOverscroll;
      if (root) root.style.overflow = estilosPrevios.rootOverflow;
    };
  }, [activo]);

  const bloquearOrientacionLandscape = useCallback(async () => {
    const orientacion = window.screen?.orientation;
    if (!detectarMovil() || typeof orientacion?.lock !== "function") return;
    try {
      await orientacion.lock("landscape");
    } catch {
      // La orientación se controla visualmente con el overlay cuando el navegador no permite bloquearla.
    }
  }, []);

  const solicitarFullscreen = useCallback(async () => {
    const elemento = contenedorRef.current;
    const api = obtenerApiFullscreen(document);
    setMostrarAvisoSalida(false);
    setSolicitudPendiente(true);

    try {
      if (!elemento || !api.soportado) {
        setUsarPseudoFullscreen(true);
        return false;
      }

      salidaIntencionalRef.current = false;
      if (api.elementoActual() !== elemento) {
        await Promise.resolve(api.solicitar.call(elemento));
      }

      const nativoActivo = api.elementoActual() === elemento;
      if (nativoActivo) {
        fullscreenIngresadoRef.current = true;
        fullscreenAnteriorRef.current = true;
        setFullscreenNativoIngresado(true);
        setFullscreenNativoActivo(true);
      }
      setUsarPseudoFullscreen(resolverModoFullscreen({
        soportado: api.soportado,
        fullscreenNativoActivo: nativoActivo,
      }) === "pseudo");
      await bloquearOrientacionLandscape();
      return nativoActivo;
    } catch {
      // Rechazos por política del navegador son normales en móviles; el fallback no bloquea la partida.
      setUsarPseudoFullscreen(true);
      return false;
    } finally {
      setSolicitudPendiente(false);
    }
  }, [bloquearOrientacionLandscape, contenedorRef]);

  const salirFullscreen = useCallback(async () => {
    const api = obtenerApiFullscreen(document);
    salidaIntencionalRef.current = true;
    setMostrarAvisoSalida(false);

    try {
      if (api.elementoActual() && typeof api.salir === "function") {
        await Promise.resolve(api.salir.call(document));
      }
    } catch {
      // El usuario puede haber salido desde el navegador antes de pulsar Salir.
    } finally {
      try {
        window.screen?.orientation?.unlock?.();
      } catch {
        // El desbloqueo no está disponible en todos los navegadores.
      }
      fullscreenAnteriorRef.current = false;
      fullscreenIngresadoRef.current = false;
      setFullscreenNativoActivo(false);
      setFullscreenNativoIngresado(false);
      setUsarPseudoFullscreen(false);
      salidaIntencionalRef.current = false;
    }
  }, []);

  return {
    esLandscape,
    esMovil,
    fullscreenNativoActivo,
    fullscreenNativoIngresado,
    mostrarAvisoSalida,
    solicitudPendiente,
    solicitarFullscreen,
    salirFullscreen,
    soportaFullscreenNativo,
    usarPseudoFullscreen,
  };
};

export default useGameFullscreen;
