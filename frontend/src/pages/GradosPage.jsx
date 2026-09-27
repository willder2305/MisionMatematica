import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import GradoForm from "../components/grados/GradoForm";
import GradosTable from "../components/grados/GradosTable";
import {
  actualizarGrado,
  cambiarEstadoGrado,
  obtenerGrados,
} from "../services/gradosService";
import { obtenerCodigosGradosUnicos } from "../services/gruposService";

/**
 * Funcion: GradosPage
 *
 * Descripcion:
 * Coordina el CRUD completo de grados: consulta, creacion, edicion, cambio de estado y eliminacion.
 *
 * Es llamada desde:
 * src/main.jsx cuando la ruta del navegador es /grados.
 *
 * Llama a:
 * GradoForm, GradosTable y funciones de src/services/gradosService.js.
 *
 * Parametros:
 * No recibe parametros directos.
 *
 * Resultado:
 * Renderiza la vista Administracion de grados con tabla, formulario, mensajes y modal.
 *
 * Manejo de errores:
 * Captura errores del servicio, muestra mensajes visibles y conserva el formulario si falla una solicitud.
 */
const GradosPage = () => {
  const [grados, setGrados] = useState([]);
  const [codigosPorGrado, setCodigosPorGrado] = useState({});
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [gradoSeleccionado, setGradoSeleccionado] = useState(null);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });
  const [erroresBackend, setErroresBackend] = useState({});

  /**
   * Funcion: mostrarMensaje
   *
   * Descripcion:
   * Guarda mensajes de exito o error para mostrarlos en la pagina.
   *
   * Es llamada desde:
   * cargarGrados(), guardarGrado() y cambiarEstado().
   *
   * Llama a:
   * setMensaje() para actualizar el estado visual.
   *
   * Parametros:
   * tipo y texto del mensaje.
   *
   * Resultado:
   * Muestra o limpia el mensaje en la interfaz.
   *
   * Manejo de errores:
   * Si el texto es vacio, limpia el mensaje actual.
   */
  const mostrarMensaje = (tipo, texto) => {
    setMensaje({ tipo, texto });
  };

  /**
   * Funcion: cargarGrados
   *
   * Descripcion:
   * Solicita al backend la lista de grados y actualiza el estado.
   *
   * Es llamada desde:
   * El hook useEffect cuando se carga GradosPage y despues de operaciones exitosas.
   *
   * Llama a:
   * obtenerGrados(), ubicada en src/services/gradosService.js, que consume GET /api/grados.
   *
   * Parametros:
   * No recibe parametros.
   *
   * Resultado:
   * Actualiza el estado grados con datos provenientes de Flask y MySQL.
   *
   * Manejo de errores:
   * Muestra un mensaje visible si falla la solicitud y deja la tabla vacia.
   */
  const cargarGrados = async () => {
    try {
      setCargando(true);
      const [respuesta, respuestaCodigos] = await Promise.all([
        obtenerGrados(),
        obtenerCodigosGradosUnicos(),
      ]);
      setGrados(respuesta.data || []);
      setCodigosPorGrado(
        (respuestaCodigos.data || []).reduce((mapa, codigo) => {
          const idGrado = codigo.id_grado;
          mapa[idGrado] = [...(mapa[idGrado] || []), codigo];
          return mapa;
        }, {}),
      );
    } catch (error) {
      setGrados([]);
      setCodigosPorGrado({});
      mostrarMensaje("error", error.message);
    } finally {
      setCargando(false);
    }
  };

  /**
   * Funcion: useEffect de carga inicial
   *
   * Descripcion:
   * Ejecuta la carga inicial de grados cuando la pagina aparece.
   *
   * Es llamada desde:
   * React al montar GradosPage.
   *
   * Llama a:
   * cargarGrados().
   *
   * Parametros:
   * No recibe parametros.
   *
   * Resultado:
   * Llena la tabla con datos reales desde MySQL.
   *
   * Manejo de errores:
   * cargarGrados() captura y muestra cualquier error.
   */
  useEffect(() => {
    cargarGrados();
  }, []);

  /**
   * Funcion: abrirFormularioNuevo
   *
   * Descripcion:
   * Limpia seleccion y errores para preparar el formulario en modo creacion.
   *
   * Es llamada desde:
   * El boton Nuevo grado de esta pagina.
   *
   * Llama a:
   * setGradoSeleccionado(), setErroresBackend() y mostrarMensaje().
   *
   * Parametros:
   * No recibe parametros.
   *
   * Resultado:
   * El formulario queda listo para registrar un grado nuevo.
   *
   * Manejo de errores:
   * No ejecuta solicitudes externas, por lo que no requiere manejo especial.
   */
  /**
   * Funcion: seleccionarGradoParaEditar
   *
   * Descripcion:
   * Coloca un grado de la tabla en el formulario para editarlo.
   *
   * Es llamada desde:
   * onEditar(grado) en GradosTable.jsx.
   *
   * Llama a:
   * setGradoSeleccionado(), setErroresBackend(), mostrarMensaje() y window.scrollTo().
   *
   * Parametros:
   * grado seleccionado desde la tabla.
   *
   * Resultado:
   * El formulario cambia a modo edicion con datos actuales.
   *
   * Manejo de errores:
   * Si el grado llega incompleto, React conserva el estado anterior hasta una nueva accion.
   */
  const seleccionarGradoParaEditar = (grado) => {
    setGradoSeleccionado(grado);
    setErroresBackend({});
    mostrarMensaje("", "");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Funcion: guardarGrado
   *
   * Descripcion:
   * Decide si debe crear un grado nuevo o actualizar el grado seleccionado.
   *
   * Es llamada desde:
   * onGuardar(datos) en GradoForm.jsx despues de handleSubmit().
   *
   * Llama a:
   * crearGrado(datos) o actualizarGrado(idGrado, datos), ubicadas en gradosService.js.
   *
   * Parametros:
   * datos normalizados recibidos desde el formulario.
   *
   * Resultado:
   * Guarda en MySQL mediante Flask, refresca la tabla y muestra mensaje de exito.
   *
   * Manejo de errores:
   * Muestra mensaje y errores por campo del backend sin limpiar el formulario.
   */
  const guardarGrado = async (datos) => {
    try {
      setGuardando(true);
      setErroresBackend({});
      const respuesta = gradoSeleccionado
        ? await actualizarGrado(gradoSeleccionado.id_grado, datos)
        : null;
      if (!respuesta) {
        mostrarMensaje("error", "Seleccione un grado base para editar.");
        return;
      }
      mostrarMensaje("success", respuesta.message);
      setGradoSeleccionado(null);
      await cargarGrados();
    } catch (error) {
      setErroresBackend(error.errors || {});
      mostrarMensaje("error", error.message);
    } finally {
      setGuardando(false);
    }
  };

  /**
   * Funcion: cambiarEstado
   *
   * Descripcion:
   * Alterna un grado entre activo e inactivo sin eliminarlo.
   *
   * Es llamada desde:
   * onCambiarEstado(grado) en GradosTable.jsx.
   *
   * Llama a:
   * cambiarEstadoGrado(idGrado, nuevoEstado), ubicada en gradosService.js.
   *
   * Parametros:
   * grado seleccionado desde la tabla.
   *
   * Resultado:
   * Actualiza el estado en MySQL y refresca la tabla.
   *
   * Manejo de errores:
   * Muestra mensaje visible si el backend rechaza la operacion.
   */
  const cambiarEstado = async (grado) => {
    try {
      const nuevoEstado = grado.estado === "activo" ? "inactivo" : "activo";
      const respuesta = await cambiarEstadoGrado(grado.id_grado, nuevoEstado);
      mostrarMensaje("success", respuesta.message);
      await cargarGrados();
    } catch (error) {
      mostrarMensaje("error", error.message);
    }
  };

  return (
    <section className="content">
        <div className="header-row">
          <div>
            <h1>Administración de grados</h1>
            <p>Gestión de Cuarto, Quinto y Sexto primaria para el módulo de secciones.</p>
          </div>
        </div>

        <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

        {gradoSeleccionado && (
          <GradoForm
            gradoSeleccionado={gradoSeleccionado}
            guardando={guardando}
            erroresBackend={erroresBackend}
            onGuardar={guardarGrado}
            onCancelar={() => {
              setGradoSeleccionado(null);
              setErroresBackend({});
            }}
          />
        )}

        <section className="table-section">
          <h2>Grados registrados</h2>
          {cargando ? (
            <PixelLoader text="Cargando grados..." />
          ) : (
            <GradosTable
              grados={grados}
              codigosPorGrado={codigosPorGrado}
              onEditar={seleccionarGradoParaEditar}
              onCambiarEstado={cambiarEstado}
            />
          )}
        </section>
      </section>
  );
};

export default GradosPage;




