import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import { obtenerGrados } from "../services/gradosService";
import { obtenerTemasPorGrado } from "../services/temasService";
import {
  actualizarPlantilla,
  cambiarEstadoPlantilla,
  crearPlantilla,
  obtenerNivelesPlantillas,
  obtenerPlantillas,
  probarPlantilla,
} from "../services/plantillasService";
import { formatLabel } from "../constants/uiLabels";

const estadoInicial = {
  id_plantilla: null,
  id_grado: "",
  id_tema: "",
  id_nivel: "",
  nombre: "",
  descripcion: "",
  tipo_respuesta: "seleccion_multiple",
  plantilla_enunciado: "¿Cuánto es {a} x {b}?",
  configuracion_json: '{\n  "operacion": "multiplicacion",\n  "variables": {\n    "a": { "tipo": "entero", "min": 2, "max": 9 },\n    "b": { "tipo": "entero", "min": 2, "max": 9 }\n  }\n}',
  plantilla_explicacion: "{a} x {b} = {respuesta}.",
  plantilla_pista: "Calcula paso a paso.",
  estado: "borrador",
};

// Pantalla administrativa basica para revisar plantillas y probar generaciones.
const PlantillasPage = () => {
  const [plantillas, setPlantillas] = useState([]);
  const [ejemplos, setEjemplos] = useState([]);
  const [grados, setGrados] = useState([]);
  const [temas, setTemas] = useState([]);
  const [temasFiltro, setTemasFiltro] = useState([]);
  const [niveles, setNiveles] = useState([]);
  const [formulario, setFormulario] = useState(estadoInicial);
  const [filtros, setFiltros] = useState({ grado: "", tema: "", estado: "" });
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarPlantillas();
    cargarCatalogos();
  }, []);

  useEffect(() => {
    if (!formulario.id_grado) {
      setTemas([]);
      return;
    }
    cargarTemas(formulario.id_grado);
  }, [formulario.id_grado]);

  useEffect(() => {
    if (!filtros.grado) {
      setTemasFiltro([]);
      setFiltros((actual) => ({ ...actual, tema: "" }));
      return;
    }
    cargarTemasFiltro(filtros.grado);
  }, [filtros.grado]);

  // Carga las plantillas disponibles desde Flask.
  const cargarPlantillas = async () => {
    try {
      setCargando(true);
      const respuesta = await obtenerPlantillas(filtros);
      setPlantillas(respuesta.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  // Carga grados y niveles usados por el formulario.
  const cargarCatalogos = async () => {
    try {
      const [respuestaGrados, respuestaNiveles] = await Promise.all([
        obtenerGrados({ estado: "activo" }),
        obtenerNivelesPlantillas(),
      ]);
      setGrados(respuestaGrados.data || []);
      setNiveles(respuestaNiveles.data || []);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Carga temas activos del grado elegido.
  const cargarTemas = async (idGrado) => {
    try {
      const respuesta = await obtenerTemasPorGrado(idGrado);
      setTemas(respuesta.data || []);
    } catch (error) {
      setTemas([]);
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Carga temas usados por los filtros sin alterar el formulario de edicion.
  const cargarTemasFiltro = async (idGrado) => {
    try {
      const respuesta = await obtenerTemasPorGrado(idGrado);
      setTemasFiltro(respuesta.data || []);
    } catch (error) {
      setTemasFiltro([]);
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Aplica filtros administrativos de plantillas.
  const aplicarFiltros = async (evento) => {
    evento.preventDefault();
    await cargarPlantillas();
  };

  // Actualiza un campo del formulario.
  const cambiarCampo = (evento) => {
    const { name, value } = evento.target;
    setFormulario((actual) => ({
      ...actual,
      [name]: value,
      ...(name === "id_grado" ? { id_tema: "" } : {}),
    }));
  };

  // Guarda una plantilla nueva o actualiza la seleccionada.
  const guardar = async (evento) => {
    evento.preventDefault();
    try {
      const payload = {
        ...formulario,
        id_grado: Number(formulario.id_grado),
        id_tema: Number(formulario.id_tema),
        id_nivel: Number(formulario.id_nivel),
      };
      const respuesta = formulario.id_plantilla
        ? await actualizarPlantilla(formulario.id_plantilla, payload)
        : await crearPlantilla(payload);
      setMensaje({ tipo: "success", texto: respuesta.message });
      setFormulario(estadoInicial);
      cargarPlantillas();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Carga una plantilla existente en el formulario.
  const editar = (plantilla) => {
    setFormulario({
      id_plantilla: plantilla.id_plantilla,
      id_grado: String(plantilla.id_grado),
      id_tema: String(plantilla.id_tema),
      id_nivel: String(plantilla.id_nivel),
      nombre: plantilla.nombre,
      descripcion: plantilla.descripcion || "",
      tipo_respuesta: plantilla.tipo_respuesta,
      plantilla_enunciado: plantilla.plantilla_enunciado,
      configuracion_json: JSON.stringify(plantilla.configuracion_json, null, 2),
      plantilla_explicacion: plantilla.plantilla_explicacion || "",
      plantilla_pista: plantilla.plantilla_pista || "",
      estado: plantilla.estado,
    });
  };

  // Publica o desactiva rapidamente una plantilla.
  const alternarEstado = async (plantilla) => {
    try {
      const nuevoEstado = plantilla.estado === "publicada" ? "desactivada" : "publicada";
      const respuesta = await cambiarEstadoPlantilla(plantilla.id_plantilla, nuevoEstado);
      setMensaje({ tipo: "success", texto: respuesta.message });
      cargarPlantillas();
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  // Solicita al backend ejemplos temporales de una plantilla.
  const probar = async (plantilla) => {
    try {
      const respuesta = await probarPlantilla(plantilla.id_plantilla, 3);
      setEjemplos(respuesta.data || []);
      setMensaje({ tipo: "success", texto: `Ejemplos de ${plantilla.nombre}.` });
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    }
  };

  return (
    <section className="content">
      <div className="header-row">
        <div>
          <h1>Plantillas de ejercicios</h1>
          <p>Generación procedimental para el agente adaptativo.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="panel">
        <h2>Filtros</h2>
        <form className="admin-filter-form" onSubmit={aplicarFiltros}>
          <select value={filtros.grado} onChange={(evento) => setFiltros((actual) => ({ ...actual, grado: evento.target.value, tema: "" }))}>
            <option value="">Todos los grados</option>
            {grados.map((grado) => (
              <option key={grado.id_grado} value={grado.id_grado}>{grado.nombre_grado}</option>
            ))}
          </select>
          <select value={filtros.tema} onChange={(evento) => setFiltros((actual) => ({ ...actual, tema: evento.target.value }))} disabled={!filtros.grado}>
            <option value="">Todos los temas</option>
            {temasFiltro.map((tema) => (
              <option key={tema.id_tema} value={tema.id_tema}>{formatLabel(tema.nombre_tema)}</option>
            ))}
          </select>
          <select value={filtros.estado} onChange={(evento) => setFiltros((actual) => ({ ...actual, estado: evento.target.value }))}>
            <option value="">Todos los estados</option>
            <option value="borrador">Borrador</option>
            <option value="publicada">Publicada</option>
            <option value="desactivada">Desactivada</option>
          </select>
          <button type="submit">Filtrar</button>
        </form>
      </section>

      <section className="panel">
        <h2>{formulario.id_plantilla ? "Editar plantilla" : "Nueva plantilla"}</h2>
        <form className="template-form" onSubmit={guardar}>
          <label>
            <span>Grado</span>
            <select name="id_grado" value={formulario.id_grado} onChange={cambiarCampo}>
              <option value="">Seleccione</option>
              {grados.map((grado) => (
                <option key={grado.id_grado} value={grado.id_grado}>{grado.nombre_grado}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Tema</span>
            <select name="id_tema" value={formulario.id_tema} onChange={cambiarCampo}>
              <option value="">Seleccione</option>
              {temas.map((tema) => (
                <option key={tema.id_tema} value={tema.id_tema}>{formatLabel(tema.nombre_tema)}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Nivel</span>
            <select name="id_nivel" value={formulario.id_nivel} onChange={cambiarCampo}>
              <option value="">Seleccione</option>
              {niveles.map((nivel) => (
                <option key={nivel.id_nivel} value={nivel.id_nivel}>{nivel.nombre}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Nombre</span>
            <input name="nombre" value={formulario.nombre} onChange={cambiarCampo} />
          </label>
          <label>
            <span>Tipo</span>
            <select name="tipo_respuesta" value={formulario.tipo_respuesta} onChange={cambiarCampo}>
              <option value="seleccion_multiple">Selección múltiple</option>
              <option value="numerica">Numérica</option>
            </select>
          </label>
          <label>
            <span>Estado</span>
            <select name="estado" value={formulario.estado} onChange={cambiarCampo}>
              <option value="borrador">Borrador</option>
              <option value="publicada">Publicada</option>
              <option value="desactivada">Desactivada</option>
            </select>
          </label>
          <label className="template-form-wide">
            <span>Enunciado</span>
            <input name="plantilla_enunciado" value={formulario.plantilla_enunciado} onChange={cambiarCampo} />
          </label>
          <label className="template-form-wide">
            <span>Configuración JSON</span>
            <textarea name="configuracion_json" value={formulario.configuracion_json} onChange={cambiarCampo} rows={8} />
          </label>
          <label className="template-form-wide">
            <span>Explicación</span>
            <input name="plantilla_explicacion" value={formulario.plantilla_explicacion} onChange={cambiarCampo} />
          </label>
          <label className="template-form-wide">
            <span>Pista</span>
            <input name="plantilla_pista" value={formulario.plantilla_pista} onChange={cambiarCampo} />
          </label>
          <div className="form-actions template-form-wide">
            <button type="submit">{formulario.id_plantilla ? "Actualizar" : "Crear"}</button>
            <button type="button" className="secondary" onClick={() => setFormulario(estadoInicial)}>
              Limpiar
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        {cargando ? (
          <p>Cargando plantillas...</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Grado</th>
                  <th>Tema</th>
                  <th>Nivel</th>
                  <th>Nombre</th>
                  <th>Tipo</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {plantillas.map((plantilla) => (
                  <tr key={plantilla.id_plantilla}>
                    <td>{plantilla.nombre_grado}</td>
                    <td>{formatLabel(plantilla.nombre_tema)}</td>
                    <td>{plantilla.nombre_nivel}</td>
                    <td>{plantilla.nombre}</td>
                    <td>{formatLabel(plantilla.tipo_respuesta)}</td>
                    <td>
                      <button type="button" onClick={() => probar(plantilla)}>
                        Probar generación
                      </button>
                      <button type="button" className="secondary" onClick={() => editar(plantilla)}>
                        Editar
                      </button>
                      <button type="button" className="secondary" onClick={() => alternarEstado(plantilla)}>
                        {plantilla.estado === "publicada" ? "Desactivar" : "Publicar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {ejemplos.length > 0 && (
        <section className="panel">
          <h2>Ejemplos generados</h2>
          <div className="generated-examples">
            {ejemplos.map((ejemplo, index) => (
              <article key={`${ejemplo.enunciado}-${index}`} className="generated-example">
                <strong>Ejemplo {index + 1}</strong>
                <p>{ejemplo.enunciado}</p>
                <span>Respuesta: {ejemplo.respuesta_correcta}</span>
              </article>
            ))}
          </div>
        </section>
      )}
    </section>
  );
};

export default PlantillasPage;
