import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelEmptyState from "../components/ui/PixelEmptyState";
import PixelLoader from "../components/ui/PixelLoader";
import ReportExportButtons from "../components/ui/ReportExportButtons";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import {
  exportarReporteEstudiantesAdmin,
  obtenerCatalogosReportesAdmin,
  obtenerReporteEstudiantesAdmin,
} from "../services/adminService";
import { formatDateTime, formatLabel } from "../constants/uiLabels";

const filtrosIniciales = {
  modalidad: "",
  id_institucion: "",
  id_grado_base: "",
  id_tema: "",
  buscar_estudiante: "",
  fecha_inicio: "",
  fecha_fin: "",
  limite: 25,
  offset: 0,
};

const porcentaje = (valor) => `${Number(valor || 0).toFixed(2)}%`;
const mejora = (fila) => fila.improvement_status === "suficiente" ? `${Number(fila.improvement_percentage).toFixed(2)} pp` : "Sin datos suficientes";

const ReportesAdminPage = () => {
  const [catalogos, setCatalogos] = useState({ instituciones: [], grados_base: [], temas: [] });
  const [filtros, setFiltros] = useState(filtrosIniciales);
  const [reporte, setReporte] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [exportando, setExportando] = useState("");
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });

  const cargar = async (filtrosAplicados = filtrosIniciales) => {
    try {
      setCargando(true);
      const [resCatalogos, resReporte] = await Promise.all([
        obtenerCatalogosReportesAdmin(filtrosAplicados),
        obtenerReporteEstudiantesAdmin(filtrosAplicados),
      ]);
      setCatalogos(resCatalogos.data || { instituciones: [], grados_base: [], temas: [] });
      setReporte(resReporte.data);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => { cargar(); }, []);

  const cambiarFiltro = (evento) => {
    const { name, value } = evento.target;
    setFiltros((actual) => ({ ...actual, [name]: value, ...(name === "limite" ? { offset: 0 } : {}) }));
  };

  const aplicar = async (evento) => {
    evento.preventDefault();
    setMensaje({ tipo: "", texto: "" });
    const siguientes = { ...filtros, offset: 0 };
    setFiltros(siguientes);
    await cargar(siguientes);
  };

  const cambiarPagina = async (direccion) => {
    const siguiente = { ...filtros, offset: Math.max(0, Number(filtros.offset) + direccion * Number(filtros.limite)) };
    setFiltros(siguiente);
    await cargar(siguiente);
  };

  const limpiar = async () => {
    setFiltros(filtrosIniciales);
    await cargar(filtrosIniciales);
  };

  const exportar = async (formato) => {
    try {
      setExportando(formato);
      await exportarReporteEstudiantesAdmin(formato, filtros);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setExportando("");
    }
  };

  if (cargando && !reporte) return <PixelLoader text="Cargando reportes globales..." />;
  const filas = reporte?.filas || [];
  const paginacion = reporte?.paginacion || { total: 0, limite: Number(filtros.limite), offset: 0 };
  const puedeAnterior = Number(paginacion.offset) > 0;
  const puedeSiguiente = Number(paginacion.offset) + Number(paginacion.limite) < Number(paginacion.total);

  return (
    <section className="content reports-page">
      <div className="header-row"><div><h1>Reportes globales</h1><p>Seguimiento de estudiantes independientes e institucionales.</p></div></div>
      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />
      <section className="student-stats-grid reports-stats-grid">
        <article className="student-stat-card"><span>Estudiantes</span><strong>{reporte?.resumen?.estudiantes || 0}</strong></article>
        <article className="student-stat-card"><span>Intentos</span><strong>{reporte?.resumen?.intentos || 0}</strong></article>
        <article className="student-stat-card"><span>Acierto</span><strong>{porcentaje(reporte?.resumen?.precision_promedio)}</strong></article>
        <article className="student-stat-card"><span>Partidas</span><strong>{reporte?.resumen?.partidas || 0}</strong></article>
      </section>
      <section className="panel">
        <h2>Filtros</h2>
        <form className="reports-filter-form" onSubmit={aplicar}>
          <label><span>Modalidad</span><ResponsiveSelect name="modalidad" value={filtros.modalidad} onChange={cambiarFiltro}><option value="">Todas</option><option value="independiente">Independiente</option><option value="institucional">Institución</option></ResponsiveSelect></label>
          <label><span>Institución</span><ResponsiveSelect name="id_institucion" value={filtros.id_institucion} onChange={cambiarFiltro}><option value="">Todas</option>{catalogos.instituciones.map((item) => <option key={item.id_institucion} value={item.id_institucion}>{item.nombre}</option>)}</ResponsiveSelect></label>
          <label><span>Grado</span><ResponsiveSelect name="id_grado_base" value={filtros.id_grado_base} onChange={cambiarFiltro}><option value="">Todos</option>{catalogos.grados_base.map((item) => <option key={item.id_grado_base} value={item.id_grado_base}>{item.nombre_grado}</option>)}</ResponsiveSelect></label>
          <label><span>Tema</span><ResponsiveSelect name="id_tema" value={filtros.id_tema} onChange={cambiarFiltro}><option value="">Todos</option>{catalogos.temas.map((item) => <option key={item.id_tema} value={item.id_tema}>{formatLabel(item.nombre_tema)}</option>)}</ResponsiveSelect></label>
          <label><span>Estudiante</span><input name="buscar_estudiante" value={filtros.buscar_estudiante} onChange={cambiarFiltro} placeholder="Nombre, apellido o correo" /></label>
          <label><span>Desde</span><input type="datetime-local" name="fecha_inicio" value={filtros.fecha_inicio} onChange={cambiarFiltro} /></label>
          <label><span>Hasta</span><input type="datetime-local" name="fecha_fin" value={filtros.fecha_fin} onChange={cambiarFiltro} /></label>
          <label><span>Filas</span><ResponsiveSelect name="limite" value={String(filtros.limite)} onChange={cambiarFiltro}><option value="25">25</option><option value="50">50</option></ResponsiveSelect></label>
          <div className="form-actions reports-filter-actions"><button type="submit" disabled={cargando}>Aplicar</button><button type="button" className="secondary" onClick={limpiar} disabled={cargando}>Limpiar</button></div>
        </form>
        <ReportExportButtons cargando={exportando} onExportar={exportar} />
      </section>
      <section className="table-section">
        <h2>Estudiantes</h2>
        {filas.length === 0 ? <PixelEmptyState title="No hay actividad para estos filtros." description="Los registros aparecerán cuando los estudiantes completen intentos." /> : (
          <div className="table-wrapper"><table><thead><tr><th>Estudiante</th><th>Modalidad</th><th>Institución</th><th>Tema</th><th>Nivel actual</th><th>Acierto</th><th>Mejora</th><th>Última actividad</th></tr></thead><tbody>
            {filas.map((fila) => <tr key={`${fila.id_estudiante}-${fila.id_tema}-${fila.id_asignacion || "personal"}`}><td>{fila.estudiante}</td><td>{fila.modalidad}</td><td>{fila.institucion || "—"}</td><td>{formatLabel(fila.tema)}</td><td>{fila.nivel_actual}</td><td>{porcentaje(fila.precision)}</td><td>{mejora(fila)}</td><td>{formatDateTime(fila.ultima_actividad, "Sin actividad")}</td></tr>)}
          </tbody></table></div>
        )}
        <div className="form-actions reports-filter-actions"><button type="button" className="secondary" onClick={() => cambiarPagina(-1)} disabled={!puedeAnterior || cargando}>Anterior</button><span>{Number(paginacion.total) ? `${Number(paginacion.offset) + 1}-${Math.min(Number(paginacion.offset) + filas.length, Number(paginacion.total))} de ${paginacion.total}` : "0 resultados"}</span><button type="button" onClick={() => cambiarPagina(1)} disabled={!puedeSiguiente || cargando}>Siguiente</button></div>
      </section>
    </section>
  );
};

export default ReportesAdminPage;
