import React from "react";

/**
 * Funcion: ExitGameModal
 *
 * Descripcion:
 * Solicita confirmacion antes de abandonar una partida en curso.
 *
 * Es llamada desde:
 * JuegoPage.jsx cuando modalSalidaAbierto es true.
 *
 * Llama a:
 * onCancelar() o onConfirmar() segun la decision del usuario.
 *
 * Parametros:
 * abierto, procesando, onCancelar y onConfirmar.
 *
 * Resultado:
 * Renderiza un modal sin usar window.confirm().
 *
 * Manejo de errores:
 * Bloquea botones mientras se envia la solicitud de salida al backend.
 */
const ExitGameModal = ({ abierto, procesando, onCancelar, onConfirmar }) => {
  if (!abierto) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="exit-game-title">
        <h2 id="exit-game-title">¿Deseas salir de la actividad?</h2>
        <p>La actividad quedará pendiente para continuar después.</p>
        <div className="modal-actions">
          <button type="button" className="secondary" onClick={onCancelar} disabled={procesando}>
            Continuar jugando
          </button>
          <button type="button" className="danger" onClick={onConfirmar} disabled={procesando}>
            {procesando ? "Saliendo..." : "Salir"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExitGameModal;
