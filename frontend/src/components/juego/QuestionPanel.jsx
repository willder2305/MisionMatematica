import React from "react";
import LivesIndicator from "./LivesIndicator";
import MultipleChoiceQuestion from "./MultipleChoiceQuestion";
import NumericQuestion from "./NumericQuestion";

// Dibuja solo el HUD superior para que el escenario conserve sus capas propias.
const QuestionPanel = ({ partida, pregunta }) => {
  if (!partida || !pregunta) {
    return null;
  }

  return (
    <section className="question-panel">
      <div className="game-hud-top">
        <div className="game-lives-panel">
          <span>VIDAS</span>
          <LivesIndicator restantes={partida.vidas_restantes} total={partida.vidas_iniciales} />
        </div>

        <div className="question-card">
          <h2>{pregunta.enunciado}</h2>
        </div>
      </div>
    </section>
  );
};

// Mantiene las respuestas y la salida fuera del tablero en móviles horizontales.
export const GameBottomControls = ({ pregunta, disabled, onResponder, onSalir }) => {
  if (!pregunta) {
    return null;
  }

  const questionKey = pregunta.id_ejercicio_generado || pregunta.id_ejercicio || pregunta.enunciado;

  return (
    <section className="game-bottom-controls" aria-label="Controles de la actividad">
      <div className="game-answer-panel">
        <span className="game-answer-label">RESPUESTAS</span>
        {pregunta.tipo_respuesta === "seleccion_multiple" ? (
          <MultipleChoiceQuestion opciones={pregunta.opciones} disabled={disabled} onResponder={onResponder} />
        ) : (
          <NumericQuestion disabled={disabled} onResponder={onResponder} questionKey={questionKey} />
        )}
      </div>
      <button type="button" className="game-exit-button" onClick={onSalir} disabled={disabled}>
        Salir
      </button>
    </section>
  );
};

export default QuestionPanel;
