import React, { useEffect, useRef, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import CoinBalance from "../components/ui/CoinBalance";
import PurchaseConfirmModal from "../components/tienda/PurchaseConfirmModal";
import { obtenerMapaConfig } from "../config/mapasConfig";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { obtenerUsuarioLocal } from "../services/authService";
import { actualizarPersonaje, comprarItem, obtenerTienda } from "../services/personalizacionService";

/**
 * Presenta el catálogo personal del estudiante y su inventario real.
 *
 * Las compras, el saldo, los personajes desbloqueados y el mapa elegido se
 * confirman siempre con Flask; esta pantalla solo conserva el estado visual
 * de la respuesta recibida y no calcula monedas localmente.
 */
const TiendaPage = () => {
  const [datos, setDatos] = useState(null);
  const [indice, setIndice] = useState(0);
  const [vista, setVista] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [ocupado, setOcupado] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [compraPendiente, setCompraPendiente] = useState(null);
  const [errorCompra, setErrorCompra] = useState("");
  const touchStart = useRef(null);
  const botonCompraRef = useRef(null);
  const personajes = datos?.personajes || [];
  const personaje = personajes[indice] || null;
  const nombreUsuario = String(obtenerUsuarioLocal()?.nombres || "").trim();

  /** Obtiene catálogo, inventario y saldo en una única lectura al abrir la pantalla. */
  const cargar = async () => {
    try { setCargando(true); setDatos((await obtenerTienda()).data); } catch (error) { setMensaje({ tipo: "error", texto: error.message }); } finally { setCargando(false); }
  };
  useEffect(() => { cargar(); }, []);
  useEffect(() => {
    if (!personaje) return undefined;
    const temporizador = window.setInterval(() => setVista((actual) => (actual + 1) % 3), 2000);
    return () => window.clearInterval(temporizador);
  }, [personaje?.key]);

  const cambiar = (delta) => {
    if (!personajes.length) return;
    setVista(0);
    setIndice((actual) => (actual + delta + personajes.length) % personajes.length);
  };
  /** Abre el modal propio de compra sin ejecutar una mutación todavía. */
  const abrirCompra = (item, boton) => {
    if (!item || ocupado || item.desbloqueado) return;
    botonCompraRef.current = boton;
    const configuracion = item.tipo === "mapa" ? obtenerMapaConfig(item.key) : obtenerPersonajeConfig(item.key);
    setErrorCompra("");
    setCompraPendiente({ ...item, preview: item.tipo === "mapa" ? configuracion.asset : configuracion.vistas[0] });
  };
  const cancelarCompra = () => {
    if (ocupado) return;
    setCompraPendiente(null);
    setErrorCompra("");
    botonCompraRef.current?.focus();
  };
  /** Ejecuta una sola compra y reemplaza el estado por la respuesta transaccional del backend. */
  const confirmarCompra = async () => {
    if (!compraPendiente || ocupado) return;
    try {
      setOcupado(true);
      setErrorCompra("");
      const respuesta = await comprarItem(compraPendiente.id_item);
      setDatos(respuesta.data);
      setCompraPendiente(null);
      setMensaje({ tipo: "success", texto: `${compraPendiente.nombre} ya es tuyo.` });
      botonCompraRef.current?.focus();
    } catch (error) {
      setErrorCompra(error.message || "No fue posible realizar la compra. Intenta nuevamente.");
    } finally {
      setOcupado(false);
    }
  };
  /** Persiste un personaje ya desbloqueado y evita clics simultáneos mientras responde la API. */
  const seleccionar = async (item) => {
    try { setOcupado(true); const respuesta = await actualizarPersonaje(item.key); setDatos(respuesta.data); setMensaje({ tipo: "success", texto: "Personaje seleccionado." }); } catch (error) { setMensaje({ tipo: "error", texto: error.message }); } finally { setOcupado(false); }
  };
  const manejarTouchFin = (evento) => {
    if (touchStart.current === null) return;
    const distancia = evento.changedTouches[0].clientX - touchStart.current;
    if (Math.abs(distancia) > 35) cambiar(distancia < 0 ? 1 : -1);
    touchStart.current = null;
  };
  if (cargando) return <PixelLoader text="Abriendo la tienda..." />;
  const config = personaje ? obtenerPersonajeConfig(personaje.key) : null;
  const puedeComprar = personaje && !personaje.desbloqueado && datos.saldo_monedas >= personaje.precio_monedas;
  return <section className="content tienda-page">
    <div className="student-page-heading"><div><h1>Tienda</h1><p>Desbloquea nuevos compañeros y lugares para jugar.</p></div><CoinBalance saldo={datos?.saldo_monedas} /></div>
    <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />
    {personaje && <section className="store-carousel" onTouchStart={(evento) => { touchStart.current = evento.touches[0].clientX; }} onTouchEnd={manejarTouchFin}>
      <button type="button" className="carousel-control" aria-label="Personaje anterior" onClick={() => cambiar(-1)}>Anterior</button>
      <article className="store-character-card">
        <img className="pixel-art store-character-preview" src={config.vistas[vista]} alt={personaje.nombre} />
        <h2>{personaje.nombre}</h2>
        {personaje.seleccionado ? <strong>Personaje actual</strong> : personaje.desbloqueado ? <button type="button" className="pixel-primary-button" disabled={ocupado} onClick={() => seleccionar(personaje)}>Seleccionar</button> : <><CoinBalance saldo={personaje.precio_monedas} className="store-price" /><button type="button" className="pixel-primary-button success" disabled={!puedeComprar || ocupado} onClick={(evento) => abrirCompra(personaje, evento.currentTarget)}>{puedeComprar ? "Comprar" : "Necesitas más monedas"}</button></>}
      </article>
      <button type="button" className="carousel-control" aria-label="Siguiente personaje" onClick={() => cambiar(1)}>Siguiente</button>
    </section>}
    <section className="store-maps"><h2>Mapas</h2><div className="store-map-grid">{(datos?.mapas || []).map((item) => { const mapa = obtenerMapaConfig(item.key); const disponible = datos.saldo_monedas >= item.precio_monedas; return <article className="store-map-card" key={item.key}><img className="pixel-art map-preview" src={mapa.asset} alt={item.nombre} loading="lazy" decoding="async" /><strong>{item.nombre}</strong>{item.desbloqueado ? <span>Desbloqueado</span> : <><CoinBalance saldo={item.precio_monedas} className="store-price" /><button type="button" className="pixel-primary-button success" disabled={!disponible || ocupado} onClick={(evento) => abrirCompra(item, evento.currentTarget)}>{disponible ? "Comprar" : "Necesitas más monedas"}</button></>}</article>; })}</div></section>
    <PurchaseConfirmModal item={compraPendiente} saldo={datos?.saldo_monedas} nombreUsuario={nombreUsuario} procesando={ocupado} error={errorCompra} onCancelar={cancelarCompra} onConfirmar={confirmarCompra} />
  </section>;
};

export default TiendaPage;
