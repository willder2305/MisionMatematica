import React from "react";

// Muestra resultado de la respuesta y mensaje breve del agente.
const AgentFeedback = ({ feedback }) => {
  if (!feedback) {
    return null;
  }

  return (
    <div className={`agent-feedback ${feedback.correcta ? "correct" : "incorrect"}`} aria-live="polite">
      <strong>{feedback.correcta ? "Respuesta correcta" : "Respuesta incorrecta"}</strong>
      {feedback.explicacion && <p>{feedback.explicacion}</p>}
      {feedback.agente?.mensaje && <span>{feedback.agente.mensaje}</span>}
    </div>
  );
};

export default AgentFeedback;
