import React, { useEffect, useRef, useState } from "react";
import logoMision from "../assets/pixel/logo_mision_matematica_pixel.png";
import { obtenerPersonajeConfig } from "../config/personajesConfig";
import { guardarSesion, obtenerAccessToken, obtenerRefreshToken, obtenerUsuarioLocal } from "../services/authService";
import { obtenerOpcionesGrados } from "../services/gradosService";
import { ingresarConPin } from "../services/gruposService";
import {
  buscarInstituciones,
  crearOReutilizarInstitucion,
  obtenerSeccionesDisponiblesInstitucion,
} from "../services/institucionesService";
import { navegarInternamente } from "../services/navigationService";
import { completarOnboarding, obtenerPersonajesIniciales } from "../services/onboardingService";

const SECCIONES_CONFIGURABLES = ["A", "B", "C", "D"];

const OnboardingPage = () => {
  const usuario = obtenerUsuarioLocal();
  const [grados, setGrados] = useState([]);
  const [personajesIniciales, setPersonajesIniciales] = useState([]);
  const [cargandoPersonajes, setCargandoPersonajes] = useState(() => usuario?.rol === "estudiante");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);
  const [buscandoInstituciones, setBuscandoInstituciones] = useState(false);
  const [instituciones, setInstituciones] = useState([]);
  const [disponibilidadSecciones, setDisponibilidadSecciones] = useState({});
  const envioEnCursoRef = useRef(false);
  const [formulario, setFormulario] = useState({
    modalidad: "cuenta_propia",
    id_grado: "",
    personaje: "masculino",
    institucion: "",
    id_institucion: "",
    grados: [],
    secciones_por_grado: {},
    pin: "",
  });

  useEffect(() => {
    // Carga grados activos para estudiante o docente.
    obtenerOpcionesGrados()
      .then((respuesta) => setGrados(respuesta.data || []))
      .catch(() => setMensaje("No fue posible cargar los grados."));
  }, []);

  useEffect(() => {
    // El onboarding recibe exclusivamente starters desde el backend, nunca el catálogo de tienda.
    if (usuario?.rol !== "estudiante") return undefined;
    let activo = true;
    obtenerPersonajesIniciales()
      .then((respuesta) => {
        if (!activo) return;
        const disponibles = respuesta.data?.personajes || [];
        setPersonajesIniciales(disponibles);
        setFormulario((actual) => (
          disponibles.some((personaje) => personaje.personaje === actual.personaje)
            ? actual
            : { ...actual, personaje: disponibles[0]?.personaje || "" }
        ));
      })
      .catch((error) => activo && setMensaje(error.response?.data?.message || "No fue posible cargar los personajes."))
      .finally(() => activo && setCargandoPersonajes(false));
    return () => { activo = false; };
  }, [usuario?.rol]);

  if (!usuario) {
    navegarInternamente("/login", { replace: true });
    return null;
  }

  const cambiarCampo = (evento) => {
    // Sincroniza campos simples del formulario.
    const { name, value } = evento.target;
    setFormulario((actual) => ({
      ...actual,
      [name]: value,
      ...(name === "institucion" ? { id_institucion: "", institucion_seleccionada: "" } : {}),
    }));
  };

  const cargarDisponibilidadSecciones = async (idInstitucion) => {
    // Consulta ocupacion A-D por grado para impedir tomar secciones ya asignadas.
    try {
      const respuesta = await obtenerSeccionesDisponiblesInstitucion(idInstitucion);
      const mapa = {};
      (respuesta.data || []).forEach((grado) => {
        mapa[String(grado.id_grado)] = grado.secciones || [];
      });
      setDisponibilidadSecciones(mapa);
    } catch (error) {
      setDisponibilidadSecciones({});
      setMensaje(error.message);
    }
  };

  const alternarGradoDocente = (idGrado) => {
    // Agrega o quita grados del docente sin duplicados.
    setFormulario((actual) => ({
      ...actual,
      grados: actual.grados.includes(idGrado)
        ? actual.grados.filter((id) => id !== idGrado)
        : [...actual.grados, idGrado],
    }));
  };

  const alternarSeccionDocente = (idGrado, seccion) => {
    // Agrega o quita una seccion A-D para el grado seleccionado.
    const disponibilidad = (disponibilidadSecciones[String(idGrado)] || []).find(
      (item) => item.nombre_seccion === seccion,
    );
    if (disponibilidad && !disponibilidad.disponible) {
      return;
    }
    setFormulario((actual) => {
      const clave = String(idGrado);
      const actuales = actual.secciones_por_grado[clave] || [];
      const siguientes = actuales.includes(seccion)
        ? actuales.filter((valor) => valor !== seccion)
        : [...actuales, seccion];
      return {
        ...actual,
        secciones_por_grado: {
          ...actual.secciones_por_grado,
          [clave]: siguientes,
        },
      };
    });
  };

  const buscarInstitucion = async () => {
    // Consulta coincidencias por nombre normalizado.
    if (buscandoInstituciones || cargando) {
      return;
    }
    setBuscandoInstituciones(true);
    setMensaje("");
    try {
      const respuesta = await buscarInstituciones(formulario.institucion);
      setInstituciones(respuesta.data || []);
    } catch (error) {
      setMensaje(error.message);
      setInstituciones([]);
    } finally {
      setBuscandoInstituciones(false);
    }
  };

  const seleccionarInstitucion = (institucion) => {
    // Fija la institucion elegida desde resultados.
    setFormulario((actual) => ({
      ...actual,
      id_institucion: institucion.id_institucion,
      institucion: institucion.nombre,
      institucion_seleccionada: institucion.nombre,
    }));
    setInstituciones([]);
    cargarDisponibilidadSecciones(institucion.id_institucion);
  };

  const obtenerDisponibilidad = (idGrado, seccion) => (
    (disponibilidadSecciones[String(idGrado)] || []).find((item) => item.nombre_seccion === seccion)
  );

  const crearInstitucion = async () => {
    // Crea o reutiliza una institucion con el nombre escrito.
    if (buscandoInstituciones || cargando) {
      return;
    }
    if (!formulario.institucion.trim()) {
      setMensaje("Ingrese el nombre de la institución.");
      return;
    }
    setBuscandoInstituciones(true);
    setMensaje("");
    try {
      const respuesta = await crearOReutilizarInstitucion(formulario.institucion);
      if (respuesta.data) {
        seleccionarInstitucion(respuesta.data);
      }
    } catch (error) {
      setMensaje(error.message);
    } finally {
      setBuscandoInstituciones(false);
    }
  };

  const enviar = async (evento) => {
    // Guarda onboarding segun rol y actualiza usuario local.
    evento.preventDefault();
    if (envioEnCursoRef.current) {
      return;
    }

    if (usuario.rol === "docente") {
      if (!formulario.id_institucion) {
        setMensaje("Seleccione una institución existente o cree una nueva antes de continuar.");
        return;
      }
      if (!formulario.grados.length) {
        setMensaje("Debes seleccionar al menos un grado.");
        return;
      }
    }
    if (usuario.rol === "estudiante" && !personajesIniciales.some((personaje) => personaje.personaje === formulario.personaje)) {
      setMensaje("Selecciona uno de los personajes disponibles.");
      return;
    }

    envioEnCursoRef.current = true;
    setCargando(true);
    setMensaje("");
    try {
      const payload = usuario.rol === "docente"
        ? {
            id_institucion: Number(formulario.id_institucion),
            grados: formulario.grados,
            secciones_por_grado: formulario.secciones_por_grado,
          }
        : {
            modalidad: formulario.modalidad,
            personaje: formulario.personaje,
          };
      if (usuario.rol === "estudiante" && formulario.modalidad === "grupo_educativo") {
        await ingresarConPin(formulario.pin);
      }
      await completarOnboarding(payload);
      guardarSesion({
        usuario: { ...usuario, onboarding_completado: true },
        access_token: obtenerAccessToken(),
        refresh_token: obtenerRefreshToken(),
      });
      navegarInternamente(usuario.rol === "docente" ? "/mi-institucion" : "/panel-estudiante", { replace: true });
    } catch (error) {
      setMensaje(error.response?.data?.message || "No fue posible completar el onboarding.");
    } finally {
      setCargando(false);
      envioEnCursoRef.current = false;
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card onboarding-card" onSubmit={enviar}>
        <img className="auth-logo pixel-art" src={logoMision} alt="Misión Matemática" decoding="async" />
        <h1>Configurar perfil</h1>
        {mensaje && <div className="auth-error">{mensaje}</div>}

        {usuario.rol === "docente" ? (
          <>
            <label>
              Institución
              <input name="institucion" value={formulario.institucion} onChange={cambiarCampo} />
            </label>
            <div className="institution-actions">
              <button type="button" className="secondary" onClick={buscarInstitucion} disabled={buscandoInstituciones || cargando}>
                {buscandoInstituciones ? "Buscando..." : "Buscar institución"}
              </button>
              <button type="button" className="secondary" onClick={crearInstitucion} disabled={buscandoInstituciones || cargando}>
                Crear institución
              </button>
            </div>
            {formulario.id_institucion && (
              <div className="institution-selected" role="status">
                Institución seleccionada: <strong>{formulario.institucion_seleccionada || formulario.institucion}</strong>
              </div>
            )}
            {instituciones.length > 0 && (
              <div className="institution-results">
                {instituciones.map((institucion) => (
                  <button
                    type="button"
                    key={institucion.id_institucion}
                    onClick={() => seleccionarInstitucion(institucion)}
                  >
                    {institucion.nombre}
                  </button>
                ))}
              </div>
            )}
            <div className="onboarding-group">
              <strong>Grados que atenderás</strong>
              {grados.map((grado) => (
                <div key={grado.id_grado} className="teacher-grade-config">
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={formulario.grados.includes(grado.id_grado)}
                      onChange={() => alternarGradoDocente(grado.id_grado)}
                    />
                    <span>{grado.nombre_grado}</span>
                  </label>
                  {formulario.grados.includes(grado.id_grado) && (
                    <div className="teacher-section-options" aria-label={`Secciones de ${grado.nombre_grado}`}>
                      {SECCIONES_CONFIGURABLES.map((seccion) => (
                        <label
                          key={seccion}
                          className={`check-row compact-check ${
                            obtenerDisponibilidad(grado.id_grado, seccion)?.disponible === false ? "disabled-check" : ""
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={(formulario.secciones_por_grado[String(grado.id_grado)] || []).includes(seccion)}
                            disabled={obtenerDisponibilidad(grado.id_grado, seccion)?.disponible === false}
                            onChange={() => alternarSeccionDocente(grado.id_grado, seccion)}
                          />
                          <span>
                            {seccion}
                            {obtenerDisponibilidad(grado.id_grado, seccion)?.disponible === false
                              ? " - No disponible"
                              : ""}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <label>
              Modalidad
              <select name="modalidad" value={formulario.modalidad} onChange={cambiarCampo}>
                <option value="cuenta_propia">Cuenta propia</option>
                <option value="grupo_educativo">Grupo educativo</option>
              </select>
            </label>
            {formulario.modalidad === "grupo_educativo" && (
              <label>
                PIN de acceso
                <input
                  name="pin"
                  inputMode="numeric"
                  maxLength={6}
                  minLength={6}
                  value={formulario.pin}
                  onChange={cambiarCampo}
                  required
                />
              </label>
            )}
            <div className="onboarding-group">
              <strong>Personaje</strong>
              <div className="character-options compact">
                {personajesIniciales.map((personaje) => {
                  const configuracion = obtenerPersonajeConfig(personaje.personaje);
                  return (
                  <button
                    key={personaje.id_item}
                    type="button"
                    className={`character-option ${formulario.personaje === personaje.personaje ? "selected" : ""}`}
                    onClick={() => setFormulario((actual) => ({ ...actual, personaje: personaje.personaje }))}
                    disabled={cargandoPersonajes}
                  >
                    <img className="pixel-art" src={configuracion.seleccion} alt="" aria-hidden="true" decoding="async" />
                    <span>{personaje.nombre}</span>
                  </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        <button type="submit" disabled={cargando || buscandoInstituciones || cargandoPersonajes}>{cargando ? "Guardando..." : "Continuar"}</button>
      </form>
    </main>
  );
};

export default OnboardingPage;
