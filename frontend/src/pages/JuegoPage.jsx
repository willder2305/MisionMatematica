import React, { useEffect, useMemo, useRef, useState } from "react";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import ExitGameModal from "../components/juego/ExitGameModal";
import GameBoard from "../components/juego/GameBoard";
import GameFinishedModal from "../components/juego/GameFinishedModal";
import QuestionPanel from "../components/juego/QuestionPanel";
import PixelAlert from "../components/ui/PixelAlert";
import { MAPA_PREDETERMINADO, obtenerPosicionCasilla } from "../config/mapasConfig";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { obtenerUsuarioLocal } from "../services/authService";
import { formatLabel } from "../constants/uiLabels";
import { continuarPartida, iniciarPartida, obtenerContextoJuego, responderPregunta, salirPartida } from "../services/juegoService";
import { navegarInternamente } from "../services/navigationService";

const DURACION_AVANCE_MS = 900;
const DURACION_ERROR_MS = 1050;
const ALTURA_SALTO_LOGICA = 96;
const SACUDIDA_ERROR_X_LOGICA = 14;
const SACUDIDA_ERROR_Y_LOGICA = 28;

// Calcula una posicion intermedia entre dos casillas durante el salto.
const interpolarEntreCasillas = (origen, destino, progreso) => ({
  x: origen.x + (destino.x - origen.x) * progreso,
  y: origen.y + (destino.y - origen.y) * progreso,
});

// Agrega un desplazamiento vertical temporal para la animacion de acierto.
const calcularOffsetSalto = (progreso) => ({
  x: 0,
  y: -Math.sin(progreso * Math.PI) * ALTURA_SALTO_LOGICA,
});

// Combina la posicion oficial con el offset temporal de animacion.
const aplicarPosicionVisual = (posicionBase, offsetAnimacion) => ({
  x: posicionBase.x + (offsetAnimacion?.x || 0),
  y: posicionBase.y + (offsetAnimacion?.y || 0),
});

// Elige el frame del sprite segun el tiempo transcurrido.
const calcularFrame = (tiempoTranscurrido, duracionTotal, totalFrames) => {
  if (!totalFrames) {
    return 0;
  }
  return Math.min(totalFrames - 1, Math.floor((tiempoTranscurrido / duracionTotal) * totalFrames));
};

// Genera un identificador unico para que el backend no registre dos veces la misma respuesta.
const generarRequestId = () => {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

// Detecta pantallas tactiles o compactas donde conviene usar landscape.
const requiereLandscape = () => (
  window.matchMedia?.("(pointer: coarse)")?.matches || window.innerWidth <= 1024
);

// Detecta modo vertical solo para telefono/tablet; desktop no se bloquea.
const estaEnVerticalMovil = () => (
  requiereLandscape() && window.matchMedia?.("(orientation: portrait)")?.matches
);

// Pantalla principal del juego: seleccion, partida, pregunta y animaciones.
const JuegoPage = () => {
  const [partida, setPartida] = useState(null);
  const [preguntaActual, setPreguntaActual] = useState(null);
  const [temas, setTemas] = useState([]);
  const [idTema, setIdTema] = useState("");
  const parametrosInicialesRef = useRef(new URLSearchParams(window.location.search));
  const idAsignacion = parametrosInicialesRef.current.get("asignacion") || "";
  const [temaInicial, setTemaInicial] = useState(parametrosInicialesRef.current.get("tema") || "");
  const [modalSalidaAbierto, setModalSalidaAbierto] = useState(false);
  const [modalFinalAbierto, setModalFinalAbierto] = useState(false);
  const [preparandoPartida, setPreparandoPartida] = useState(false);
  const [orientacionVertical, setOrientacionVertical] = useState(false);
  const [fullscreenPerdido, setFullscreenPerdido] = useState(false);
  const [posicionBase, setPosicionBase] = useState(() => obtenerPosicionCasilla(MAPA_PREDETERMINADO, 0));
  const [offsetAnimacion, setOffsetAnimacion] = useState({ x: 0, y: 0 });
  const [tipoAnimacion, setTipoAnimacion] = useState("idle");
  const [frameIndex, setFrameIndex] = useState(0);
  const [procesando, setProcesando] = useState(false);
  const [animando, setAnimando] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [feedback, setFeedback] = useState(null);
  const [explicacionAbierta, setExplicacionAbierta] = useState(false);
  const [recompensa, setRecompensa] = useState(null);
  const [saldoMonedas, setSaldoMonedas] = useState(0);
  const animacionRef = useRef(null);
  const bloqueoRef = useRef(false);
  const inicioPartidaRef = useRef(false);
  const gameFullscreenRef = useRef(null);
  const salidaIntencionalRef = useRef(false);
  const requestInicioRef = useRef("");
  const inicioPreguntaRef = useRef(Date.now());
  const posicionVisual = aplicarPosicionVisual(posicionBase, offsetAnimacion);
  const juegoActivo = Boolean(partida) || preparandoPartida;
  // El catálogo solo cambia al cargar contexto; no se reagrupa durante cada frame de animación.
  const temasPorCategoria = useMemo(() => temas.reduce((grupos, tema) => {
    const categoria = tema.categoria || "Temas";
    if (!grupos[categoria]) grupos[categoria] = [];
    grupos[categoria].push(tema);
    return grupos;
  }, {}), [temas]);

  useEffect(() => {
    const usuario = obtenerUsuarioLocal();
    if (!usuario) {
      navegarInternamente("/login", { replace: true });
      return undefined;
    }
    if (usuario.rol !== "estudiante") {
      navegarInternamente("/secciones", { replace: true });
      return undefined;
    }
    if (!usuario.onboarding_completado) {
      navegarInternamente("/onboarding", { replace: true });
      return undefined;
    }

    cargarContextoJuego();
    return () => {
      cancelarAnimacion();
      desbloquearOrientacion();
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    if (!juegoActivo) {
      return undefined;
    }

    const overflowAnterior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflowAnterior;
    };
  }, [juegoActivo]);

  useEffect(() => {
    const actualizarOrientacion = () => setOrientacionVertical(estaEnVerticalMovil());
    actualizarOrientacion();
    window.addEventListener("resize", actualizarOrientacion);
    window.addEventListener("orientationchange", actualizarOrientacion);
    return () => {
      window.removeEventListener("resize", actualizarOrientacion);
      window.removeEventListener("orientationchange", actualizarOrientacion);
    };
  }, []);

  useEffect(() => {
    const detectarSalidaFullscreen = () => {
      if (!partida || salidaIntencionalRef.current) {
        return;
      }

      const elementoJuego = gameFullscreenRef.current;
      if (elementoJuego && document.fullscreenElement !== elementoJuego) {
        setFullscreenPerdido(true);
      }
    };

    document.addEventListener("fullscreenchange", detectarSalidaFullscreen);
    return () => document.removeEventListener("fullscreenchange", detectarSalidaFullscreen);
  }, [partida]);

  // Carga el catálogo personal completo; el backend conserva grado y dificultad internos.
  const cargarContextoJuego = async () => {
    try {
      const respuesta = await obtenerContextoJuego();
      const contexto = respuesta.data || {};
      const temasDisponibles = contexto.temas || [];
      setTemas(temasDisponibles);
      if (temaInicial && temasDisponibles.some((tema) => String(tema.id_tema) === String(temaInicial))) {
        setIdTema(String(temaInicial));
        setTemaInicial("");
      }
    } catch (error) {
      if (error.response?.status === 401) {
        navegarInternamente("/login", { replace: true });
        return;
      }
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Cancela el requestAnimationFrame pendiente si la pantalla cambia o se reinicia.
  const cancelarAnimacion = () => {
    if (animacionRef.current) {
      cancelAnimationFrame(animacionRef.current);
      animacionRef.current = null;
    }
  };

  // Bloquea orientacion horizontal cuando el navegador y el dispositivo lo permiten.
  const bloquearOrientacionLandscape = async () => {
    if (!requiereLandscape() || !screen.orientation || typeof screen.orientation.lock !== "function") {
      return;
    }

    try {
      await screen.orientation.lock("landscape-primary");
    } catch (error) {
      try {
        await screen.orientation.lock("landscape");
      } catch (segundoError) {
        // Algunos navegadores no permiten bloquear orientacion; se usa overlay fallback.
      }
    }
  };

  // Libera el bloqueo de orientacion sin fallar en navegadores incompatibles.
  const desbloquearOrientacion = () => {
    if (!screen.orientation || typeof screen.orientation.unlock !== "function") {
      return;
    }

    try {
      screen.orientation.unlock();
    } catch (error) {
      // No todos los navegadores implementan unlock de forma consistente.
    }
  };

  // Solicita fullscreen desde una accion del usuario y prepara el fallback si falla.
  const solicitarPantallaCompleta = async () => {
    const elementoJuego = gameFullscreenRef.current;
    if (!elementoJuego || typeof elementoJuego.requestFullscreen !== "function") {
      setFullscreenPerdido(true);
      return;
    }

    try {
      salidaIntencionalRef.current = false;
      if (document.fullscreenElement !== elementoJuego) {
        await elementoJuego.requestFullscreen();
      }
      await bloquearOrientacionLandscape();
      setFullscreenPerdido(false);
    } catch (error) {
      setFullscreenPerdido(true);
    }
  };

  // Sale de fullscreen y restaura orientacion/layout normal al abandonar el juego.
  const salirPantallaCompleta = async () => {
    salidaIntencionalRef.current = true;
    desbloquearOrientacion();
    setFullscreenPerdido(false);
    if (document.fullscreenElement && typeof document.exitFullscreen === "function") {
      try {
        await document.exitFullscreen();
      } catch (error) {
        // Si el navegador ya salio de fullscreen, el flujo puede continuar.
      }
    }
    salidaIntencionalRef.current = false;
  };

  // Devuelve el personaje a idle y habilita controles.
  const liberarControles = () => {
    bloqueoRef.current = false;
    setAnimando(false);
    setProcesando(false);
    setTipoAnimacion("idle");
    setFrameIndex(0);
    setOffsetAnimacion({ x: 0, y: 0 });
  };

  // Ajusta el personaje a la coordenada oficial del mapa base confirmada por el backend.
  const snapACasilla = (mapaId, numeroCasilla) => {
    const posicionExacta = obtenerPosicionCasilla(mapaId, numeroCasilla);
    setPosicionBase(posicionExacta);
    setOffsetAnimacion({ x: 0, y: 0 });
    return posicionExacta;
  };

  // Guarda la pregunta visible y reinicia el contador de tiempo de respuesta.
  const aplicarPregunta = (pregunta) => {
    setPreguntaActual(pregunta || null);
    inicioPreguntaRef.current = Date.now();
  };

  // Sincroniza partida y muestra la explicacion solo despues de un intento incorrecto.
  const finalizarAnimacion = (partidaConfirmada, resultadoRespuesta = null) => {
    if (!partidaConfirmada) {
      liberarControles();
      return;
    }

    setPartida(partidaConfirmada);
    setRecompensa(resultadoRespuesta?.recompensa || null);
    setSaldoMonedas(resultadoRespuesta?.saldo_monedas ?? saldoMonedas);
    snapACasilla(partidaConfirmada.mapa, partidaConfirmada.casilla_actual);

    if (resultadoRespuesta) {
      const feedbackNuevo = {
        correcta: resultadoRespuesta.resultado.correcta,
        respuestaCorrecta: resultadoRespuesta.resultado.respuesta_correcta,
        explicacionPasos: resultadoRespuesta.resultado.explicacion_pasos || [],
        siguientePregunta: resultadoRespuesta.siguiente_pregunta,
      };
      setFeedback(feedbackNuevo);
      if (!feedbackNuevo.correcta && partidaConfirmada.estado === "en_curso") {
        setExplicacionAbierta(true);
      } else {
        aplicarPregunta(partidaConfirmada.estado === "en_curso" ? resultadoRespuesta.siguiente_pregunta : null);
      }
    }

    liberarControles();
    if (partidaConfirmada.estado === "completada" || partidaConfirmada.estado === "sin_vidas") {
      setModalFinalAbierto(true);
    }
  };

  // Reproduce salto interpolando entre dos coordenadas oficiales de casilla.
  const reproducirAnimacionAvance = (casillaOrigen, partidaConfirmada, resultadoRespuesta) => {
    const personajeConfig = obtenerPersonajeConfig(partidaConfirmada.personaje);
    const origen = obtenerPosicionCasilla(partidaConfirmada.mapa, casillaOrigen);
    const destino = obtenerPosicionCasilla(partidaConfirmada.mapa, partidaConfirmada.casilla_actual);
    let inicio = null;

    setAnimando(true);
    setTipoAnimacion("correcto");
    setPosicionBase(origen);
    setOffsetAnimacion({ x: 0, y: 0 });

    const animar = (timestamp) => {
      if (!inicio) {
        inicio = timestamp;
      }
      const tiempo = timestamp - inicio;
      const progreso = Math.min(tiempo / DURACION_AVANCE_MS, 1);
      setFrameIndex(calcularFrame(tiempo, DURACION_AVANCE_MS, personajeConfig.correcto.length));
      setPosicionBase(interpolarEntreCasillas(origen, destino, progreso));
      setOffsetAnimacion(calcularOffsetSalto(progreso));

      if (progreso < 1) {
        animacionRef.current = requestAnimationFrame(animar);
        return;
      }

      animacionRef.current = null;
      finalizarAnimacion(partidaConfirmada, resultadoRespuesta);
    };

    cancelarAnimacion();
    animacionRef.current = requestAnimationFrame(animar);
  };

  // Reproduce animacion de error y al final vuelve a la coordenada oficial actual.
  const reproducirAnimacionError = (partidaConfirmada, resultadoRespuesta) => {
    const personajeConfig = obtenerPersonajeConfig(partidaConfirmada.personaje);
    const posicionExacta = obtenerPosicionCasilla(partidaConfirmada.mapa, partidaConfirmada.casilla_actual);
    let inicio = null;

    setAnimando(true);
    setTipoAnimacion("error");
    setPosicionBase(posicionExacta);
    setOffsetAnimacion({ x: 0, y: 0 });

    const animar = (timestamp) => {
      if (!inicio) {
        inicio = timestamp;
      }
      const tiempo = timestamp - inicio;
      const progreso = Math.min(tiempo / DURACION_ERROR_MS, 1);
      setFrameIndex(calcularFrame(tiempo, DURACION_ERROR_MS, personajeConfig.error.length));
      setOffsetAnimacion({
        x: Math.sin(progreso * Math.PI * 4) * SACUDIDA_ERROR_X_LOGICA,
        y: -Math.sin(progreso * Math.PI) * SACUDIDA_ERROR_Y_LOGICA,
      });

      if (progreso < 1) {
        animacionRef.current = requestAnimationFrame(animar);
        return;
      }

      animacionRef.current = null;
      finalizarAnimacion(partidaConfirmada, resultadoRespuesta);
    };

    cancelarAnimacion();
    animacionRef.current = requestAnimationFrame(animar);
  };

  // Valida grado/tema e inicia con el personaje persistente del estudiante.
  const iniciarAventura = () => {
    if (!idAsignacion && !idTema) {
      setMensaje({ tipo: "error", texto: "Seleccione un tema antes de iniciar." });
      return;
    }
    setMensaje({ tipo: "", texto: "" });
    confirmarPartida();
  };

  // Crea la partida en backend; personaje y mapa se resuelven desde preferencias protegidas.
  const confirmarPartida = async () => {
    if (inicioPartidaRef.current) {
      return;
    }

    inicioPartidaRef.current = true;
    requestInicioRef.current = generarRequestId();
    try {
      setProcesando(true);
      setPreparandoPartida(true);
      setFeedback(null);
      setExplicacionAbierta(false);
      setMensaje({ tipo: "", texto: "" });
      await solicitarPantallaCompleta();
      const respuesta = await iniciarPartida({
        ...(idTema ? { id_tema: Number(idTema) } : {}),
        request_id: requestInicioRef.current,
        ...(idAsignacion ? { id_asignacion: Number(idAsignacion) } : {}),
      });
      const partidaCreada = respuesta.data.partida;
      setPartida(partidaCreada);
      aplicarPregunta(respuesta.data.pregunta_actual);
      snapACasilla(partidaCreada.mapa, partidaCreada.casilla_actual);
      setModalFinalAbierto(false);
      setMensaje({ tipo: "", texto: "" });
    } catch (error) {
      await salirPantallaCompleta();
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setPreparandoPartida(false);
      inicioPartidaRef.current = false;
      requestInicioRef.current = "";
      setProcesando(false);
    }
  };

  // Envia la respuesta al backend; el backend evalua y decide la siguiente pregunta.
  const manejarRespuesta = async (respuestaEstudiante) => {
    if (!partida || !preguntaActual || bloqueoRef.current || partida.estado !== "en_curso") {
      return;
    }

    bloqueoRef.current = true;
    setProcesando(true);
    setMensaje({ tipo: "", texto: "" });

    try {
      const casillaOrigen = partida.casilla_actual;
      const respuesta = await responderPregunta(partida.id_partida, {
        id_ejercicio: preguntaActual.id_ejercicio || null,
        id_ejercicio_generado: preguntaActual.id_ejercicio_generado || null,
        respuesta: respuestaEstudiante,
        request_id: generarRequestId(),
        tiempo_respuesta_ms: Date.now() - inicioPreguntaRef.current,
      });
      const resultado = respuesta.data;
      if (resultado.resultado.correcta) {
        reproducirAnimacionAvance(casillaOrigen, resultado.partida, resultado);
      } else {
        reproducirAnimacionError(resultado.partida, resultado);
      }
    } catch (error) {
      liberarControles();
      setMensaje({ tipo: "error", texto: "No se pudo procesar la respuesta. Intenta nuevamente." });
    }
  };

  // Marca la partida como abandonada cuando el usuario confirma salir.
  const confirmarSalida = async () => {
    if (!partida) {
      return;
    }

    try {
      setProcesando(true);
      await salirPartida(partida.id_partida);
      reiniciarEstadoLocal();
      await salirPantallaCompleta();
      navegarInternamente(idAsignacion ? "/actividades" : "/panel-estudiante");
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
      setProcesando(false);
    }
  };

  // Limpia estado local para volver a la pantalla inicial.
  const reiniciarEstadoLocal = (textoMensaje = "") => {
    cancelarAnimacion();
    setPartida(null);
    aplicarPregunta(null);
    setFeedback(null);
    setExplicacionAbierta(false);
    setRecompensa(null);
    setSaldoMonedas(0);
    setModalSalidaAbierto(false);
    setModalFinalAbierto(false);
    snapACasilla(MAPA_PREDETERMINADO, 0);
    liberarControles();
    setMensaje(textoMensaje ? { tipo: "success", texto: textoMensaje } : { tipo: "", texto: "" });
  };

  // Sale definitivamente del juego y restaura el menu de actividades.
  const volverAActividades = async () => {
    reiniciarEstadoLocal();
    await salirPantallaCompleta();
    navegarInternamente(idAsignacion ? "/actividades" : "/panel-estudiante");
  };

  // Resta una moneda en backend y conserva la misma partida, casilla y progreso.
  const continuarAventura = async () => {
    if (!partida || procesando) return;
    try {
      setProcesando(true);
      const respuesta = await continuarPartida(partida.id_partida, generarRequestId());
      setPartida(respuesta.data.partida);
      setSaldoMonedas(respuesta.data.saldo_monedas);
      setRecompensa(null);
      aplicarPregunta(respuesta.data.pregunta_actual);
      snapACasilla(respuesta.data.partida.mapa, respuesta.data.partida.casilla_actual);
      setModalFinalAbierto(false);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setProcesando(false);
    }
  };

  const cerrarExplicacion = () => {
    setExplicacionAbierta(false);
    aplicarPregunta(partida?.estado === "en_curso" ? feedback?.siguientePregunta || null : null);
    setFeedback(null);
  };

  return (
    <section ref={gameFullscreenRef} className={`content game-page ${juegoActivo ? "game-page-active" : ""}`}>
      {!juegoActivo && (
        <div className="header-row">
          <div>
            <h1>Misión Matemática</h1>
            <p>Responde ejercicios y avanza por el recorrido.</p>
          </div>
        </div>
      )}

      {!juegoActivo && <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />}

      {!partida && !preparandoPartida && (
        <section className="game-start-panel">
          <div className={`game-start-grid ${idAsignacion ? "activity-start" : ""}`}>
            {!idAsignacion && (
              <label>
                <span>Tema</span>
                <ResponsiveSelect value={idTema} onChange={(evento) => setIdTema(evento.target.value)}>
                  <option value="">Seleccione un tema</option>
                  {Object.entries(temasPorCategoria).map(([categoria, temasCategoria]) => (
                    <optgroup key={categoria} label={categoria}>
                      {temasCategoria.map((tema) => (
                        <option key={`${tema.id_tema}-${tema.nombre_tema}`} value={tema.id_tema}>
                          {formatLabel(tema.nombre_tema)}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </ResponsiveSelect>
              </label>
            )}

            <button type="button" className="pixel-primary-button success" onClick={iniciarAventura} disabled={procesando}>
              {procesando ? "Iniciando..." : idAsignacion ? "Iniciar actividad" : "Iniciar juego"}
            </button>
          </div>
        </section>
      )}

      {preparandoPartida && !partida && (
        <div className="game-fullscreen-container game-loading-screen">
          <div className="game-loading-panel">Preparando aventura...</div>
        </div>
      )}

      {partida && (
        <div className="game-fullscreen-container">
          <GameBoard
            mapa={partida.mapa}
            personaje={partida.personaje}
            posicionVisual={posicionVisual}
            tipoAnimacion={tipoAnimacion}
            frameIndex={frameIndex}
          >
            <QuestionPanel
              partida={partida}
              pregunta={preguntaActual}
              disabled={
                procesando ||
                animando ||
                modalSalidaAbierto ||
                modalFinalAbierto ||
                explicacionAbierta ||
                orientacionVertical ||
                fullscreenPerdido ||
                partida.estado !== "en_curso"
              }
              onResponder={manejarRespuesta}
              onSalir={() => setModalSalidaAbierto(true)}
            />
            {mensaje.tipo === "error" && <div className="game-inline-alert">{mensaje.texto}</div>}
            {explicacionAbierta && feedback && (
              <div className="game-explanation-panel" role="dialog" aria-modal="true" aria-labelledby="explicacion-title">
                <h2 id="explicacion-title">Vamos a revisarlo</h2>
                <p className="game-correct-answer">Respuesta correcta: <strong>{feedback.respuestaCorrecta}</strong></p>
                <section className="game-procedure" aria-labelledby="procedure-title">
                  <h3 id="procedure-title">¿Cómo se resuelve?</h3>
                  <ol>
                    {feedback.explicacionPasos.map((paso, indice) => <li key={`${indice}-${paso}`}>{paso}</li>)}
                  </ol>
                </section>
                <span>¡Inténtalo de nuevo en el siguiente reto!</span>
                <button type="button" className="pixel-primary-button success" onClick={cerrarExplicacion}>Entendido</button>
              </div>
            )}
            {orientacionVertical && (
              <div className="game-blocking-overlay" role="alert">
                <strong>Gira tu dispositivo</strong>
                <span>Para jugar Misión Matemática, coloca tu dispositivo horizontalmente.</span>
              </div>
            )}
            {fullscreenPerdido && !orientacionVertical && (
              <div className="game-blocking-overlay" role="alert">
                <strong>Has salido de pantalla completa.</strong>
                <span>Para una mejor experiencia, activa pantalla completa.</span>
                <div className="game-overlay-actions">
                  <button type="button" className="pixel-primary-button success" onClick={solicitarPantallaCompleta}>
                    Volver a pantalla completa
                  </button>
                  <button type="button" className="danger" onClick={() => setModalSalidaAbierto(true)}>
                    Salir de la actividad
                  </button>
                </div>
              </div>
            )}
          </GameBoard>
        </div>
      )}

      <ExitGameModal
        abierto={modalSalidaAbierto}
        procesando={procesando}
        onCancelar={() => setModalSalidaAbierto(false)}
        onConfirmar={confirmarSalida}
      />
      <GameFinishedModal
        abierto={modalFinalAbierto}
        estado={partida?.estado}
        recompensa={recompensa}
        saldoMonedas={saldoMonedas}
        procesando={procesando}
        onContinuar={partida?.estado === "sin_vidas" ? continuarAventura : undefined}
        onVolverInicio={volverAActividades}
      />
    </section>
  );
};

export default JuegoPage;
