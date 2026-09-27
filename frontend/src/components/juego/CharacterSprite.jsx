import React from "react";
import { obtenerFrameActual, obtenerPersonajeConfig } from "../../config/personajesConfig";

/**
 * Renderiza el frame del personaje seleccionado sobre el tablero.
 *
 * La posición llega ya calculada desde las coordenadas oficiales de cada
 * casilla. Se aplica con `translate3d` para que los fotogramas de animación
 * no obliguen al navegador a recalcular el layout completo del escenario.
 */
const CharacterSprite = ({ personaje, posicion, tipoAnimacion, frameIndex }) => {
  const personajeConfig = obtenerPersonajeConfig(personaje);
  const frameActual = obtenerFrameActual(personajeConfig, tipoAnimacion, frameIndex);
  const feetAnchor = frameActual.feetAnchor || personajeConfig.feetAnchor;
  const spriteBox = personajeConfig.spriteBox;

  return (
    <div
      className="character-position"
      style={{ transform: `translate3d(${posicion.x}px, ${posicion.y}px, 0)` }}
      data-feet-anchor="true"
    >
      <div
        className="character-sprite-box"
        style={{
          "--character-width": spriteBox.width,
          "--character-height": spriteBox.height,
          "--feet-anchor-x": `${feetAnchor.x * 100}%`,
          "--feet-anchor-y": `${feetAnchor.y * 100}%`,
          "--frame-offset-x": `${frameActual.offset.x}px`,
          "--frame-offset-y": `${frameActual.offset.y}px`,
        }}
      >
        <img
          className={`character-sprite pixel-art ${tipoAnimacion === "error" ? "error" : ""}`}
          src={frameActual.src}
          alt={personajeConfig.nombre}
          decoding="async"
        />
      </div>
    </div>
  );
};

export default CharacterSprite;
