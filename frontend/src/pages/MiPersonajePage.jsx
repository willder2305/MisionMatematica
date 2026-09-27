import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import CoinBalance from "../components/ui/CoinBalance";
import { obtenerMapaConfig } from "../config/mapasConfig";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { actualizarMapa, actualizarPersonaje, obtenerTienda } from "../services/personalizacionService";

const MiPersonajePage = () => {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });

  const cargar = async () => {
    try {
      setCargando(true);
      setDatos((await obtenerTienda()).data);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => { cargar(); }, []);

  const seleccionarPersonaje = async (personaje) => {
    try {
      setGuardando(true);
      const respuesta = await actualizarPersonaje(personaje.key);
      setDatos(respuesta.data);
      setMensaje({ tipo: "success", texto: "Tu personaje está listo para la próxima aventura." });
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setGuardando(false);
    }
  };

  const seleccionarMapa = async (modo, mapa = null) => {
    try {
      setGuardando(true);
      const respuesta = await actualizarMapa(modo, mapa?.key);
      setDatos(respuesta.data);
      setMensaje({ tipo: "success", texto: modo === "aleatorio" ? "Tus mapas cambiarán en cada aventura." : "Mapa seleccionado para tus próximas partidas." });
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) return <PixelLoader text="Preparando tu personaje..." />;

  const personajes = (datos?.personajes || []).filter((item) => item.desbloqueado);
  const mapas = (datos?.mapas || []).filter((item) => item.desbloqueado);
  const preferencias = datos?.preferencias || {};

  return (
    <section className="content personalizacion-page">
      <div className="student-page-heading">
        <div><h1>Mi personaje</h1><p>Elige quién te acompañará en la aventura.</p></div>
        <CoinBalance saldo={datos?.saldo_monedas} />
      </div>
      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />
      <section className="personalizacion-section">
        <h2>Personajes desbloqueados</h2>
        <div className="personalizacion-grid">
          {personajes.map((item) => {
            const config = obtenerPersonajeConfig(item.key);
            return <article className={`personalizacion-card ${item.seleccionado ? "selected" : ""}`} key={item.key}>
              <img className="pixel-art personalizacion-character" src={config.vistas[0]} alt={item.nombre} />
              <strong>{item.nombre}</strong>
              <button type="button" className="pixel-primary-button" disabled={guardando || item.seleccionado} onClick={() => seleccionarPersonaje(item)}>
                {item.seleccionado ? "Personaje actual" : "Seleccionar"}
              </button>
            </article>;
          })}
        </div>
      </section>
      <section className="personalizacion-section">
        <h2>Mapa de la aventura</h2>
        <div className="map-mode-actions">
          <button type="button" className={`pixel-primary-button ${preferencias.modo_mapa === "aleatorio" ? "success" : ""}`} disabled={guardando || preferencias.modo_mapa === "aleatorio"} onClick={() => seleccionarMapa("aleatorio")}>Aleatorio</button>
          <span>Se elige entre tus mapas desbloqueados.</span>
        </div>
        <div className="personalizacion-grid map-grid">
          {mapas.map((item) => {
            const mapa = obtenerMapaConfig(item.key);
            const seleccionado = preferencias.modo_mapa === "fijo" && preferencias.mapa === item.key;
            return <article className={`personalizacion-card map-card ${seleccionado ? "selected" : ""}`} key={item.key}>
              <img className="pixel-art map-preview" src={mapa.asset} alt={item.nombre} />
              <strong>{item.nombre}</strong>
              <button type="button" className="pixel-primary-button" disabled={guardando || seleccionado} onClick={() => seleccionarMapa("fijo", item)}>{seleccionado ? "Mapa actual" : "Usar este mapa"}</button>
            </article>;
          })}
        </div>
      </section>
    </section>
  );
};

export default MiPersonajePage;
