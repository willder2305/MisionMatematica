import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelEmptyState from "../components/ui/PixelEmptyState";
import PixelLoader from "../components/ui/PixelLoader";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { formatLabel } from "../constants/uiLabels";
import { obtenerUsuarioLocal } from "../services/authService";
import {
  obtenerClasificacionEstudiante,
  obtenerTemasEstudiante,
} from "../services/estudianteService";
import { navegarInternamente } from "../services/navigationService";


const LIMITE = 25;


const ClasificacionPage = () => {
  const [temas, setTemas] = useState([]);
  const [temaId, setTemaId] = useState("");
  const [scope, setScope] = useState("general");
  const [pagina, setPagina] = useState(1);
  const [clasificacion, setClasificacion] = useState(null);
  const [cargandoTemas, setCargandoTemas] = useState(true);
  const [cargandoTabla, setCargandoTabla] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const usuario = obtenerUsuarioLocal();

  useEffect(() => {
    if (!usuario) {
      navegarInternamente("/login", { replace: true });
      return;
    }
    if (usuario.rol !== "estudiante") {
      navegarInternamente("/secciones", { replace: true });
      return;
    }
    if (!usuario.onboarding_completado) {
      navegarInternamente("/onboarding", { replace: true });
      return;
    }

    const cargarTemas = async () => {
      try {
        setCargandoTemas(true);
        const respuesta = await obtenerTemasEstudiante();
        const temasDisponibles = respuesta.data?.temas || [];
        setTemas(temasDisponibles);
        setTemaId((actual) => actual || String(temasDisponibles[0]?.id_tema || ""));
      } catch (error) {
        setMensaje({ tipo: "error", texto: error.message });
      } finally {
        setCargandoTemas(false);
      }
    };
    cargarTemas();
  }, []);

  useEffect(() => {
    if (!temaId) return;
    let activo = true;
    const cargarClasificacion = async () => {
      try {
        setCargandoTabla(true);
        setMensaje({ tipo: "", texto: "" });
        const respuesta = await obtenerClasificacionEstudiante({ temaId, scope, page: pagina, limit: LIMITE });
        if (!activo) return;
        const datos = respuesta.data;
        if (scope === "grupo" && !datos?.puede_ver_grupo) {
          setScope("general");
          return;
        }
        setClasificacion(datos);
      } catch (error) {
        if (activo) setMensaje({ tipo: "error", texto: error.message });
      } finally {
        if (activo) setCargandoTabla(false);
      }
    };
    cargarClasificacion();
    return () => { activo = false; };
  }, [temaId, scope, pagina]);

  const cambiarTema = (evento) => {
    setTemaId(evento.target.value);
    setPagina(1);
  };

  const cambiarScope = (nuevoScope) => {
    setScope(nuevoScope);
    setPagina(1);
  };

  if (cargandoTemas) return <PixelLoader text="Preparando clasificación..." />;

  const participantes = clasificacion?.participantes || [];
  const paginacion = clasificacion?.paginacion || { page: 1, total: 0, limit: LIMITE };
  const totalPaginas = Math.max(1, Math.ceil(paginacion.total / paginacion.limit));
  const temaActual = temas.find((tema) => String(tema.id_tema) === String(temaId));

  return (
    <section className="content classification-page">
      <div className="student-page-heading">
        <div>
          <p className="child-kicker">Tu avance académico</p>
          <h1>Clasificación</h1>
          <p>Compara tu puntuación por tema con otros exploradores.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="panel classification-controls">
        <label>
          <span>Tema</span>
          <ResponsiveSelect name="tema" value={temaId} onChange={cambiarTema} aria-label="Seleccionar tema">
            {temas.map((tema) => (
              <option key={tema.id_tema} value={tema.id_tema}>{formatLabel(tema.nombre_tema || tema.tema_nombre)}</option>
            ))}
          </ResponsiveSelect>
        </label>
        <div className="classification-score" aria-live="polite">
          <span>Tu puntuación en {formatLabel(clasificacion?.tema?.nombre_tema || temaActual?.nombre_tema || temaActual?.tema_nombre || "este tema")}</span>
          <strong>{clasificacion?.mi_puntuacion || 0} puntos</strong>
        </div>
      </section>

      <section className="classification-tabs" aria-label="Alcance de clasificación">
        <button type="button" className={scope === "general" ? "is-active" : ""} onClick={() => cambiarScope("general")}>General</button>
        {clasificacion?.puede_ver_grupo && (
          <button type="button" className={scope === "grupo" ? "is-active" : ""} onClick={() => cambiarScope("grupo")}>Mi grupo</button>
        )}
      </section>

      <section className="panel classification-results" aria-busy={cargandoTabla}>
        <h2>{scope === "grupo" ? "Puntuación de mi grupo" : "Puntuación general"}</h2>
        {cargandoTabla ? (
          <PixelLoader text="Actualizando puntuaciones..." />
        ) : participantes.length === 0 ? (
          <PixelEmptyState title="Todavía no hay puntuaciones en este tema." description="Las respuestas correctas suman 2 puntos." />
        ) : (
          <>
            <div className="classification-table-wrap">
              <table className="classification-table">
                <thead><tr><th>Nombre</th><th>Personaje</th><th>Tema</th><th>Puntuación</th></tr></thead>
                <tbody>{participantes.map((participante, indice) => {
                  const personaje = obtenerPersonajeConfig(participante.personaje_key);
                  return <tr key={`${participante.nombre}-${indice}`}>
                    <td>{participante.nombre}</td>
                    <td><span className="classification-character"><img className="pixel-art" src={personaje.vistas[0]} alt="" /><span>{personaje.nombre}</span></span></td>
                    <td>{formatLabel(participante.tema)}</td>
                    <td><strong>{participante.puntos} puntos</strong></td>
                  </tr>;
                })}</tbody>
              </table>
            </div>
            <div className="classification-cards">
              {participantes.map((participante, indice) => {
                const personaje = obtenerPersonajeConfig(participante.personaje_key);
                return <article key={`${participante.nombre}-${indice}`}>
                  <span className="classification-character"><img className="pixel-art" src={personaje.vistas[0]} alt="" /><strong>{participante.nombre}</strong></span>
                  <span>Personaje: {personaje.nombre}</span>
                  <span>Tema: {formatLabel(participante.tema)}</span>
                  <strong>{participante.puntos} puntos</strong>
                </article>;
              })}
            </div>
          </>
        )}

        {paginacion.total > LIMITE && (
          <nav className="classification-pagination" aria-label="Paginación de clasificación">
            <button type="button" className="secondary" disabled={pagina <= 1} onClick={() => setPagina((actual) => actual - 1)}>Anterior</button>
            <span>Página {paginacion.page} de {totalPaginas}</span>
            <button type="button" className="secondary" disabled={pagina >= totalPaginas} onClick={() => setPagina((actual) => actual + 1)}>Siguiente</button>
          </nav>
        )}
      </section>
    </section>
  );
};


export default ClasificacionPage;
