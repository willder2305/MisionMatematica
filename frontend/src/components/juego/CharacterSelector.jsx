import React, { useState } from "react";
import { personajesConfig } from "../../config/personajesConfig";

/**
 * Funcion: CharacterSelector
 *
 * Descripcion:
 * Muestra los personajes disponibles y permite confirmar uno antes de crear la partida.
 *
 * Es llamada desde:
 * JuegoPage.jsx cuando el usuario presiona INICIAR JUEGO.
 *
 * Llama a:
 * onConfirmar(personaje) cuando el usuario pulsa COMENZAR.
 *
 * Parametros:
 * abierto, onConfirmar, onCancelar y procesando.
 *
 * Resultado:
 * Devuelve el personaje elegido al componente padre.
 *
 * Manejo de errores:
 * Deshabilita COMENZAR hasta que exista una seleccion valida.
 */
const CharacterSelector = ({ abierto, onConfirmar, onCancelar, procesando }) => {
  const [personajeSeleccionado, setPersonajeSeleccionado] = useState("");

  if (!abierto) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal game-selector-modal" role="dialog" aria-modal="true" aria-labelledby="selector-title">
        <h2 id="selector-title">Selección de personaje</h2>
        <div className="character-options">
          {Object.values(personajesConfig).map((personaje) => (
            <button
              key={personaje.id}
              type="button"
              className={`character-option ${personajeSeleccionado === personaje.id ? "selected" : ""}`}
              onClick={() => setPersonajeSeleccionado(personaje.id)}
            >
              <img className="pixel-art" src={personaje.seleccion} alt={personaje.nombre} loading="lazy" decoding="async" />
              <span>{personaje.nombre}</span>
            </button>
          ))}
        </div>
        <div className="modal-actions">
          <button type="button" className="secondary" onClick={onCancelar} disabled={procesando}>
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => onConfirmar(personajeSeleccionado)}
            disabled={!personajeSeleccionado || procesando}
          >
            {procesando ? "Creando..." : "Comenzar"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CharacterSelector;
