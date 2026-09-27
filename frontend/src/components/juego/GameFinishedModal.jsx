import React from "react";
import CoinBalance from "../ui/CoinBalance";

/**
 * Funcion: GameFinishedModal
 *
 * Descripcion:
 * Celebra la meta o permite continuar la misma partida cuando ya no quedan vidas.
 *
 * Es llamada desde:
 * JuegoPage.jsx cuando la partida queda con estado completada.
 *
 * Llama a:
 * onContinuar() o onVolverInicio() segun el estado persistido.
 *
 * Parametros:
 * abierto, estado, recompensa, saldoMonedas, onContinuar y onVolverInicio.
 *
 * Resultado:
 * Renderiza el mensaje final del recorrido.
 *
 * Manejo de errores:
 * No consume API; solo cierra el flujo visual completado.
 */
const GameFinishedModal = ({ abierto, estado, recompensa, saldoMonedas, procesando, onContinuar, onVolverInicio }) => {
  if (!abierto) {
    return null;
  }

  const sinVidas = estado === "sin_vidas";
  const completada = estado === "completada";
  const perfecta = recompensa?.tipo === "perfecta";

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="finished-title">
        <h2 id="finished-title">{completada ? (perfecta ? "¡Partida perfecta!" : "¡Actividad completada!") : "¡Buen intento!"}</h2>
        {completada && <>
          <p>{perfecta ? "Conservaste todas tus vidas." : "Llegaste al final del recorrido."}</p>
          <div className="game-reward"><CoinBalance saldo={`+${recompensa?.monedas_ganadas || 0}`} tamano="medium" /><strong>{perfecta ? "¡Ganaste dos monedas!" : "¡Ganaste una moneda!"}</strong></div>
          <span className="game-balance-after">Ahora tienes <CoinBalance saldo={saldoMonedas} />.</span>
        </>}
        {sinVidas && <>
          <p>Puedes continuar desde esta casilla usando 1 moneda.</p>
          <span className="game-balance-after"><CoinBalance saldo={saldoMonedas} /> {Number(saldoMonedas || 0) < 1 ? "Necesitas 1 moneda para continuar." : ""}</span>
        </>}
        <div className="modal-actions">
          {sinVidas && onContinuar && (
            <button type="button" className="pixel-primary-button success" onClick={onContinuar} disabled={procesando || Number(saldoMonedas || 0) < 1}>
              {procesando ? "Continuando..." : "Continuar por 1 moneda"}
            </button>
          )}
          <button type="button" onClick={onVolverInicio}>
            Volver al menú
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameFinishedModal;
