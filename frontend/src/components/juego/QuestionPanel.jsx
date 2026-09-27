import React from "react";
import LivesIndicator from "./LivesIndicator";
import MultipleChoiceQuestion from "./MultipleChoiceQuestion";
import NumericQuestion from "./NumericQuestion";

// Dibuja el HUD jugable: vidas, pregunta, respuestas y salida.
const QuestionPanel = ({ partida, pregunta, disabled, onResponder, onSalir }) => {
  if (!partida || !pregunta) {
    return null;
  }

  const questionKey = pregunta.id_ejercicio_generado || pregunta.id_ejercicio || pregunta.enunciado;

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

      <div className="game-hud-bottom">
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
      </div>
    </section>
  );
};

export default QuestionPanel;
