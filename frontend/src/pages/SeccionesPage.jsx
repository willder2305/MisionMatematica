import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import SeccionForm from "../components/secciones/SeccionForm";
import SeccionesTable from "../components/secciones/SeccionesTable";
import {
  actualizarSeccion,
  cambiarEstadoSeccion,
  crearSeccion,
  obtenerGrados,
  obtenerSecciones,
} from "../services/seccionesService";
import { obtenerUsuarioLocal } from "../services/authService";
import { obtenerCodigosSecciones } from "../services/gruposService";

/**
 * Funcion: SeccionesPage
 *
 * Descripcion:
 * Coordina la administracion completa de secciones: consulta, creacion, edicion, cambio de estado y eliminacion.
 *
 * Es llamada desde:
 * src/main.jsx como pantalla principal de la aplicacion React.
 *
 * Llama a:
 * SeccionForm, SeccionesTable y las funciones de src/services/seccionesService.js.
 *
 * Resultado:
 * Renderiza la vista Administracion de secciones con tabla, formulario, mensajes y modal de confirmacion.
 *
 * Manejo de errores:
 * Captura errores de servicios y muestra mensajes visibles sin usar alert() ni confirm().
 */
const SeccionesPage = () => {
  const [secciones, setSecciones] = useState([]);
  const [grados, setGrados] = useState([]);
  const [codigosPorSeccion, setCodigosPorSeccion] = useState({});
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [seccionSeleccionada, setSeccionSeleccionada] = useState(null);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const usuario = obtenerUsuarioLocal();
  const puedeCrearSecciones = usuario?.rol === "docente";

  /**
   * Funcion: mostrarMensaje
   *
   * Descripcion:
   * Guarda un mensaje de exito o error para mostrarlo en la parte superior de la pagina.
   *
   * Es llamada desde:
   * cargarSecciones(), cargarGrados(), guardarSeccion(), cambiarEstado() y confirmarEliminacion().
   *
   * Llama a:
   * setMensaje() para actualizar el estado visual.
   *
   * Resultado:
   * Muestra el texto recibido dentro de la interfaz.
   *
   * Manejo de errores:
   * Si recibe texto vacio, limpia el mensaje actual.
   */
  const mostrarMensaje = (tipo, texto) => {
    setMensaje({ tipo, texto });
  };

  /**
   * Funcion: cargarSecciones
   *
   * Descripcion:
   * Solicita al backend todas las secciones registradas y actualiza el estado del componente.
   *
   * Es llamada desde:
   * El hook useEffect al cargar SeccionesPage y despues de crear, editar o cambiar estado.
   *
   * Llama a:
   * obtenerSecciones(), ubicada en src/services/seccionesService.js, que consume GET /api/secciones.
   *
   * Resultado:
   * Actualiza el estado secciones con los datos recibidos desde Flask y MySQL.
   *
   * Manejo de errores:
   * Muestra un mensaje visible si la solicitud falla y deja la tabla vacia.
   */
  const cargarSecciones = async () => {
    try {
      setCargando(true);
      const [respuesta, respuestaCodigos] = await Promise.all([
        obtenerSecciones(),
        obtenerCodigosSecciones(),
      ]);
      setSecciones(respuesta.data || []);
      setCodigosPorSeccion(
        (respuestaCodigos.data || []).reduce((mapa, codigo) => {
          const idSeccion = codigo.id_seccion;
          mapa[idSeccion] = [...(mapa[idSeccion] || []), codigo];
          return mapa;
        }, {}),
      );
    } catch (error) {
      setSecciones([]);
      setCodigosPorSeccion({});
      mostrarMensaje("error", error.message);
    } finally {
      setCargando(false);
    }
  };

  /**
   * Funcion: cargarGrados
   *
   * Descripcion:
   * Solicita al backend los grados disponibles para alimentar el selector del formulario.
   *
   * Es llamada desde:
   * El hook useEffect cuando se carga SeccionesPage.
   *
   * Llama a:
   * obtenerGrados(), ubicada en src/services/seccionesService.js, que consume GET /api/grados.
   *
   * Resultado:
   * Actualiza el estado grados con los datos reales de MySQL.
   *
   * Manejo de errores:
   * Muestra un mensaje visible si no se pueden cargar los grados.
   */
  const cargarGrados = async () => {
    try {
      const respuesta = await obtenerGrados();
      setGrados(respuesta.data || []);
    } catch (error) {
      setGrados([]);
      mostrarMensaje("error", error.message);
    }
  };

  /**
   * Funcion: useEffect de carga inicial
   *
   * Descripcion:
   * Ejecuta la carga inicial de grados y secciones cuando la pagina aparece.
   *
   * Es llamada desde:
   * React al montar SeccionesPage.
   *
   * Llama a:
   * cargarGrados() y cargarSecciones().
   *
   * Resultado:
   * Llena la tabla y el selector con datos provenientes del backend.
   *
   * Manejo de errores:
   * Cada funcion llamada maneja sus propios errores y muestra mensajes.
   */
  useEffect(() => {
    cargarGrados();
    cargarSecciones();
  }, []);

  /**
   * Funcion: abrirFormularioNuevo
   *
   * Descripcion:
   * Limpia la seccion seleccionada para que el formulario quede en modo creacion.
   *
   * Es llamada desde:
   * El boton Nueva seccion ubicado en esta pagina.
   *
   * Llama a:
   * setSeccionSeleccionada() y mostrarMensaje().
   *
   * Resultado:
   * El formulario muestra los campos vacios para registrar una seccion nueva.
   *
   * Manejo de errores:
   * No ejecuta solicitudes externas, por lo que no requiere manejo especial de errores.
   */
  const abrirFormularioNuevo = () => {
    if (!puedeCrearSecciones) {
      mostrarMensaje("error", "El administrador solo supervisa y edita secciones; la creación corresponde al docente.");
      return;
    }
    setSeccionSeleccionada(null);
    mostrarMensaje("", "");
  };

  /**
   * Funcion: seleccionarSeccionParaEditar
   *
   * Descripcion:
   * Recibe una seccion desde la tabla y la coloca en el formulario para editarla.
   *
   * Es llamada desde:
   * onEditar(seccion) en SeccionesTable.jsx.
   *
   * Llama a:
   * setSeccionSeleccionada() y mostrarMensaje().
   *
   * Resultado:
   * El formulario cambia a modo edicion con los datos actuales de la seccion.
   *
   * Manejo de errores:
   * Si la seccion no llega completa, React mantiene el ultimo estado valido.
   */
  const seleccionarSeccionParaEditar = (seccion) => {
    setSeccionSeleccionada(seccion);
    mostrarMensaje("", "");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Funcion: guardarSeccion
   *
   * Descripcion:
   * Decide si debe crear una seccion nueva o actualizar la seccion seleccionada.
   *
   * Es llamada desde:
   * onGuardar(datos) en SeccionForm.jsx despues de handleSubmit().
   *
   * Llama a:
   * crearSeccion(datos) o actualizarSeccion(id, datos), ubicadas en src/services/seccionesService.js.
   *
   * Resultado:
   * Guarda cambios en MySQL mediante Flask, refresca la tabla y muestra mensaje de exito.
   *
   * Manejo de errores:
   * Muestra el mensaje enviado por el backend si faltan datos, hay duplicados o falla la conexion.
   */
  const guardarSeccion = async (datos) => {
    try {
      setGuardando(true);
      const respuesta = seccionSeleccionada
        ? await actualizarSeccion(seccionSeleccionada.id_seccion, datos)
        : await crearSeccion(datos);
      mostrarMensaje("success", respuesta.message);
      setSeccionSeleccionada(null);
      await cargarSecciones();
    } catch (error) {
      mostrarMensaje("error", error.message);
    } finally {
      setGuardando(false);
    }
  };

  /**
   * Funcion: cambiarEstado
   *
   * Descripcion:
   * Alterna una seccion entre activo e inactivo sin eliminarla.
   *
   * Es llamada desde:
   * onCambiarEstado(seccion) en SeccionesTable.jsx.
   *
   * Llama a:
   * cambiarEstadoSeccion(idSeccion, estado), ubicada en src/services/seccionesService.js.
   *
   * Resultado:
   * Actualiza el estado en MySQL y refresca la tabla.
   *
   * Manejo de errores:
   * Muestra un mensaje visible cuando el backend rechaza la operacion.
   */
  const cambiarEstado = async (seccion) => {
    try {
      const nuevoEstado = seccion.estado === "activo" ? "inactivo" : "activo";
      const respuesta = await cambiarEstadoSeccion(seccion.id_seccion, nuevoEstado);
      mostrarMensaje("success", respuesta.message);
      await cargarSecciones();
    } catch (error) {
      mostrarMensaje("error", error.message);
    }
  };

  return (
    <section className="content">
        <div className="header-row">
          <div>
            <h1>Administración de secciones</h1>
            <p>Gestión de secciones para Cuarto, Quinto y Sexto primaria.</p>
          </div>
          {puedeCrearSecciones && (
            <button type="button" className="pixel-primary-button success" onClick={abrirFormularioNuevo}>
              + Nueva sección
            </button>
          )}
        </div>

        <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

        {(puedeCrearSecciones || seccionSeleccionada) && (
          <SeccionForm
            grados={grados}
            seccionSeleccionada={seccionSeleccionada}
            guardando={guardando}
            onGuardar={guardarSeccion}
            onCancelar={() => setSeccionSeleccionada(null)}
          />
        )}

        <section className="table-section">
          <h2>Secciones registradas</h2>
          {cargando ? (
            <PixelLoader text="Cargando secciones..." />
          ) : (
            <SeccionesTable
              secciones={secciones}
              codigosPorSeccion={codigosPorSeccion}
              onEditar={seleccionarSeccionParaEditar}
              onCambiarEstado={cambiarEstado}
            />
          )}
        </section>
      </section>
  );
};

export default SeccionesPage;





