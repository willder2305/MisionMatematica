import React, { useEffect, useRef, useState } from "react";
import {
  DEBUG_POSITIONS,
  MAP_BASE_HEIGHT,
  MAP_BASE_WIDTH,
  obtenerMapaConfig,
  obtenerPosicionesDebug,
} from "../../config/mapasConfig";
import CharacterSprite from "./CharacterSprite";

const ESCALA_INICIAL = { scaleX: 0, scaleY: 0 };

// Convierte coordenadas logicas 1983x793 a pixeles del mapa visible actual.
const escalarPosicion = (posicion, escala) => ({
  x: posicion.x * escala.scaleX,
  y: posicion.y * escala.scaleY,
});

/**
 * Funcion: GameBoard
 *
 * Descripcion:
 * Muestra el mapa original y coloca encima el sprite calculando escala desde el mapa real.
 *
 * Es llamada desde:
 * JuegoPage.jsx cuando existe una partida activa.
 *
 * Llama a:
 * obtenerMapaConfig(), ResizeObserver, CharacterSprite y puntos de depuracion opcionales.
 *
 * Parametros:
 * mapa, personaje, posicionVisual logica, tipoAnimacion, frameIndex y children para el HUD.
 *
 * Resultado:
 * Renderiza un escenario responsive sin deformar el mapa ni acumular errores de coordenadas.
 *
 * Manejo de errores:
 * Si el mapa no existe, usa el mapa predeterminado configurado.
 */
const GameBoard = ({ mapa, personaje, posicionVisual, tipoAnimacion, frameIndex, children }) => {
  const mapaConfig = obtenerMapaConfig(mapa);
  const mapaRef = useRef(null);
  const resizeFrameRef = useRef(null);
  const [escalaMapa, setEscalaMapa] = useState(ESCALA_INICIAL);
  const mapaMedido = escalaMapa.scaleX > 0 && escalaMapa.scaleY > 0;
  const posicionRenderizada = escalarPosicion(posicionVisual, escalaMapa);

  useEffect(() => {
    const elementoMapa = mapaRef.current;
    if (!elementoMapa) {
      return undefined;
    }

    const actualizarEscala = () => {
      const rect = elementoMapa.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }

      setEscalaMapa((escalaActual) => {
        const siguienteEscala = {
          scaleX: rect.width / MAP_BASE_WIDTH,
          scaleY: rect.height / MAP_BASE_HEIGHT,
        };
        const sinCambios =
          Math.abs(escalaActual.scaleX - siguienteEscala.scaleX) < 0.0001 &&
          Math.abs(escalaActual.scaleY - siguienteEscala.scaleY) < 0.0001;
        return sinCambios ? escalaActual : siguienteEscala;
      });
    };

    // ResizeObserver puede dispararse varias veces durante una misma adaptación.
    // Se conserva solo la última medida del cuadro de animación para evitar renders redundantes.
    const programarActualizacionEscala = () => {
      if (resizeFrameRef.current) {
        return;
      }
      resizeFrameRef.current = requestAnimationFrame(() => {
        resizeFrameRef.current = null;
        actualizarEscala();
      });
    };

    actualizarEscala();
    const observer = new ResizeObserver(programarActualizacionEscala);
    observer.observe(elementoMapa);
    return () => {
      observer.disconnect();
      if (resizeFrameRef.current) {
        cancelAnimationFrame(resizeFrameRef.current);
        resizeFrameRef.current = null;
      }
    };
  }, [mapaConfig.asset]);

  return (
    <section className="game-board" aria-label="Escenario del juego">
      <div className="game-board-inner">
        <img
          ref={mapaRef}
          className="game-map pixel-art"
          src={mapaConfig.asset}
          alt={mapaConfig.nombre}
          decoding="async"
          onLoad={() => {
            const rect = mapaRef.current?.getBoundingClientRect();
            if (rect?.width && rect?.height) {
              setEscalaMapa({
                scaleX: rect.width / MAP_BASE_WIDTH,
                scaleY: rect.height / MAP_BASE_HEIGHT,
              });
            }
          }}
        />
        {DEBUG_POSITIONS &&
          mapaMedido &&
          obtenerPosicionesDebug().map((posicion) => {
            const punto = escalarPosicion(posicion, escalaMapa);
            return (
              <span
                className="debug-position-point"
                key={posicion.tile}
                style={{ left: `${punto.x}px`, top: `${punto.y}px` }}
              >
                {posicion.tile}
              </span>
            );
          })}
        {mapaMedido && (
          <CharacterSprite
            personaje={personaje}
            posicion={posicionRenderizada}
            tipoAnimacion={tipoAnimacion}
            frameIndex={frameIndex}
          />
        )}
        {children}
      </div>
    </section>
  );
};

export default GameBoard;
