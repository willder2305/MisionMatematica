import React from "react";
import corazonActivo from "../../assets/juego/ui/corazon_vida.png";
import corazonPerdido from "../../assets/juego/ui/corazon_vida_perdida.png";

// Representa cinco espacios de vida y cambia cada corazon perdido a gris.
const LivesIndicator = ({ restantes = 0, total = 5 }) => (
  <div className="lives-indicator" aria-label={`Vidas restantes: ${restantes} de ${total}`}>
    {Array.from({ length: total }).map((_, index) => (
      <img
        key={index}
        className={`life-heart pixel-art ${index < restantes ? "active" : "lost"}`}
        src={index < restantes ? corazonActivo : corazonPerdido}
        alt={index < restantes ? "Vida disponible" : "Vida perdida"}
        draggable="false"
      />
    ))}
  </div>
);

export default LivesIndicator;
