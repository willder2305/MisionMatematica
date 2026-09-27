import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelEmptyState from "../components/ui/PixelEmptyState";
import PixelLoader from "../components/ui/PixelLoader";
import { obtenerUsuarioLocal } from "../services/authService";
import { obtenerAsignacionesEstudiante } from "../services/asignacionesService";
import { navegarInternamente } from "../services/navigationService";
import { obtenerOnboarding } from "../services/onboardingService";
import { formatDateTime, formatLabel } from "../constants/uiLabels";

const ActividadesPage = () => {
  const [asignaciones, setAsignaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
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
    cargarActividades();
  }, []);

  const cargarActividades = async () => {
    // Obtiene actividades asignadas al estudiante autenticado.
    try {
      setCargando(true);
      const perfil = await obtenerOnboarding();
      if (perfil.data?.perfil?.modalidad !== "grupo_educativo") {
        navegarInternamente("/panel-estudiante", { replace: true });
        return;
      }
      const respuesta = await obtenerAsignacionesEstudiante();
      setAsignaciones(respuesta.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  if (cargando) {
    return <PixelLoader text="Cargando actividades..." />;
  }

  return (
    <section className="content activities-page">
      <div className="header-row">
        <div>
          <h1>Actividades</h1>
          <p>Asignaciones disponibles para tu grado y sección.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      {asignaciones.length === 0 ? (
        <section className="panel">
          <PixelEmptyState title="No hay actividades asignadas." description="Cuando tu docente publique una actividad, aparecerá aquí." />
        </section>
      ) : (
        <section className="activity-grid">
          {asignaciones.map((asignacion) => {
            const primerTema = asignacion.temas[0];
            const enlaceJuego = primerTema ? `/juego?asignacion=${asignacion.id_asignacion}` : "/juego";
            return (
              <article key={asignacion.id_asignacion} className="activity-card">
                <div>
                  <strong>{asignacion.nombre}</strong>
                  <span>{asignacion.grado || "Sin grado"} | {asignacion.seccion || "Todas las secciones"}</span>
                </div>
                {asignacion.instrucciones && <p>{asignacion.instrucciones}</p>}
                <dl>
                  <dt>Tipo</dt>
                  <dd>{formatLabel(asignacion.tipo)}</dd>
                  <dt>Preguntas</dt>
                  <dd>{asignacion.cantidad_preguntas}</dd>
                  <dt>Límite</dt>
                  <dd>{formatDateTime(asignacion.fecha_limite, "Sin límite")}</dd>
                  <dt>Partidas</dt>
                  <dd>{asignacion.cantidad_intentos_estudiante || asignacion.partidas_realizadas || 0}</dd>
                  <dt>Estado</dt>
                  <dd>{formatLabel(asignacion.estado_estudiante || "pendiente")}</dd>
                </dl>
                <div className="activity-topics">
                  {asignacion.temas.map((tema) => (
                    <span key={tema.id_tema}>{formatLabel(tema.nombre_tema)}</span>
                  ))}
                </div>
                <a className="pixel-primary-button success" href={enlaceJuego}>Jugar actividad</a>
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
};

export default ActividadesPage;
