import React, { useEffect, useMemo, useState } from "react";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import PixelAlert from "../components/ui/PixelAlert";
import PixelEmptyState from "../components/ui/PixelEmptyState";
import PixelLoader from "../components/ui/PixelLoader";
import ReportExportButtons from "../components/ui/ReportExportButtons";
import {
  actualizarEjercicioAdmin,
  actualizarReglaAdmin,
  actualizarTemaAdmin,
  cambiarEstadoEjercicioAdmin,
  cambiarEstadoReglaAdmin,
  cambiarEstadoTemaAdmin,
  cambiarEstadoUsuarioAdmin,
  cambiarRolUsuarioAdmin,
  crearEjercicioAdmin,
  crearTemaAdmin,
  exportarReporteInstitucionalAdmin,
  obtenerAuditoriaAdmin,
  obtenerCatalogosReportesAdmin,
  obtenerEjerciciosAdmin,
  obtenerPanelAdmin,
  obtenerReporteInstitucionalAdmin,
  obtenerReglasAdmin,
  obtenerTemasAdmin,
  obtenerUsuariosAdmin,
} from "../services/adminService";
import { obtenerUsuarioLocal } from "../services/authService";
import { obtenerGrados } from "../services/gradosService";
import { navegarInternamente } from "../services/navigationService";
import { obtenerNivelesPlantillas } from "../services/plantillasService";
import { formatDateTime, formatLabel } from "../constants/uiLabels";

const temaInicial = {
  id_tema: null,
  id_grado: "",
  nombre_tema: "",
  descripcion: "",
  estado: "activo",
};

const ejercicioInicial = {
  id_ejercicio: null,
  id_tema: "",
  id_nivel: "",
  enunciado: "",
  tipo_respuesta: "numerica",
  respuesta_correcta: "",
  explicacion: "",
  pista: "",
  estado: "borrador",
  opciones: "",
};

const reglaInicial = {
  id_regla: null,
  nombre: "",
  descripcion: "",
  prioridad: 1,
  parametros_json: "{}",
  accion: "mantener",
  estado: "activo",
};

const filtroReporteInicial = {
  modalidad: "",
  id_institucion: "",
  id_grado_base: "",
  id_institucion_grado: "",
  id_seccion: "",
  id_docente: "",
  id_estudiante: "",
  id_tema: "",
  id_asignacion: "",
  fecha_inicio: "",
  fecha_fin: "",
  limite: 50,
  offset: 0,
};

const tabs = [
  { key: "usuarios", label: "Usuarios" },
  { key: "temas", label: "Temas" },
  { key: "ejercicios", label: "Ejercicios" },
  { key: "reglas", label: "Reglas" },
  { key: "auditoria", label: "Auditoría" },
];

const formatearPorcentaje = (valor) => `${Number(valor || 0).toFixed(2)}%`;

const AdminPage = () => {
  const [tabActiva, setTabActiva] = useState("usuarios");
  const [panel, setPanel] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [temas, setTemas] = useState([]);
  const [ejercicios, setEjercicios] = useState([]);
  const [reglas, setReglas] = useState([]);
  const [auditoria, setAuditoria] = useState([]);
  const [catalogosReporte, setCatalogosReporte] = useState({
    instituciones: [],
    grados_base: [],
    grados_institucionales: [],
    secciones: [],
    docentes: [],
    estudiantes: [],
    temas: [],
    asignaciones: [],
  });
  const [reporteAdmin, setReporteAdmin] = useState(null);
  const [grados, setGrados] = useState([]);
  const [niveles, setNiveles] = useState([]);
  const [formTema, setFormTema] = useState(temaInicial);
  const [formEjercicio, setFormEjercicio] = useState(ejercicioInicial);
  const [formRegla, setFormRegla] = useState(reglaInicial);
  const [filtroUsuario, setFiltroUsuario] = useState({ rol: "", estado: "", busqueda: "" });
  const [filtroTema, setFiltroTema] = useState({ id_grado: "", estado: "" });
  const [filtroEjercicio, setFiltroEjercicio] = useState({ id_tema: "", id_nivel: "", estado: "" });
  const [filtroAuditoria, setFiltroAuditoria] = useState({ accion: "", entidad: "", resultado: "", limite: 100 });
  const [filtroReporte, setFiltroReporte] = useState(filtroReporteInicial);
  const [cargando, setCargando] = useState(true);
  const [exportando, setExportando] = useState("");
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const usuario = obtenerUsuarioLocal();

  useEffect(() => {
    if (!usuario) {
      navegarInternamente("/login", { replace: true });
      return;
    }
    if (usuario.rol !== "administrador") {
      navegarInternamente(usuario.rol === "estudiante" ? "/panel-estudiante" : "/reportes", { replace: true });
      return;
    }
    cargarTodo();
  }, []);

  useEffect(() => {
    if (tabActiva === "reportes" && usuario?.rol === "administrador" && !reporteAdmin) {
      cargarReporteAdmin();
    }
  }, [tabActiva]);

  const cargarTodo = async () => {
    // Carga datos globales usados por el panel administrador.
    try {
      setCargando(true);
      const [resPanel, resUsuarios, resTemas, resEjercicios, resReglas, resAuditoria, resGrados, resNiveles] = await Promise.all([
        obtenerPanelAdmin(),
        obtenerUsuariosAdmin(),
        obtenerTemasAdmin(),
        obtenerEjerciciosAdmin(),
        obtenerReglasAdmin(),
        obtenerAuditoriaAdmin(),
        obtenerGrados(),
        obtenerNivelesPlantillas(),
      ]);
      setPanel(resPanel.data);
      setUsuarios(resUsuarios.data || []);
      setTemas(resTemas.data || []);
      setEjercicios(resEjercicios.data || []);
      setReglas(resReglas.data || []);
      setAuditoria(resAuditoria.data || []);
      setGrados(resGrados.data || []);
      setNiveles(resNiveles.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const cargarUsuarios = async () => {
    // Refresca usuarios aplicando filtros administrativos.
    const respuesta = await obtenerUsuariosAdmin(filtroUsuario);
    setUsuarios(respuesta.data || []);
  };

  const cargarTemas = async () => {
    // Refresca temas incluyendo activos e inactivos segun filtros.
    const respuesta = await obtenerTemasAdmin(filtroTema);
    setTemas(respuesta.data || []);
  };

  const cargarEjercicios = async () => {
    // Refresca ejercicios manuales con sus opciones.
    const respuesta = await obtenerEjerciciosAdmin(filtroEjercicio);
    setEjercicios(respuesta.data || []);
  };

  const cargarAuditoria = async () => {
    // Refresca eventos recientes de auditoria administrativa.
    const respuesta = await obtenerAuditoriaAdmin(filtroAuditoria);
    setAuditoria(respuesta.data || []);
  };

  const cargarReporteAdmin = async (filtros = filtroReporte) => {
    // Solicita catalogos y reporte paginado al backend con filtros institucionales.
    const [resCatalogos, resReporte] = await Promise.all([
      obtenerCatalogosReportesAdmin(filtros),
      obtenerReporteInstitucionalAdmin(filtros),
    ]);
    setCatalogosReporte(resCatalogos.data || catalogosReporte);
    setReporteAdmin(resReporte.data);
  };

  const aplicarFiltroUsuarios = async (evento) => {
    evento.preventDefault();
    try {
      await cargarUsuarios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const aplicarFiltroTemas = async (evento) => {
    evento.preventDefault();
    try {
      await cargarTemas();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const aplicarFiltroEjercicios = async (evento) => {
    evento.preventDefault();
    try {
      await cargarEjercicios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const aplicarFiltroAuditoria = async (evento) => {
    evento.preventDefault();
    try {
      await cargarAuditoria();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const aplicarFiltroReporte = async (evento) => {
    evento.preventDefault();
    try {
      await cargarReporteAdmin(filtroReporte);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const cambiarFiltroReporte = (evento) => {
    const { name, value } = evento.target;
    setFiltroReporte((actual) => ({
      ...actual,
      [name]: value,
      offset: 0,
      ...(name === "modalidad" && value === "independiente"
        ? { id_institucion: "", id_institucion_grado: "", id_seccion: "", id_docente: "", id_asignacion: "" }
        : {}),
      ...(name === "id_institucion" ? { id_institucion_grado: "", id_seccion: "", id_docente: "", id_estudiante: "", id_asignacion: "" } : {}),
      ...(name === "id_grado_base" ? { id_institucion_grado: "", id_seccion: "", id_tema: "", id_asignacion: "" } : {}),
      ...(name === "id_institucion_grado" ? { id_seccion: "", id_asignacion: "" } : {}),
      ...(name === "id_seccion" ? { id_estudiante: "", id_asignacion: "" } : {}),
    }));
  };

  const exportarReporteInstitucional = async (formato) => {
    // Descarga el reporte usando los mismos filtros institucionales visibles.
    try {
      setExportando(formato);
      setMensaje({ tipo: "", texto: "" });
      await exportarReporteInstitucionalAdmin(formato, filtroReporte);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setExportando("");
    }
  };

  const guardarTema = async (evento) => {
    // Crea o actualiza un tema curricular.
    evento.preventDefault();
    try {
      const payload = { ...formTema, id_grado: Number(formTema.id_grado) };
      const respuesta = formTema.id_tema
        ? await actualizarTemaAdmin(formTema.id_tema, payload)
        : await crearTemaAdmin(payload);
      setMensaje({ tipo: "success", texto: respuesta.message });
      setFormTema(temaInicial);
      await cargarTemas();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const editarTema = (tema) => {
    // Carga tema seleccionado en el formulario.
    setFormTema({
      id_tema: tema.id_tema,
      id_grado: String(tema.id_grado),
      nombre_tema: tema.nombre_tema,
      descripcion: tema.descripcion || "",
      estado: tema.estado,
    });
    setTabActiva("temas");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const alternarTema = async (tema) => {
    try {
      const estado = tema.estado === "activo" ? "inactivo" : "activo";
      const respuesta = await cambiarEstadoTemaAdmin(tema.id_tema, estado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      await cargarTemas();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const guardarEjercicio = async (evento) => {
    // Crea o actualiza un ejercicio manual del banco.
    evento.preventDefault();
    try {
      const payload = {
        ...formEjercicio,
        id_tema: Number(formEjercicio.id_tema),
        id_nivel: Number(formEjercicio.id_nivel),
        opciones: formEjercicio.opciones.split(",").map((opcion) => opcion.trim()).filter(Boolean),
      };
      const respuesta = formEjercicio.id_ejercicio
        ? await actualizarEjercicioAdmin(formEjercicio.id_ejercicio, payload)
        : await crearEjercicioAdmin(payload);
      setMensaje({ tipo: "success", texto: respuesta.message });
      setFormEjercicio(ejercicioInicial);
      await cargarEjercicios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const editarEjercicio = (ejercicio) => {
    // Carga ejercicio existente en el formulario admin.
    setFormEjercicio({
      id_ejercicio: ejercicio.id_ejercicio,
      id_tema: String(ejercicio.id_tema),
      id_nivel: String(ejercicio.id_nivel),
      enunciado: ejercicio.enunciado,
      tipo_respuesta: ejercicio.tipo_respuesta,
      respuesta_correcta: ejercicio.respuesta_correcta,
      explicacion: ejercicio.explicacion || "",
      pista: ejercicio.pista || "",
      estado: ejercicio.estado,
      opciones: (ejercicio.opciones || []).map((opcion) => opcion.texto_opcion).join(", "),
    });
    setTabActiva("ejercicios");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const alternarEjercicio = async (ejercicio) => {
    try {
      const estado = ejercicio.estado === "publicado" ? "desactivado" : "publicado";
      const respuesta = await cambiarEstadoEjercicioAdmin(ejercicio.id_ejercicio, estado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      await cargarEjercicios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const editarRegla = (regla) => {
    // Carga regla adaptativa para editar umbrales y estado futuro.
    setFormRegla({
      id_regla: regla.id_regla,
      nombre: regla.nombre,
      descripcion: regla.descripcion || "",
      prioridad: regla.prioridad,
      parametros_json: JSON.stringify(regla.parametros_json, null, 2),
      accion: regla.accion,
      estado: regla.estado,
    });
    setTabActiva("reglas");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const guardarRegla = async (evento) => {
    // Actualiza regla adaptativa para decisiones nuevas del agente.
    evento.preventDefault();
    if (!formRegla.id_regla) {
      setMensaje({ tipo: "error", texto: "Seleccione una regla para editar." });
      return;
    }
    try {
      const respuesta = await actualizarReglaAdmin(formRegla.id_regla, formRegla);
      setMensaje({ tipo: "success", texto: respuesta.message });
      setFormRegla(reglaInicial);
      const reglasRes = await obtenerReglasAdmin();
      setReglas(reglasRes.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const alternarRegla = async (regla) => {
    try {
      const estado = regla.estado === "activo" ? "inactivo" : "activo";
      const respuesta = await cambiarEstadoReglaAdmin(regla.id_regla, estado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      const reglasRes = await obtenerReglasAdmin();
      setReglas(reglasRes.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const cambiarEstadoUsuario = async (usuarioItem, estado) => {
    try {
      const respuesta = await cambiarEstadoUsuarioAdmin(usuarioItem.id_usuario, estado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      await cargarUsuarios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const cambiarRolUsuario = async (usuarioItem, rol) => {
    try {
      const respuesta = await cambiarRolUsuarioAdmin(usuarioItem.id_usuario, rol);
      setMensaje({ tipo: "success", texto: respuesta.message });
      await cargarUsuarios();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const temasOrdenados = useMemo(
    () => [...temas].sort((a, b) => `${a.nombre_grado}-${a.nombre_tema}`.localeCompare(`${b.nombre_grado}-${b.nombre_tema}`)),
    [temas],
  );

  if (cargando) {
    return <PixelLoader text="Cargando panel administrador..." />;
  }

  return (
    <section className="content admin-page">
      <div className="header-row">
        <div>
          <h1>Panel administrador</h1>
          <p>Usuarios, temas, ejercicios, reglas adaptativas y resumen general.</p>
        </div>
        <button
          type="button"
          className="pixel-primary-button success"
          onClick={() => navegarInternamente("/admin/plantillas")}
        >
          Plantillas
        </button>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="student-stats-grid admin-stats-grid">
        <article className="student-stat-card"><span>Usuarios</span><strong>{panel?.usuarios || 0}</strong></article>
        <article className="student-stat-card"><span>Partidas</span><strong>{panel?.partidas || 0}</strong></article>
        <article className="student-stat-card"><span>Generados</span><strong>{panel?.ejercicios_generados || 0}</strong></article>
        <article className="student-stat-card"><span>Plantillas</span><strong>{panel?.plantillas || 0}</strong></article>
        <article className="student-stat-card"><span>Temas</span><strong>{panel?.temas || 0}</strong></article>
        <article className="student-stat-card"><span>Decisiones</span><strong>{panel?.decisiones_agente || 0}</strong></article>
      </section>

      <nav className="admin-tabs" aria-label="Secciones administrador">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={tabActiva === tab.key ? "active" : ""}
            onClick={() => setTabActiva(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {tabActiva === "usuarios" && (
        <section className="panel">
          <h2>Usuarios</h2>
          <form className="admin-filter-form" onSubmit={aplicarFiltroUsuarios}>
            <input
              value={filtroUsuario.busqueda}
              onChange={(evento) => setFiltroUsuario((actual) => ({ ...actual, busqueda: evento.target.value }))}
              placeholder="Buscar por nombre o correo"
            />
            <ResponsiveSelect value={filtroUsuario.rol} onChange={(evento) => setFiltroUsuario((actual) => ({ ...actual, rol: evento.target.value }))}>
              <option value="">Todos los roles</option>
              <option value="administrador">Administrador</option>
              <option value="docente">Docente</option>
              <option value="estudiante">Estudiante</option>
            </ResponsiveSelect>
            <ResponsiveSelect value={filtroUsuario.estado} onChange={(evento) => setFiltroUsuario((actual) => ({ ...actual, estado: evento.target.value }))}>
              <option value="">Todos los estados</option>
              <option value="activo">Activo</option>
              <option value="inactivo">Inactivo</option>
              <option value="bloqueado">Bloqueado</option>
            </ResponsiveSelect>
            <button type="submit">Filtrar</button>
          </form>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Correo</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Onboarding</th>
                  <th>Intentos</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((item) => (
                  <tr key={item.id_usuario}>
                    <td>{item.nombres} {item.apellidos}</td>
                    <td>{item.correo}</td>
                    <td>
                      <ResponsiveSelect value={item.rol} onChange={(evento) => cambiarRolUsuario(item, evento.target.value)}>
                        <option value="administrador">Administrador</option>
                        <option value="docente">Docente</option>
                        <option value="estudiante">Estudiante</option>
                      </ResponsiveSelect>
                    </td>
                    <td>{formatLabel(item.estado)}</td>
                    <td>{item.onboarding_completado ? "Completo" : "Pendiente"}</td>
                    <td>{item.total_intentos}</td>
                    <td className="actions">
                      <button type="button" className="secondary" onClick={() => cambiarEstadoUsuario(item, item.estado === "activo" ? "inactivo" : "activo")}>
                        {item.estado === "activo" ? "Desactivar" : "Activar"}
                      </button>
                      <button type="button" className="danger" onClick={() => cambiarEstadoUsuario(item, "bloqueado")}>Bloquear</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tabActiva === "temas" && (
        <section className="panel">
          <h2>{formTema.id_tema ? "Editar tema" : "Nuevo tema"}</h2>
          <form className="admin-form" onSubmit={guardarTema}>
            <label><span>Grado</span><ResponsiveSelect value={formTema.id_grado} onChange={(evento) => setFormTema((actual) => ({ ...actual, id_grado: evento.target.value }))}><option value="">Seleccione</option>{grados.map((grado) => <option key={grado.id_grado} value={grado.id_grado}>{grado.nombre_grado}</option>)}</ResponsiveSelect></label>
            <label><span>Nombre</span><input value={formTema.nombre_tema} onChange={(evento) => setFormTema((actual) => ({ ...actual, nombre_tema: evento.target.value }))} /></label>
            <label><span>Estado</span><ResponsiveSelect value={formTema.estado} onChange={(evento) => setFormTema((actual) => ({ ...actual, estado: evento.target.value }))}><option value="activo">Activo</option><option value="inactivo">Inactivo</option></ResponsiveSelect></label>
            <label className="admin-form-wide"><span>Descripción</span><input value={formTema.descripcion} onChange={(evento) => setFormTema((actual) => ({ ...actual, descripcion: evento.target.value }))} /></label>
            <div className="form-actions admin-form-wide">
              <button type="submit">{formTema.id_tema ? "Actualizar" : "Crear"}</button>
              <button type="button" className="secondary" onClick={() => setFormTema(temaInicial)}>Limpiar</button>
            </div>
          </form>
          <form className="admin-filter-form" onSubmit={aplicarFiltroTemas}>
            <ResponsiveSelect value={filtroTema.id_grado} onChange={(evento) => setFiltroTema((actual) => ({ ...actual, id_grado: evento.target.value }))}><option value="">Todos los grados</option>{grados.map((grado) => <option key={grado.id_grado} value={grado.id_grado}>{grado.nombre_grado}</option>)}</ResponsiveSelect>
            <ResponsiveSelect value={filtroTema.estado} onChange={(evento) => setFiltroTema((actual) => ({ ...actual, estado: evento.target.value }))}><option value="">Todos los estados</option><option value="activo">Activo</option><option value="inactivo">Inactivo</option></ResponsiveSelect>
            <button type="submit">Filtrar</button>
          </form>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Grado</th><th>Tema</th><th>Descripción</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody>{temasOrdenados.map((tema) => <tr key={tema.id_tema}><td>{tema.nombre_grado}</td><td>{formatLabel(tema.nombre_tema)}</td><td>{tema.descripcion || "Sin descripción"}</td><td>{formatLabel(tema.estado)}</td><td className="actions"><button type="button" className="secondary" onClick={() => editarTema(tema)}>Editar</button><button type="button" className="secondary" onClick={() => alternarTema(tema)}>{tema.estado === "activo" ? "Desactivar" : "Activar"}</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
      )}

      {tabActiva === "ejercicios" && (
        <section className="panel">
          <h2>{formEjercicio.id_ejercicio ? "Editar ejercicio" : "Nuevo ejercicio"}</h2>
          <form className="admin-form" onSubmit={guardarEjercicio}>
            <label><span>Tema</span><ResponsiveSelect value={formEjercicio.id_tema} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, id_tema: evento.target.value }))}><option value="">Seleccione</option>{temasOrdenados.map((tema) => <option key={tema.id_tema} value={tema.id_tema}>{tema.nombre_grado} - {formatLabel(tema.nombre_tema)}</option>)}</ResponsiveSelect></label>
            <label><span>Nivel</span><ResponsiveSelect value={formEjercicio.id_nivel} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, id_nivel: evento.target.value }))}><option value="">Seleccione</option>{niveles.map((nivel) => <option key={nivel.id_nivel} value={nivel.id_nivel}>{nivel.nombre}</option>)}</ResponsiveSelect></label>
            <label><span>Tipo</span><ResponsiveSelect value={formEjercicio.tipo_respuesta} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, tipo_respuesta: evento.target.value }))}><option value="numerica">Numérica</option><option value="seleccion_multiple">Selección múltiple</option></ResponsiveSelect></label>
            <label><span>Estado</span><ResponsiveSelect value={formEjercicio.estado} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, estado: evento.target.value }))}><option value="borrador">Borrador</option><option value="publicado">Publicado</option><option value="desactivado">Desactivado</option></ResponsiveSelect></label>
            <label className="admin-form-wide"><span>Enunciado</span><input value={formEjercicio.enunciado} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, enunciado: evento.target.value }))} /></label>
            <label><span>Respuesta correcta</span><input value={formEjercicio.respuesta_correcta} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, respuesta_correcta: evento.target.value }))} /></label>
            <label><span>Opciones separadas por coma</span><input value={formEjercicio.opciones} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, opciones: evento.target.value }))} /></label>
            <label className="admin-form-wide"><span>Explicación</span><input value={formEjercicio.explicacion} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, explicacion: evento.target.value }))} /></label>
            <label className="admin-form-wide"><span>Pista</span><input value={formEjercicio.pista} onChange={(evento) => setFormEjercicio((actual) => ({ ...actual, pista: evento.target.value }))} /></label>
            <div className="form-actions admin-form-wide">
              <button type="submit">{formEjercicio.id_ejercicio ? "Actualizar" : "Crear"}</button>
              <button type="button" className="secondary" onClick={() => setFormEjercicio(ejercicioInicial)}>Limpiar</button>
            </div>
          </form>
          <form className="admin-filter-form" onSubmit={aplicarFiltroEjercicios}>
            <ResponsiveSelect value={filtroEjercicio.id_tema} onChange={(evento) => setFiltroEjercicio((actual) => ({ ...actual, id_tema: evento.target.value }))}><option value="">Todos los temas</option>{temasOrdenados.map((tema) => <option key={tema.id_tema} value={tema.id_tema}>{tema.nombre_grado} - {formatLabel(tema.nombre_tema)}</option>)}</ResponsiveSelect>
            <ResponsiveSelect value={filtroEjercicio.id_nivel} onChange={(evento) => setFiltroEjercicio((actual) => ({ ...actual, id_nivel: evento.target.value }))}><option value="">Todos los niveles</option>{niveles.map((nivel) => <option key={nivel.id_nivel} value={nivel.id_nivel}>{nivel.nombre}</option>)}</ResponsiveSelect>
            <ResponsiveSelect value={filtroEjercicio.estado} onChange={(evento) => setFiltroEjercicio((actual) => ({ ...actual, estado: evento.target.value }))}><option value="">Todos los estados</option><option value="borrador">Borrador</option><option value="publicado">Publicado</option><option value="desactivado">Desactivado</option></ResponsiveSelect>
            <button type="submit">Filtrar</button>
          </form>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Tema</th><th>Nivel</th><th>Enunciado</th><th>Respuesta</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody>{ejercicios.map((ejercicio) => <tr key={ejercicio.id_ejercicio}><td>{formatLabel(ejercicio.nombre_tema)}</td><td>{ejercicio.nombre_nivel}</td><td>{ejercicio.enunciado}</td><td>{ejercicio.respuesta_correcta}</td><td>{formatLabel(ejercicio.estado)}</td><td className="actions"><button type="button" className="secondary" onClick={() => editarEjercicio(ejercicio)}>Editar</button><button type="button" className="secondary" onClick={() => alternarEjercicio(ejercicio)}>{ejercicio.estado === "publicado" ? "Desactivar" : "Publicar"}</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
      )}

      {tabActiva === "reglas" && (
        <section className="panel">
          <h2>Reglas adaptativas</h2>
          <form className="admin-form" onSubmit={guardarRegla}>
            <label><span>Nombre</span><input value={formRegla.nombre} onChange={(evento) => setFormRegla((actual) => ({ ...actual, nombre: evento.target.value }))} /></label>
            <label><span>Prioridad</span><input type="number" value={formRegla.prioridad} onChange={(evento) => setFormRegla((actual) => ({ ...actual, prioridad: evento.target.value }))} /></label>
            <label><span>Acción</span><ResponsiveSelect value={formRegla.accion} onChange={(evento) => setFormRegla((actual) => ({ ...actual, accion: evento.target.value }))}><option value="mantener">Mantener</option><option value="aumentar">Aumentar</option><option value="reducir">Reducir</option><option value="reforzar">Reforzar</option></ResponsiveSelect></label>
            <label><span>Estado</span><ResponsiveSelect value={formRegla.estado} onChange={(evento) => setFormRegla((actual) => ({ ...actual, estado: evento.target.value }))}><option value="activo">Activo</option><option value="inactivo">Inactivo</option></ResponsiveSelect></label>
            <label className="admin-form-wide"><span>Descripción</span><input value={formRegla.descripcion} onChange={(evento) => setFormRegla((actual) => ({ ...actual, descripcion: evento.target.value }))} /></label>
            <label className="admin-form-wide"><span>Parametros JSON</span><textarea rows={6} value={formRegla.parametros_json} onChange={(evento) => setFormRegla((actual) => ({ ...actual, parametros_json: evento.target.value }))} /></label>
            <div className="form-actions admin-form-wide">
              <button type="submit">Actualizar regla</button>
              <button type="button" className="secondary" onClick={() => setFormRegla(reglaInicial)}>Limpiar</button>
            </div>
          </form>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Código</th><th>Nombre</th><th>Prioridad</th><th>Acción</th><th>Estado</th><th>Decisiones</th><th>Acciones</th></tr></thead>
              <tbody>{reglas.map((regla) => <tr key={regla.id_regla}><td>{formatLabel(regla.codigo_regla)}</td><td>{regla.nombre}</td><td>{regla.prioridad}</td><td>{formatLabel(regla.accion)}</td><td>{formatLabel(regla.estado)}</td><td>{regla.total_decisiones}</td><td className="actions"><button type="button" className="secondary" onClick={() => editarRegla(regla)}>Editar</button><button type="button" className="secondary" onClick={() => alternarRegla(regla)}>{regla.estado === "activo" ? "Desactivar" : "Activar"}</button></td></tr>)}</tbody>
            </table>
          </div>
        </section>
      )}

      {tabActiva === "auditoria" && (
        <section className="panel">
          <h2>Auditoría</h2>
          <form className="admin-filter-form" onSubmit={aplicarFiltroAuditoria}>
            <input
              value={filtroAuditoria.accion}
              onChange={(evento) => setFiltroAuditoria((actual) => ({ ...actual, accion: evento.target.value }))}
              placeholder="Accion exacta"
            />
            <input
              value={filtroAuditoria.entidad}
              onChange={(evento) => setFiltroAuditoria((actual) => ({ ...actual, entidad: evento.target.value }))}
              placeholder="Entidad exacta"
            />
            <ResponsiveSelect value={filtroAuditoria.resultado} onChange={(evento) => setFiltroAuditoria((actual) => ({ ...actual, resultado: evento.target.value }))}>
              <option value="">Todos los resultados</option>
              <option value="exitoso">Exitoso</option>
              <option value="fallido">Fallido</option>
            </ResponsiveSelect>
            <ResponsiveSelect value={filtroAuditoria.limite} onChange={(evento) => setFiltroAuditoria((actual) => ({ ...actual, limite: Number(evento.target.value) }))}>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={300}>300</option>
            </ResponsiveSelect>
            <button type="submit">Filtrar</button>
          </form>
          {auditoria.length === 0 ? (
            <PixelEmptyState title="No hay eventos de auditoría." description="Las acciones sensibles aparecerán aquí al usarse el sistema." />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Usuario</th>
                    <th>Acción</th>
                    <th>Entidad</th>
                    <th>Metodo</th>
                    <th>Ruta</th>
                    <th>Estado</th>
                    <th>Resultado</th>
                  </tr>
                </thead>
                <tbody>
                  {auditoria.map((evento) => (
                    <tr key={evento.id_bitacora}>
                      <td>{formatDateTime(evento.fecha_creacion)}</td>
                      <td>{evento.usuario}</td>
                      <td>{formatLabel(evento.accion)}</td>
                      <td>{evento.entidad}</td>
                      <td>{evento.metodo}</td>
                      <td>{evento.ruta}</td>
                      <td>{evento.codigo_estado}</td>
                      <td>{formatLabel(evento.resultado)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tabActiva === "reportes" && (
        <section className="panel">
          <h2>Reportes institucionales</h2>
          <form className="admin-filter-form report-filter-form" onSubmit={aplicarFiltroReporte}>
            <label>
              <span>Modalidad</span>
              <ResponsiveSelect name="modalidad" value={filtroReporte.modalidad} onChange={cambiarFiltroReporte}>
                <option value="">Todas</option>
                <option value="institucional">Institucional</option>
                <option value="independiente">Independiente</option>
              </ResponsiveSelect>
            </label>
            <label>
              <span>Institución</span>
              <ResponsiveSelect name="id_institucion" value={filtroReporte.id_institucion} onChange={cambiarFiltroReporte} disabled={filtroReporte.modalidad === "independiente"}>
                <option value="">Todas</option>
                {catalogosReporte.instituciones.map((institucion) => (
                  <option key={institucion.id_institucion} value={institucion.id_institucion}>{institucion.nombre}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Grado base</span>
              <ResponsiveSelect name="id_grado_base" value={filtroReporte.id_grado_base} onChange={cambiarFiltroReporte}>
                <option value="">Todos</option>
                {catalogosReporte.grados_base.map((grado) => (
                  <option key={grado.id_grado_base} value={grado.id_grado_base}>{grado.nombre_grado}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Grado institucional</span>
              <ResponsiveSelect name="id_institucion_grado" value={filtroReporte.id_institucion_grado} onChange={cambiarFiltroReporte} disabled={filtroReporte.modalidad === "independiente"}>
                <option value="">Todos</option>
                {catalogosReporte.grados_institucionales.map((grado) => (
                  <option key={grado.id_institucion_grado} value={grado.id_institucion_grado}>
                    {grado.institucion} - {grado.nombre_grado}
                  </option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Sección</span>
              <ResponsiveSelect name="id_seccion" value={filtroReporte.id_seccion} onChange={cambiarFiltroReporte} disabled={filtroReporte.modalidad === "independiente"}>
                <option value="">Todas</option>
                {catalogosReporte.secciones.map((seccion) => (
                  <option key={seccion.id_seccion} value={seccion.id_seccion}>{seccion.nombre_seccion}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Docente</span>
              <ResponsiveSelect name="id_docente" value={filtroReporte.id_docente} onChange={cambiarFiltroReporte} disabled={filtroReporte.modalidad === "independiente"}>
                <option value="">Todos</option>
                {catalogosReporte.docentes.map((docente) => (
                  <option key={docente.id_docente} value={docente.id_docente}>{docente.docente}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Estudiante</span>
              <ResponsiveSelect name="id_estudiante" value={filtroReporte.id_estudiante} onChange={cambiarFiltroReporte}>
                <option value="">Todos</option>
                {catalogosReporte.estudiantes.map((estudiante) => (
                  <option key={estudiante.id_estudiante} value={estudiante.id_estudiante}>{estudiante.estudiante}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Tema</span>
              <ResponsiveSelect name="id_tema" value={filtroReporte.id_tema} onChange={cambiarFiltroReporte}>
                <option value="">Todos</option>
                {catalogosReporte.temas.map((tema) => (
                  <option key={tema.id_tema} value={tema.id_tema}>{formatLabel(tema.nombre_tema)}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label>
              <span>Asignación</span>
              <ResponsiveSelect name="id_asignacion" value={filtroReporte.id_asignacion} onChange={cambiarFiltroReporte} disabled={filtroReporte.modalidad === "independiente"}>
                <option value="">Todas</option>
                {catalogosReporte.asignaciones.map((asignacion) => (
                  <option key={asignacion.id_asignacion} value={asignacion.id_asignacion}>{asignacion.nombre}</option>
                ))}
              </ResponsiveSelect>
            </label>
            <label><span>Desde</span><input name="fecha_inicio" type="datetime-local" value={filtroReporte.fecha_inicio} onChange={cambiarFiltroReporte} /></label>
            <label><span>Hasta</span><input name="fecha_fin" type="datetime-local" value={filtroReporte.fecha_fin} onChange={cambiarFiltroReporte} /></label>
            <button type="submit">Aplicar</button>
          </form>
          <ReportExportButtons cargando={exportando} onExportar={exportarReporteInstitucional} />

          {reporteAdmin?.resumen && (
            <div className="admin-role-grid">
              <article className="student-stat-card"><span>Estudiantes</span><strong>{reporteAdmin.resumen.estudiantes}</strong></article>
              <article className="student-stat-card"><span>Intentos</span><strong>{reporteAdmin.resumen.intentos}</strong></article>
              <article className="student-stat-card"><span>Precision</span><strong>{formatearPorcentaje(reporteAdmin.resumen.precision_promedio)}</strong></article>
              <article className="student-stat-card"><span>Partidas</span><strong>{reporteAdmin.resumen.partidas}</strong></article>
              <article className="student-stat-card"><span>Actividad</span><strong>{reporteAdmin.resumen.actividad_periodo || "Sin datos"}</strong></article>
            </div>
          )}

          {reporteAdmin?.filas?.length ? (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Estudiante</th>
                    <th>Modalidad</th>
                    <th>Institución</th>
                    <th>Docente</th>
                    <th>Grado</th>
                    <th>Sección</th>
                    <th>Asignación</th>
                    <th>Tema</th>
                    <th>Intentos</th>
                    <th>Correctos</th>
                    <th>Incorrectos</th>
                    <th>Precision</th>
                    <th>Partidas</th>
                    <th>Nivel</th>
                    <th>Última actividad</th>
                    <th>Última decisión</th>
                  </tr>
                </thead>
                <tbody>
                  {reporteAdmin.filas.map((fila, indice) => (
                    <tr key={`${fila.id_estudiante}-${fila.id_asignacion || "libre"}-${fila.id_tema || indice}`}>
                      <td>{fila.estudiante}</td>
                      <td>{formatLabel(fila.modalidad)}</td>
                      <td>{fila.institucion || "No aplica"}</td>
                      <td>{fila.docente || "No aplica"}</td>
                      <td>{fila.grado || "Sin grado"}</td>
                      <td>{fila.seccion || "No aplica"}</td>
                      <td>{fila.asignacion || "Practica libre"}</td>
                      <td>{fila.tema ? formatLabel(fila.tema) : "Sin tema"}</td>
                      <td>{fila.intentos}</td>
                      <td>{fila.correctos}</td>
                      <td>{fila.incorrectos}</td>
                      <td>{formatearPorcentaje(fila.precision)}</td>
                      <td>{fila.partidas_completadas}</td>
                      <td>{fila.nivel_actual || "Sin nivel"}</td>
                      <td>{formatDateTime(fila.ultima_actividad)}</td>
                      <td>{formatDateTime(fila.ultima_decision, "Sin decisión")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <PixelEmptyState title="No hay datos de reporte." description="Ajuste filtros o registre actividad academica." />
          )}
        </section>
      )}
    </section>
  );
};

export default AdminPage;
