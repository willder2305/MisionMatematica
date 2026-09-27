import React, { useEffect, useMemo, useState } from "react";
import ResponsiveSelect from "../components/ui/ResponsiveSelect";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import {
  actualizarAsignacion,
  cambiarEstadoAsignacion,
  crearAsignacion,
  obtenerAsignaciones,
  obtenerContextoAsignaciones,
} from "../services/asignacionesService";
import { obtenerNivelesPlantillas } from "../services/plantillasService";
import { obtenerTemasPorGrado } from "../services/temasService";
import { formatDateTime, formatLabel } from "../constants/uiLabels";

const ahoraLocal = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);

const formularioInicial = {
  id_institucion_grado: "",
  id_seccion: "",
  nombre: "",
  instrucciones: "",
  tipo: "generacion_automatica",
  id_nivel_inicial: "",
  fecha_inicio: ahoraLocal(),
  fecha_limite: "",
  obligatoria: true,
  estado: "activa",
  temas: [],
  ejercicios: "",
};

const AsignacionesPage = () => {
  const [asignaciones, setAsignaciones] = useState([]);
  const [gradosContexto, setGradosContexto] = useState([]);
  const [temas, setTemas] = useState([]);
  const [niveles, setNiveles] = useState([]);
  const [formulario, setFormulario] = useState(formularioInicial);
  const [editando, setEditando] = useState(null);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);

  const gradoSeleccionado = useMemo(
    () => gradosContexto.find((grado) => String(grado.id_institucion_grado) === String(formulario.id_institucion_grado)),
    [gradosContexto, formulario.id_institucion_grado]
  );

  const seccionesDisponibles = gradoSeleccionado?.secciones || [];

  useEffect(() => {
    cargarBase();
  }, []);

  useEffect(() => {
    if (!gradoSeleccionado) {
      setTemas([]);
      return;
    }
    cargarTemasGrado(gradoSeleccionado.id_grado_base);
  }, [gradoSeleccionado?.id_grado_base]);

  const cargarBase = async () => {
    // Carga asignaciones, contexto institucional y niveles para el formulario docente.
    try {
      setCargando(true);
      const [resAsignaciones, resContexto, resNiveles] = await Promise.all([
        obtenerAsignaciones(),
        obtenerContextoAsignaciones(),
        obtenerNivelesPlantillas(),
      ]);
      setAsignaciones(resAsignaciones.data || []);
      setGradosContexto(resContexto.data || []);
      setNiveles(resNiveles.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const cargarTemasGrado = async (idGradoBase) => {
    // Carga temas heredados desde el grado base del grado institucional.
    try {
      const respuesta = await obtenerTemasPorGrado(idGradoBase);
      setTemas(respuesta.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  const cambiarCampo = (evento) => {
    // Sincroniza campos simples y limpia dependencias al cambiar grado.
    const { name, value, type, checked } = evento.target;
    setFormulario((actual) => ({
      ...actual,
      [name]: type === "checkbox" ? checked : value,
      ...(name === "id_institucion_grado" ? { id_seccion: "", temas: [] } : {}),
    }));
  };

  const alternarTema = (idTema) => {
    // Agrega o quita temas de la asignacion.
    setFormulario((actual) => ({
      ...actual,
      temas: actual.temas.includes(idTema)
        ? actual.temas.filter((id) => id !== idTema)
        : [...actual.temas, idTema],
    }));
  };

  const prepararPayload = () => ({
    ...formulario,
    id_institucion_grado: Number(formulario.id_institucion_grado),
    id_seccion: Number(formulario.id_seccion),
    id_nivel_inicial: Number(formulario.id_nivel_inicial),
    cantidad_preguntas: 10,
    fecha_limite: formulario.fecha_limite || null,
    ejercicios: formulario.ejercicios,
  });

  const guardar = async (evento) => {
    // Crea o actualiza la asignacion con validacion final en backend.
    evento.preventDefault();
    setGuardando(true);
    setMensaje({ tipo: "", texto: "" });
    try {
      const respuesta = editando
        ? await actualizarAsignacion(editando.id_asignacion, prepararPayload())
        : await crearAsignacion(prepararPayload());
      setMensaje({ tipo: "success", texto: respuesta.message });
      setFormulario(formularioInicial);
      setEditando(null);
      await cargarBase();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setGuardando(false);
    }
  };

  const editar = (asignacion) => {
    // Carga una asignacion existente al formulario.
    setEditando(asignacion);
    setFormulario({
      id_institucion_grado: String(asignacion.id_institucion_grado),
      id_seccion: asignacion.id_seccion ? String(asignacion.id_seccion) : "",
      nombre: asignacion.nombre,
      instrucciones: asignacion.instrucciones || "",
      tipo: asignacion.tipo,
      id_nivel_inicial: String(asignacion.id_nivel_inicial),
      fecha_inicio: (asignacion.fecha_inicio || "").replace(" ", "T").slice(0, 16),
      fecha_limite: asignacion.fecha_limite ? asignacion.fecha_limite.replace(" ", "T").slice(0, 16) : "",
      obligatoria: asignacion.obligatoria,
      estado: asignacion.estado,
      temas: (asignacion.temas || []).map((tema) => tema.id_tema),
      ejercicios: (asignacion.ejercicios || []).map((ejercicio) => ejercicio.id_ejercicio).join(", "),
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const cambiarEstado = async (asignacion, estado) => {
    // Cambia estado sin alterar temas ni ejercicios.
    try {
      const respuesta = await cambiarEstadoAsignacion(asignacion.id_asignacion, estado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      await cargarBase();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  return (
    <section className="content assignments-page">
      <div className="header-row">
        <div>
          <h1>Asignaciones</h1>
          <p>Actividades por grado, sección, tema y nivel.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="panel">
        <h2>{editando ? "Editar asignación" : "Nueva asignación"}</h2>
        <form className="template-form" onSubmit={guardar}>
          <label>
            <span>Grado</span>
            <ResponsiveSelect name="id_institucion_grado" value={formulario.id_institucion_grado} onChange={cambiarCampo} required disabled={Boolean(editando)}>
              <option value="">Seleccione</option>
              {gradosContexto.map((grado) => (
                <option key={grado.id_institucion_grado} value={grado.id_institucion_grado}>
                  {grado.nombre_grado}
                </option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Sección</span>
            <ResponsiveSelect name="id_seccion" value={formulario.id_seccion} onChange={cambiarCampo} required disabled={!formulario.id_institucion_grado || Boolean(editando)}>
              <option value="">Seleccione</option>
              {seccionesDisponibles.map((seccion) => (
                <option key={seccion.id_seccion} value={seccion.id_seccion}>{seccion.nombre_seccion}</option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Nivel inicial</span>
            <ResponsiveSelect name="id_nivel_inicial" value={formulario.id_nivel_inicial} onChange={cambiarCampo} required>
              <option value="">Seleccione</option>
              {niveles.map((nivel) => (
                <option key={nivel.id_nivel} value={nivel.id_nivel}>{nivel.nombre}</option>
              ))}
            </ResponsiveSelect>
          </label>
          <label>
            <span>Nombre</span>
            <input name="nombre" value={formulario.nombre} onChange={cambiarCampo} required maxLength={120} />
          </label>
          <label>
            <span>Tipo</span>
            <ResponsiveSelect name="tipo" value={formulario.tipo} onChange={cambiarCampo}>
              <option value="generacion_automatica">Generación automática</option>
              <option value="ejercicios_especificos">Ejercicios específicos</option>
            </ResponsiveSelect>
          </label>
          <label>
            <span>Fecha inicio</span>
            <input name="fecha_inicio" type="datetime-local" value={formulario.fecha_inicio} onChange={cambiarCampo} required />
          </label>
          <label>
            <span>Fecha límite</span>
            <input name="fecha_limite" type="datetime-local" value={formulario.fecha_limite} onChange={cambiarCampo} />
          </label>
          <label>
            <span>Estado</span>
            <ResponsiveSelect name="estado" value={formulario.estado} onChange={cambiarCampo}>
              <option value="borrador">Borrador</option>
              <option value="activa">Activa</option>
              <option value="pausada">Pausada</option>
              <option value="finalizada">Finalizada</option>
              <option value="cancelada">Cancelada</option>
            </ResponsiveSelect>
          </label>
          <label className="template-form-wide">
            <span>Instrucciones</span>
            <textarea name="instrucciones" value={formulario.instrucciones} onChange={cambiarCampo} rows={3} maxLength={500} />
          </label>
          <div className="template-form-wide assignment-topic-list">
            <strong>Temas</strong>
            {temas.map((tema) => (
              <label key={tema.id_tema} className="check-row">
                <input
                  type="checkbox"
                  checked={formulario.temas.includes(tema.id_tema)}
                  onChange={() => alternarTema(tema.id_tema)}
                />
                <span>{formatLabel(tema.nombre_tema)}</span>
              </label>
            ))}
            {temas.length === 0 && <p>Seleccione un grado para cargar temas.</p>}
          </div>
          {formulario.tipo === "ejercicios_especificos" && (
            <label className="template-form-wide">
            <span>Ejercicios publicados</span>
              <input name="ejercicios" value={formulario.ejercicios} onChange={cambiarCampo} placeholder="1, 2, 3" />
            </label>
          )}
          <label className="check-row template-form-wide">
            <input name="obligatoria" type="checkbox" checked={formulario.obligatoria} onChange={cambiarCampo} />
            <span>Actividad obligatoria</span>
          </label>
          <div className="form-actions template-form-wide">
            <button type="submit" disabled={guardando}>{guardando ? "Guardando..." : editando ? "Actualizar" : "Crear"}</button>
            {editando && (
              <button type="button" className="secondary" onClick={() => { setEditando(null); setFormulario(formularioInicial); }}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </section>

      {cargando ? (
        <PixelLoader text="Cargando asignaciones..." />
      ) : (
        <section className="table-section">
          <h2>Asignaciones registradas</h2>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Grado</th>
                    <th>Sección</th>
                  <th>Tipo</th>
                  <th>Temas</th>
                  <th>Inicio</th>
                    <th>Límite</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {asignaciones.map((asignacion) => (
                  <tr key={asignacion.id_asignacion}>
                    <td>{asignacion.nombre}</td>
                    <td>{asignacion.grado || "Sin grado"}</td>
                    <td>{asignacion.seccion || "Sin sección"}</td>
                    <td>{formatLabel(asignacion.tipo)}</td>
                    <td>{asignacion.temas.map((tema) => formatLabel(tema.nombre_tema)).join(", ")}</td>
                    <td>{formatDateTime(asignacion.fecha_inicio)}</td>
                    <td>{formatDateTime(asignacion.fecha_limite, "Sin límite")}</td>
                    <td>{formatLabel(asignacion.estado)}</td>
                    <td className="actions">
                      <button type="button" className="secondary edit" onClick={() => editar(asignacion)}>Editar</button>
                      <button type="button" className="secondary state" onClick={() => cambiarEstado(asignacion, asignacion.estado === "activa" ? "pausada" : "activa")}>
                        {asignacion.estado === "activa" ? "Pausar" : "Activar"}
                      </button>
                      <button type="button" className="danger" onClick={() => cambiarEstado(asignacion, "cancelada")}>Cancelar</button>
                    </td>
                  </tr>
                ))}
                {asignaciones.length === 0 && (
                  <tr>
                    <td colSpan="9">No existen asignaciones registradas.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </section>
  );
};

export default AsignacionesPage;
