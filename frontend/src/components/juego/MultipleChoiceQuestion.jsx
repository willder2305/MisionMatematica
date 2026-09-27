import React from "react";

// Renderiza opciones de seleccion multiple y envia el texto elegido.
const MultipleChoiceQuestion = ({ opciones = [], disabled, onResponder }) => (
  <div className="question-options">
    {opciones.map((opcion) => (
      <button
        key={opcion.id_opcion}
        type="button"
        className="question-option-button"
        onClick={() => onResponder(opcion.texto_opcion)}
        disabled={disabled}
      >
        {opcion.texto_opcion}
      </button>
    ))}
  </div>
);

export default MultipleChoiceQuestion;
