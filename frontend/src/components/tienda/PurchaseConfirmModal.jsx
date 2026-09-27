import React, { useEffect, useRef } from "react";
import CoinBalance from "../ui/CoinBalance";

/** Confirma una compra de tienda sin usar dialogs nativos del navegador. */
const PurchaseConfirmModal = ({ item, saldo, nombreUsuario, procesando, error, onCancelar, onConfirmar }) => {
  const cancelRef = useRef(null);
  const confirmRef = useRef(null);

  useEffect(() => {
    if (!item) return undefined;

    cancelRef.current?.focus();
    const manejarTeclado = (evento) => {
      if (evento.key === "Escape" && !procesando) {
        evento.preventDefault();
        onCancelar();
      }
      if (evento.key === "Tab") {
        const botones = [cancelRef.current, confirmRef.current].filter(Boolean);
        if (botones.length < 2) return;
        const primero = botones[0];
        const ultimo = botones[botones.length - 1];
        if (evento.shiftKey && document.activeElement === primero) {
          evento.preventDefault();
          ultimo.focus();
        } else if (!evento.shiftKey && document.activeElement === ultimo) {
          evento.preventDefault();
          primero.focus();
        }
      }
    };
    document.addEventListener("keydown", manejarTeclado);
    return () => document.removeEventListener("keydown", manejarTeclado);
  }, [item, onCancelar, procesando]);

  if (!item) return null;

  const saldoActual = Number(saldo || 0);
  const saldoPosterior = Math.max(0, saldoActual - Number(item.precio_monedas || 0));
  const saludo = nombreUsuario
    ? `${nombreUsuario}, ¿estás seguro de que quieres realizar esta compra?`
    : "¿Estás seguro de que quieres realizar esta compra?";

  return (
    <div
      className="modal-backdrop purchase-modal-backdrop"
      role="presentation"
      onMouseDown={(evento) => {
        if (!procesando && evento.target === evento.currentTarget) onCancelar();
      }}
    >
      <section className="modal purchase-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="purchase-confirm-title" aria-describedby="purchase-confirm-message">
        <h2 id="purchase-confirm-title">Confirmar compra</h2>
        <p id="purchase-confirm-message">{saludo}</p>
        <div className="purchase-confirm-item">
          <img className={`pixel-art purchase-confirm-preview ${item.tipo === "mapa" ? "map-preview" : ""}`} src={item.preview} alt={item.nombre} />
          <strong>{item.nombre}</strong>
          <span>Precio</span>
          <CoinBalance saldo={item.precio_monedas} tamano="medium" />
        </div>
        <div className="purchase-confirm-balances">
          <span>Tus monedas</span><CoinBalance saldo={saldoActual} />
          <span>Después de la compra</span><CoinBalance saldo={saldoPosterior} />
        </div>
        {error && <p className="purchase-confirm-error" role="alert">{error}</p>}
        <div className="modal-actions purchase-confirm-actions">
          <button ref={cancelRef} type="button" className="pixel-primary-button" onClick={onCancelar} disabled={procesando}>Cancelar</button>
          <button ref={confirmRef} type="button" className="pixel-primary-button success" onClick={onConfirmar} disabled={procesando}>
            {procesando ? "Comprando..." : "Confirmar compra"}
          </button>
        </div>
      </section>
    </div>
  );
};

export default PurchaseConfirmModal;
