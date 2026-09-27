import React, { useEffect, useId, useRef, useState } from "react";

// Captura una respuesta numerica y la envia al backend.
const NumericQuestion = ({ disabled, onResponder, questionKey }) => {
  const [respuesta, setRespuesta] = useState("");
  const inputId = useId();
  const inputRef = useRef(null);

  useEffect(() => {
    setRespuesta("");
  }, [questionKey]);

  useEffect(() => {
    if (disabled) {
      return undefined;
    }

    const focusTimer = window.setTimeout(() => {
      inputRef.current?.focus({ preventScroll: true });
    }, 40);

    return () => window.clearTimeout(focusTimer);
  }, [disabled, questionKey]);

  // Evita enviar vacios y limpia el campo despues de responder.
  const enviar = (evento) => {
    evento.preventDefault();
    if (!respuesta.trim()) {
      return;
    }
    onResponder(respuesta);
    setRespuesta("");
  };

  return (
    <form className="numeric-question" onSubmit={enviar}>
      <label className="visually-hidden" htmlFor={inputId}>
        Respuesta numerica
      </label>
      <input
        ref={inputRef}
        id={inputId}
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        value={respuesta}
        onChange={(evento) => setRespuesta(evento.target.value)}
        placeholder="Escribe tu respuesta"
        disabled={disabled}
      />
      <button type="submit" className="pixel-primary-button" disabled={disabled || !respuesta.trim()}>
        Responder
      </button>
    </form>
  );
};

export default NumericQuestion;
