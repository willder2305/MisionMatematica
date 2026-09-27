import React from "react";
import monedaAsset from "../../assets/juego/ui/moneda.png";

/**
 * Muestra un saldo confirmado por el backend junto a la moneda pixel-art.
 *
 * La memorización evita redibujar este elemento decorativo cuando su padre
 * cambia por estados que no afectan el saldo, por ejemplo durante una animación.
 */
const CoinBalance = ({ saldo = 0, className = "", tamano = "small" }) => (
  <span className={`coin-balance coin-balance-${tamano} ${className}`.trim()}>
    <img className="pixel-art" src={monedaAsset} alt="Moneda" />
    <strong>{typeof saldo === "string" && saldo.startsWith("+") ? saldo : Number(saldo || 0)}</strong>
  </span>
);

export default React.memo(CoinBalance);
