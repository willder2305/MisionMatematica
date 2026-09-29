import React, { useEffect, useMemo, useState } from "react";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import PixelAlert from "../components/ui/PixelAlert";
import PixelEmptyState from "../components/ui/PixelEmptyState";
import PixelLoader from "../components/ui/PixelLoader";
import ReportExportButtons from "../components/ui/ReportExportButtons";
import { obtenerAsignaciones, obtenerContextoAsignaciones } from "../services/asignacionesService";
import { obtenerUsuarioLocal } from "../services/authService";
import { navegarInternamente } from "../services/navigationService";
import {
  obtenerDecisionesAgente,
  obtenerEstudiantesDocente,
  obtenerPanelDocente,
  obtenerReporteAgente,
  exportarReporteAgente,
} from "../services/reportesDocenteService";
import { obtenerTemasPorGrado } from "../services/temasService";
import { formatDateTime, formatLabel } from "../constants/uiLabels";

const filtrosIniciales = {
  id_institucion_grado: "",
  id_seccion: "",
  id_estudiante: "",
  id_tema: "",
  id_asignacion: "",
  fecha_inicio: "",
  fecha_fin: "",
};

const formatearPorcentaje = (valor) => `${Number(valor || 0).toFixed(2)}%`;
const formatearMejora = (fila) => fila.improvement_status === "suficiente" ? `${Number(fila.improvement_percentage).toFixed(2)} pp` : "Sin datos suficientes";

const formatearTiempo = (milisegundos) => {
  const segundosTotales = Math.floor(Number(milisegundos || 0) / 1000);
  const minutos = Math.floor(segundosTotales / 60);
  const segundos = segundosTotales % 60;
  if (minutos <= 0) return `${segundos}s`;
  return `${minutos}m ${segundos}s`;
};

const ReportesDocentePage = () => {
  const [panel, setPanel] = useState(null);
  const [estudiantes, setEstudiantes] = useState([]);
  const [gradosContexto, setGradosContexto] = useState([]);
  const [asignaciones, setAsignaciones] = useState([]);
  const [temas, setTemas] = useState([]);
  const [reporte, setReporte] = useState(null);
  const [decisiones, setDecisiones] = useState([]);
  const [filtros, setFiltros] = useState(filtrosIniciales);
  const [cargando, setCargando] = useState(true);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [exportando, setExportando] = useState("");
  const usuario = obtenerUsuarioLocal();

  useEffect(() => {
    if (!usuario) {
      navegarInternamente("/login", { replace: true });
      return;
    }
    if (!["docente", "administrador"].includes(usuario.rol)) {
      navegarInternamente("/panel-estudiante", { replace: true });
      return;
    }
    if (!usuario.onboarding_completado) {
      navegarInternamente("/onboarding", { replace: true });
      return;
    }
    cargarDatosIniciales();
  }, []);

  useEffect(() => {
    cargarTemasGrado();
  }, [filtros.id_institucion_grado, gradosContexto]);

  const cargarDatosIniciales = async () => {
    // Carga resumen, catalogos y reporte inicial del docente.
    try {
      setCargando(true);
      const [resPanel, resEstudiantes, resContexto, resAsignaciones, resReporte, resDecisiones] = await Promise.all([
        obtenerPanelDocente(),
        obtenerEstudiantesDocente(),
        obtenerContextoAsignaciones(),
        obtenerAsignaciones(),
        obtenerReporteAgente(),
        obtenerDecisionesAgente({ limite: 50 }),
      ]);
      setPanel(resPanel.data);
      setEstudiantes(resEstudiantes.data || []);
      setGradosContexto(resContexto.data || []);
      setAsignaciones(resAsignaciones.data || []);
      setReporte(resReporte.data);
      setDecisiones(resDecisiones.data?.decisiones || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const cargarTemasGrado = async () => {
    // Carga temas del grado base asociado al grado institucional seleccionado.
    const grado = gradosContexto.find((item) => String(item.id_institucion_grado) === String(filtros.id_institucion_grado));
    if (!grado) {
      setTemas([]);
      setFiltros((actual) => ({ ...actual, id_tema: "" }));
      return;
    }
    try {
      const respuesta = await obtenerTemasPorGrado(grado.id_grado_base);
      setTemas(respuesta.data || []);
    } catch (error) {
      setTemas([]);
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const cambiarFiltro = (evento) => {
    // Actualiza filtros del reporte y limpia dependencias invalidas.
    const { name, value } = evento.target;
    setFiltros((actual) => ({
      ...actual,
      [name]: value,
      ...(name === "id_institucion_grado" ? { id_seccion: "", id_tema: "", id_asignacion: "" } : {}),
    }));
  };

  const aplicarFiltros = async (evento) => {
    // Solicita al backend el reporte filtrado y la cronologia del agente.
    evento.preventDefault();
    try {
      setMensaje({ tipo: "", texto: "" });
      setCargando(true);
      const [resReporte, resDecisiones] = await Promise.all([
        obtenerReporteAgente(filtros),
        obtenerDecisionesAgente({ ...filtros, limite: 50 }),
      ]);
      setReporte(resReporte.data);
      setDecisiones(resDecisiones.data?.decisiones || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const limpiarFiltros = async () => {
    // Restaura filtros y vuelve al reporte general del docente.
    setFiltros(filtrosIniciales);
    try {
      setCargando(true);
      const [resReporte, resDecisiones] = await Promise.all([
        obtenerReporteAgente(),
        obtenerDecisionesAgente({ limite: 50 }),
      ]);
      setReporte(resReporte.data);
      setDecisiones(resDecisiones.data?.decisiones || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const exportarReporte = async (formato) => {
    // Solicita el archivo al backend usando exactamente los filtros ya aplicados.
    try {
      setExportando(formato);
      setMensaje({ tipo: "", texto: "" });
      await exportarReporteAgente(formato, filtros);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setExportando("");
    }
  };

  const seccionesDisponibles = useMemo(() => {
    const grado = gradosContexto.find((item) => String(item.id_institucion_grado) === String(filtros.id_institucion_grado));
    return grado?.secciones?.map((seccion) => ({ id_seccion: seccion.id_seccion, nombre: seccion.nombre_seccion })) || [];
  }, [gradosContexto, filtros.id_institucion_grado]);

  const estudiantesDisponibles = useMemo(
    () => estudiantes.filter((item) => !filtros.id_institucion_grado || String(item.id_institucion_grado) === String(filtros.id_institucion_grado)),
    [estudiantes, filtros.id_institucion_grado],
  );

  const asignacionesDisponibles = useMemo(
    () => asignaciones.filter((item) => !filtros.id_institucion_grado || String(item.id_institucion_grado) === String(filtros.id_institucion_grado)),
    [asignaciones, filtros.id_institucion_grado],
  );

  if (cargando && !reporte) {
    return <PixelLoader text="Cargando reportes docente..." />;
  }

  const resumen = reporte?.resumen || {};

  return (
    <section className="content reports-page">
      <div className="header-row">
        <div>
          <h1>Reportes docente</h1>
          <p>Progreso de estudiantes y decisiones del agente adaptativo.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="student-stats-grid reports-stats-grid">
        <article className="student-stat-card">
          <span>Grados</span>
          <strong>{panel?.total_grados || 0}</strong>
        </article>
        <article className="student-stat-card">
          <span>Estudiantes</span>
          <strong>{panel?.total_estudiantes || 0}</strong>
        </article>
        <article className="student-stat-card">
          <span>Asignaciones</span>
          <strong>{panel?.total_asignaciones || 0}</strong>
        </article>
        <article className="student-stat-card">
          <span>Intentos</span>
          <strong>{resumen.intentos || 0}</strong>
        </article>
        <article className="student-stat-card">
          <span>Aciertos</span>
          <strong>{formatearPorcentaje(resumen.porcentaje_aciertos)}</strong>
        </article>
        <article className="student-stat-card">
          <span>Tiempo prom.</span>
          <strong>{formatearTiempo(resumen.tiempo_promedio_ms)}</strong>
        </article>
      </section>

      <section className="panel">
        <h2>Filtros</h2>
        <form className="reports-filter-form" onSubmit={aplicarFiltros}>
          <label>
            <span>Grado</span>
            <ResponsiveSelect name="id_institucion_grado" value={filtros.id_institucion_grado} onChange={cambiarFiltro}>
              <option value="">Todos</option>
              {gradosContexto.map((grado) => (
                <option key={grado.id_institucion_grado} value={grado.id_institucion_grado}>
                  {grado.nombre_grado}
                </option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Sección</span>
            <ResponsiveSelect name="id_seccion" value={filtros.id_seccion} onChange={cambiarFiltro}>
              <option value="">Todas</option>
              {seccionesDisponibles.map((seccion) => (
                <option key={seccion.id_seccion} value={seccion.id_seccion}>{seccion.nombre}</option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Estudiante</span>
            <ResponsiveSelect name="id_estudiante" value={filtros.id_estudiante} onChange={cambiarFiltro}>
              <option value="">Todos</option>
              {estudiantesDisponibles.map((estudiante) => (
                <option key={`${estudiante.id_usuario}-${estudiante.id_institucion_grado || "base"}`} value={estudiante.id_usuario}>
                  {estudiante.nombres} {estudiante.apellidos}
                </option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Tema</span>
            <ResponsiveSelect name="id_tema" value={filtros.id_tema} onChange={cambiarFiltro} disabled={!filtros.id_institucion_grado}>
              <option value="">Todos</option>
              {temas.map((tema) => (
              <option key={tema.id_tema} value={tema.id_tema}>{formatLabel(tema.nombre_tema)}</option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Asignación</span>
            <ResponsiveSelect name="id_asignacion" value={filtros.id_asignacion} onChange={cambiarFiltro}>
              <option value="">Todas</option>
              {asignacionesDisponibles.map((asignacion) => (
                <option key={asignacion.id_asignacion} value={asignacion.id_asignacion}>{asignacion.nombre}</option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Desde</span>
            <input type="datetime-local" name="fecha_inicio" value={filtros.fecha_inicio} onChange={cambiarFiltro} />
          </label>
          <label>
            <span>Hasta</span>
            <input type="datetime-local" name="fecha_fin" value={filtros.fecha_fin} onChange={cambiarFiltro} />
          </label>
          <div className="form-actions reports-filter-actions">
            <button type="submit" disabled={cargando}>Aplicar</button>
            <button type="button" className="secondary" onClick={limpiarFiltros} disabled={cargando}>Limpiar</button>
          </div>
        </form>
        <ReportExportButtons cargando={exportando} onExportar={exportarReporte} />
      </section>

      <section className="reports-grid">
        <article className="panel">
          <h2>Decisiones adaptativas</h2>
          {(reporte?.decisiones_por_accion || []).length === 0 ? (
            <PixelEmptyState title="No hay decisiones registradas." description="El agente registrará decisiones cuando los estudiantes respondan." />
          ) : (
            <div className="report-bars">
              {reporte.decisiones_por_accion.map((item) => (
                <div key={item.accion} className={`report-bar ${item.accion}`}>
                  <span>{formatLabel(item.accion)}</span>
                  <strong>{item.total}</strong>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="panel">
          <h2>Reglas aplicadas</h2>
          {(reporte?.reglas_aplicadas || []).length === 0 ? (
            <PixelEmptyState title="Sin reglas aplicadas." description="Aparecerán después de registrar intentos." />
          ) : (
            <ul className="report-list">
              {reporte.reglas_aplicadas.map((item) => (
                <li key={item.regla}>
                  <span>{formatLabel(item.regla)}</span>
                  <strong>{item.total}</strong>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="panel">
        <h2>Alertas</h2>
        {(reporte?.alertas || []).length === 0 ? (
          <PixelEmptyState title="No hay alertas activas." description="No se detectaron temas con bajo rendimiento en los filtros actuales." />
        ) : (
          <div className="alerts-grid">
            {reporte.alertas.map((alerta, index) => (
              <article key={`${alerta.id_usuario}-${alerta.id_tema}-${index}`} className="alert-card">
                <strong>{alerta.estudiante}</strong>
                <span>{formatLabel(alerta.tema)} | {alerta.grado}</span>
                <p>{alerta.mensaje}</p>
                <dl>
                  <dt>Aciertos</dt>
                  <dd>{formatearPorcentaje(alerta.porcentaje_aciertos)}</dd>
                  <dt>Errores seguidos</dt>
                  <dd>{alerta.errores_consecutivos}</dd>
                  <dt>Refuerzos</dt>
                  <dd>{alerta.refuerzos}</dd>
                </dl>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="table-section">
        <h2>Progreso por tema</h2>
        {(reporte?.temas_dificultad || []).length === 0 ? (
          <PixelEmptyState title="No hay actividad para estos filtros." description="Los datos aparecerán cuando los estudiantes completen intentos." />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Estudiante</th>
                  <th>Grado</th>
                  <th>Tema</th>
                  <th>Intentos</th>
                  <th>Acierto</th>
                  <th>Mejora</th>
                  <th>Nivel actual</th>
                  <th>Última actividad</th>
                </tr>
              </thead>
              <tbody>
                {reporte.temas_dificultad.map((fila) => (
                  <tr key={`${fila.id_usuario}-${fila.id_tema}`}>
                    <td>{fila.estudiante}</td>
                    <td>{fila.grado}</td>
                    <td>{formatLabel(fila.tema)}</td>
                    <td>{fila.intentos}</td>
                    <td>{formatearPorcentaje(fila.porcentaje_aciertos)}</td>
                    <td>{formatearMejora(fila)}</td>
                    <td>{fila.nivel_actual}</td>
                    <td>{formatDateTime(fila.ultima_practica, "Sin actividad")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="table-section">
        <h2>Cronología de decisiones</h2>
        {decisiones.length === 0 ? (
          <PixelEmptyState title="No hay decisiones para mostrar." description="Ajusta los filtros o espera a que existan partidas respondidas." />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Estudiante</th>
                  <th>Pregunta</th>
                  <th>Resultado</th>
                  <th>Nivel anterior</th>
                  <th>Acción</th>
                  <th>Nivel nuevo</th>
                  <th>Regla</th>
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {decisiones.map((decision) => (
                  <tr key={decision.id_decision}>
                    <td>{formatDateTime(decision.fecha_decision)}</td>
                    <td>{decision.estudiante}</td>
                    <td>{decision.pregunta}</td>
                    <td>{formatLabel(decision.resultado)}</td>
                    <td>{decision.nivel_anterior}</td>
                    <td>{formatLabel(decision.accion)}</td>
                    <td>{decision.nivel_nuevo}</td>
                    <td>{decision.regla_aplicada}</td>
                    <td>{decision.motivo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
};

export default ReportesDocentePage;
