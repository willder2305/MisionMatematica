import React, { useEffect, useState } from "react";

const estadoInicial = {
  id_grado: "",
  nombre_seccion: "",
  descripcion: "",
  estado: "activo",
};

const SECCIONES_PERMITIDAS = ["A", "B", "C", "D"];

/**
 * Funcion: SeccionForm
 *
 * Descripcion:
 * Muestra el formulario para crear o editar secciones y valida los campos antes de enviarlos.
 *
 * Es llamada desde:
 * SeccionesPage.jsx, que le envia grados, seccionSeleccionada, onGuardar y onCancelar.
 *
 * Llama a:
 * handleSubmit() al enviar el formulario y onGuardar(datos) para que SeccionesPage ejecute el servicio.
 *
 * Resultado:
 * Renderiza campos de grado, nombre, descripcion, estado y botones de guardar, actualizar o cancelar.
 *
 * Manejo de errores:
 * Muestra mensajes de validacion debajo de cada campo y no envia datos invalidos.
 */
const SeccionForm = ({ grados, seccionSeleccionada, guardando, onGuardar, onCancelar }) => {
  const [formulario, setFormulario] = useState(estadoInicial);
  const [errores, setErrores] = useState({});

  /**
   * Funcion: useEffect de sincronizacion
   *
   * Descripcion:
   * Copia la seccion seleccionada al formulario cuando el usuario presiona Editar.
   *
   * Es llamada desde:
   * React cuando cambia seccionSeleccionada.
   *
   * Llama a:
   * setFormulario() y setErrores() para preparar el formulario.
   *
   * Resultado:
   * Cambia el formulario entre modo creacion y modo edicion.
   *
   * Manejo de errores:
   * Si no hay seccion seleccionada, restaura el formulario inicial.
   */
  useEffect(() => {
    if (seccionSeleccionada) {
      setFormulario({
        id_grado: String(seccionSeleccionada.id_grado),
        nombre_seccion: seccionSeleccionada.nombre_seccion,
        descripcion: seccionSeleccionada.descripcion || "",
        estado: seccionSeleccionada.estado,
      });
    } else {
      setFormulario(estadoInicial);
    }
    setErrores({});
  }, [seccionSeleccionada]);

  /**
   * Funcion: actualizarCampo
   *
   * Descripcion:
   * Actualiza el estado local del formulario cuando cambia un input o select.
   *
   * Es llamada desde:
   * Los campos grado, nombre_seccion, descripcion y estado del formulario.
   *
   * Llama a:
   * setFormulario() para guardar el nuevo valor.
   *
   * Resultado:
   * Mantiene sincronizados los controles con el estado de React.
   *
   * Manejo de errores:
   * Limpia el error visible del campo que el usuario esta corrigiendo.
   */
  const actualizarCampo = (evento) => {
    const { name, value } = evento.target;
    setFormulario((actual) => ({ ...actual, [name]: value }));
    setErrores((actual) => ({ ...actual, [name]: "" }));
  };

  /**
   * Funcion: validarFormulario
   *
   * Descripcion:
   * Verifica que el formulario tenga grado, nombre de seccion y estado valido.
   *
   * Es llamada desde:
   * handleSubmit() antes de llamar a onGuardar(datos).
   *
   * Llama a:
   * setErrores() cuando encuentra campos invalidos.
   *
   * Resultado:
   * Devuelve true si los datos son validos o false si falta informacion.
   *
   * Manejo de errores:
   * Registra mensajes visibles debajo de los campos con problemas.
   */
  const validarFormulario = () => {
    const nuevosErrores = {};
    if (!formulario.id_grado) {
      nuevosErrores.id_grado = "Seleccione un grado.";
    }
    if (!SECCIONES_PERMITIDAS.includes(formulario.nombre_seccion)) {
      nuevosErrores.nombre_seccion = "Seleccione una sección entre A, B, C o D.";
    }
    if (!["activo", "inactivo"].includes(formulario.estado)) {
      nuevosErrores.estado = "Seleccione un estado valido.";
    }
    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  /**
   * Funcion: handleSubmit
   *
   * Descripcion:
   * Prepara los datos limpios del formulario y los envia al componente padre.
   *
   * Es llamada desde:
   * El evento submit del formulario al presionar Guardar o Actualizar.
   *
   * Llama a:
   * validarFormulario() y onGuardar(datos), que despues llama a crearSeccion() o actualizarSeccion().
   *
   * Resultado:
   * Envia id_grado, nombre_seccion, descripcion y estado sin espacios innecesarios.
   *
   * Manejo de errores:
   * Si hay errores de validacion, detiene el envio y mantiene los mensajes visibles.
   */
  const handleSubmit = (evento) => {
    evento.preventDefault();
    if (!validarFormulario()) {
      return;
    }

    onGuardar({
      id_grado: Number(formulario.id_grado),
      nombre_seccion: formulario.nombre_seccion.trim(),
      descripcion: formulario.descripcion.trim(),
      estado: formulario.estado,
    });
  };

  return (
    <form className="seccion-form" onSubmit={handleSubmit}>
      <h2><span aria-hidden="true">⚑</span>{seccionSeleccionada ? "Editar sección" : "Nueva sección"}</h2>

      <label>
        Grado
        <select name="id_grado" value={formulario.id_grado} onChange={actualizarCampo}>
          <option value="">Seleccione un grado</option>
          {grados.map((grado) => (
            <option key={grado.id_grado} value={grado.id_grado}>
              {grado.codigo_grado} - {grado.nombre_grado}
            </option>
          ))}
        </select>
        {errores.id_grado && <span className="field-error">{errores.id_grado}</span>}
      </label>

      <label>
        Sección
        <select
          name="nombre_seccion"
          value={formulario.nombre_seccion}
          onChange={actualizarCampo}
        >
          <option value="">Seleccione una seccion</option>
          {SECCIONES_PERMITIDAS.map((seccion) => (
            <option key={seccion} value={seccion}>{seccion}</option>
          ))}
        </select>
        {errores.nombre_seccion && <span className="field-error">{errores.nombre_seccion}</span>}
      </label>

      <label>
        Descripción
        <textarea
          name="descripcion"
          value={formulario.descripcion}
          onChange={actualizarCampo}
          placeholder="Descripción opcional"
          maxLength="255"
        />
      </label>

      <label>
        Estado
        <select name="estado" value={formulario.estado} onChange={actualizarCampo}>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
        {errores.estado && <span className="field-error">{errores.estado}</span>}
      </label>

      <div className="form-actions">
        <button type="submit" disabled={guardando}>
          {guardando ? "Guardando..." : seccionSeleccionada ? "Actualizar" : "Guardar"}
        </button>
        {seccionSeleccionada && (
          <button type="button" className="secondary" onClick={onCancelar} disabled={guardando}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
};

export default SeccionForm;



