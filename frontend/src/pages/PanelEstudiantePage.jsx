import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import CoinBalance from "../components/ui/CoinBalance";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { obtenerUsuarioLocal } from "../services/authService";
import { obtenerPanelEstudiante } from "../services/estudianteService";
import { navegarInternamente } from "../services/navigationService";
import { obtenerTienda } from "../services/personalizacionService";
import { formatLabel } from "../constants/uiLabels";

const estrellasTema = (tema) => {
  const intentos = Number(tema.total_intentos || 0);
  const aciertos = Number(tema.total_aciertos || 0);
  if (!intentos) return 0;
  return Math.max(1, Math.min(3, Math.round((aciertos / intentos) * 3)));
};

const PanelEstudiantePage = () => {
  const [panel, setPanel] = useState(null);
  const [personalizacion, setPersonalizacion] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const usuario = obtenerUsuarioLocal();

  useEffect(() => {
    if (!usuario) { navegarInternamente("/login", { replace: true }); return; }
    if (usuario.rol !== "estudiante") { navegarInternamente("/secciones", { replace: true }); return; }
    if (!usuario.onboarding_completado) { navegarInternamente("/onboarding", { replace: true }); return; }
    const cargar = async () => {
      try {
        setCargando(true);
        const [respuestaPanel, respuestaTienda] = await Promise.all([obtenerPanelEstudiante(), obtenerTienda()]);
        setPanel(respuestaPanel.data);
        setPersonalizacion(respuestaTienda.data);
      } catch (error) {
        setMensaje({ tipo: "error", texto: error.message });
      } finally {
        setCargando(false);
      }
    };
    cargar();
  }, []);

  if (cargando) return <PixelLoader text="Preparando tu aventura..." />;

  const personaje = obtenerPersonajeConfig(personalizacion?.preferencias?.personaje);
  const temas = (panel?.temas || []).slice(0, 4);
  return <section className="content student-dashboard child-dashboard">
    <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />
    <section className="child-welcome">
      <div>
        <p className="child-kicker">Tu aventura matemática</p>
        <h1>Hola, {usuario?.nombres || "explorador"}</h1>
        <p>¿Listo para descubrir un nuevo reto?</p>
        <div className="child-play-hud"><CoinBalance saldo={personalizacion?.saldo_monedas} /><button type="button" className="pixel-primary-button success child-play-button" onClick={() => navegarInternamente("/juego")}>Jugar</button></div>
      </div>
      <div className="child-character-showcase"><img className="pixel-art" src={personaje.vistas[0]} alt={personaje.nombre} /><strong>{personaje.nombre}</strong></div>
    </section>
    <section className="child-progress-section">
      <div><h2>Tu progreso</h2><p>{temas.length ? "Cada estrella muestra todo lo que ya has practicado." : "Comienza una aventura para descubrir tus primeras estrellas."}</p></div>
      <div className="child-topic-list">{temas.map((tema) => { const estrellas = estrellasTema(tema); return <article key={tema.id_tema} className="child-topic"><strong>{formatLabel(tema.nombre_tema)}</strong><span aria-label={`${estrellas} de 3 estrellas`}>{"★".repeat(estrellas)}{"☆".repeat(3 - estrellas)}</span></article>; })}</div>
    </section>
    <section className="child-quick-actions">
      <button type="button" onClick={() => navegarInternamente("/mi-personaje")}><span aria-hidden="true">P</span><strong>Mi personaje</strong><small>Cambia tu compañero</small></button>
      <button type="button" onClick={() => navegarInternamente("/tienda")}><span aria-hidden="true">T</span><strong>Tienda</strong><small>Descubre recompensas</small></button>
    </section>
  </section>;
};

export default PanelEstudiantePage;
