import React, { useEffect, useState } from "react";

const estadoInicial = {
  codigo_grado: "",
  nombre_grado: "",
  descripcion: "",
  orden_visualizacion: "1",
  estado: "activo",
};

/**
 * Funcion: GradoForm
 *
 * Descripcion:
 * Muestra el formulario para crear o editar grados y valida los campos antes de enviarlos.
 *
 * Es llamada desde:
 * GradosPage.jsx, que le envia gradoSeleccionado, guardando, erroresBackend, onGuardar y onCancelar.
 *
 * Llama a:
 * handleSubmit() al enviar el formulario y onGuardar(datos) para que GradosPage ejecute el servicio.
 *
 * Parametros:
 * gradoSeleccionado, guardando, erroresBackend, onGuardar y onCancelar recibidos como props.
 *
 * Resultado:
 * Renderiza campos de codigo, nombre, descripcion, orden, estado y botones de accion.
 *
 * Manejo de errores:
 * Muestra validaciones por campo y conserva datos si el backend rechaza la solicitud.
 */
const GradoForm = ({ gradoSeleccionado, guardando, erroresBackend, onGuardar, onCancelar }) => {
  const [formulario, setFormulario] = useState(estadoInicial);
  const [errores, setErrores] = useState({});

  /**
   * Funcion: useEffect de sincronizacion
   *
   * Descripcion:
   * Copia el grado seleccionado al formulario cuando se presiona Editar.
   *
   * Es llamada desde:
   * React cuando cambia gradoSeleccionado.
   *
   * Llama a:
   * setFormulario() y setErrores().
   *
   * Parametros:
   * Usa gradoSeleccionado desde props.
   *
   * Resultado:
   * Cambia el formulario entre modo creacion y modo edicion.
   *
   * Manejo de errores:
   * Si no hay grado seleccionado restaura el estado inicial.
   */
  useEffect(() => {
    if (gradoSeleccionado) {
      setFormulario({
        codigo_grado: gradoSeleccionado.codigo_grado || "",
        nombre_grado: gradoSeleccionado.nombre_grado || "",
        descripcion: gradoSeleccionado.descripcion || "",
        orden_visualizacion: String(gradoSeleccionado.orden_visualizacion || 1),
        estado: gradoSeleccionado.estado || "activo",
      });
    } else {
      setFormulario(estadoInicial);
    }
    setErrores({});
  }, [gradoSeleccionado]);

  /**
   * Funcion: actualizarCampo
   *
   * Descripcion:
   * Actualiza el estado local cuando cambia un input o selector.
   *
   * Es llamada desde:
   * Los campos codigo_grado, nombre_grado, descripcion, orden_visualizacion y estado.
   *
   * Llama a:
   * setFormulario() y setErrores().
   *
   * Parametros:
   * evento emitido por el control del formulario.
   *
   * Resultado:
   * Mantiene sincronizado el formulario y convierte el codigo a mayusculas.
   *
   * Manejo de errores:
   * Limpia el error del campo que el usuario esta corrigiendo.
   */
  const actualizarCampo = (evento) => {
    const { name, value } = evento.target;
    const nuevoValor = name === "codigo_grado" ? value.toUpperCase() : value;
    setFormulario((actual) => ({ ...actual, [name]: nuevoValor }));
    setErrores((actual) => ({ ...actual, [name]: "" }));
  };

  /**
   * Funcion: validarFormulario
   *
   * Descripcion:
   * Verifica que codigo, nombre, orden y estado cumplan las reglas antes de enviar.
   *
   * Es llamada desde:
   * handleSubmit() al presionar Guardar o Actualizar.
   *
   * Llama a:
   * setErrores() para mostrar validaciones por campo.
   *
   * Parametros:
   * No recibe parametros; usa el estado formulario.
   *
   * Resultado:
   * Devuelve true si el formulario es valido o false si hay errores.
   *
   * Manejo de errores:
   * Registra mensajes visibles y evita llamadas al backend cuando hay datos invalidos.
   */
  const validarFormulario = () => {
    const nuevosErrores = {};
    const orden = Number(formulario.orden_visualizacion);

    if (!formulario.codigo_grado.trim()) {
      nuevosErrores.codigo_grado = "Escriba el código del grado.";
    } else if (formulario.codigo_grado.trim().length > 20) {
      nuevosErrores.codigo_grado = "El código no debe superar 20 caracteres.";
    }

    if (!formulario.nombre_grado.trim()) {
      nuevosErrores.nombre_grado = "Escriba el nombre del grado.";
    } else if (formulario.nombre_grado.trim().length > 100) {
      nuevosErrores.nombre_grado = "El nombre no debe superar 100 caracteres.";
    }

    if (formulario.descripcion.trim().length > 255) {
      nuevosErrores.descripcion = "La descripción no debe superar 255 caracteres.";
    }

    if (!Number.isInteger(orden) || orden <= 0) {
      nuevosErrores.orden_visualizacion = "El orden debe ser un entero mayor que cero.";
    }

    if (!["activo", "inactivo"].includes(formulario.estado)) {
      nuevosErrores.estado = "Seleccione un estado válido.";
    }

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  /**
   * Funcion: handleSubmit
   *
   * Descripcion:
   * Limpia y prepara los datos del grado para enviarlos al componente padre.
   *
   * Es llamada desde:
   * El evento submit del formulario.
   *
   * Llama a:
   * validarFormulario() y onGuardar(datos), que llama crearGrado() o actualizarGrado().
   *
   * Parametros:
   * evento submit del formulario.
   *
   * Resultado:
   * Envia datos normalizados con codigo en mayusculas y espacios eliminados.
   *
   * Manejo de errores:
   * Si la validacion falla, detiene el envio y muestra errores por campo.
   */
  const handleSubmit = (evento) => {
    evento.preventDefault();
    if (!validarFormulario()) {
      return;
    }

    onGuardar({
      codigo_grado: formulario.codigo_grado.trim().toUpperCase(),
      nombre_grado: formulario.nombre_grado.trim(),
      descripcion: formulario.descripcion.trim(),
      orden_visualizacion: Number(formulario.orden_visualizacion),
      estado: formulario.estado,
    });
  };

  const erroresVisibles = { ...erroresBackend, ...errores };

  return (
    <form className="seccion-form" onSubmit={handleSubmit}>
      <h2><span aria-hidden="true">▣</span>{gradoSeleccionado ? "Editar grado" : "Nuevo grado"}</h2>

      <label>
        Código
        <input
          type="text"
          name="codigo_grado"
          value={formulario.codigo_grado}
          onChange={actualizarCampo}
          placeholder="4P"
          maxLength="20"
        />
        {erroresVisibles.codigo_grado && <span className="field-error">{erroresVisibles.codigo_grado}</span>}
      </label>

      <label>
        Nombre del grado
        <input
          type="text"
          name="nombre_grado"
          value={formulario.nombre_grado}
          onChange={actualizarCampo}
          placeholder="Cuarto"
          maxLength="100"
        />
        {erroresVisibles.nombre_grado && <span className="field-error">{erroresVisibles.nombre_grado}</span>}
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
        {erroresVisibles.descripcion && <span className="field-error">{erroresVisibles.descripcion}</span>}
      </label>

      <label>
        Orden
        <input
          type="number"
          name="orden_visualizacion"
          value={formulario.orden_visualizacion}
          onChange={actualizarCampo}
          min="1"
          step="1"
        />
        {erroresVisibles.orden_visualizacion && (
          <span className="field-error">{erroresVisibles.orden_visualizacion}</span>
        )}
      </label>

      <label>
        Estado
        <select name="estado" value={formulario.estado} onChange={actualizarCampo}>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
        {erroresVisibles.estado && <span className="field-error">{erroresVisibles.estado}</span>}
      </label>

      <div className="form-actions">
        <button type="submit" disabled={guardando}>
          {guardando ? "Guardando..." : gradoSeleccionado ? "Actualizar" : "Guardar"}
        </button>
        {gradoSeleccionado && (
          <button type="button" className="secondary" onClick={onCancelar} disabled={guardando}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
};

export default GradoForm;

