import React from "react";
import PixelEmptyState from "../ui/PixelEmptyState";
import { formatLabel } from "../../constants/uiLabels";

/**
 * Funcion: GradosTable
 *
 * Descripcion:
 * Muestra una tabla con los grados recibidos desde GradosPage.
 *
 * Es llamada desde:
 * GradosPage.jsx despues de cargar los registros con obtenerGrados().
 *
 * Llama a:
 * onEditar(grado) y onCambiarEstado(grado) segun la accion seleccionada.
 *
 * Parametros:
 * grados, onEditar y onCambiarEstado recibidos como props.
 *
 * Resultado:
 * Renderiza ID, codigo, grado, descripcion, orden, secciones, estado y acciones.
 *
 * Manejo de errores:
 * No realiza llamadas HTTP; cualquier error lo maneja GradosPage mediante callbacks.
 */
const renderCodigos = (grado, codigos) => {
  // Muestra el PIN general solo cuando el grado funciona como seccion unica.
  if (!codigos?.length) {
    return <span className="pin-empty">{grado.total_secciones > 0 ? "Con secciones" : "Sin PIN activo"}</span>;
  }
  return (
    <div className="pin-code-list">
      {codigos.map((codigo) => (
        <span key={codigo.id_pin} className="pin-code">
          <strong>{codigo.pin}</strong>
          <small>Sección única</small>
          {codigo.docente && <small>{codigo.docente}</small>}
        </span>
      ))}
    </div>
  );
};

const GradosTable = ({ grados, codigosPorGrado, onEditar, onCambiarEstado }) => {
  if (grados.length === 0) {
    return (
      <PixelEmptyState
        title="No existen grados registrados."
        description="Crea el primer grado para comenzar."
      />
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Código</th>
            <th>Grado</th>
            <th>Descripción</th>
            <th>Orden</th>
            <th>Secciones</th>
            <th>Código de sección única</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {grados.map((grado) => (
            <tr key={grado.id_grado}>
              <td>{grado.id_grado}</td>
              <td>{grado.codigo_grado}</td>
              <td>{grado.nombre_grado}</td>
              <td>{grado.descripcion || "Sin descripción"}</td>
              <td>{grado.orden_visualizacion}</td>
              <td>{grado.total_secciones}</td>
              <td>{renderCodigos(grado, codigosPorGrado[grado.id_grado])}</td>
              <td>
                <span className={`badge ${grado.estado}`}>{formatLabel(grado.estado)}</span>
              </td>
              <td className="actions">
                <button type="button" className="secondary edit" onClick={() => onEditar(grado)}>
                  Editar
                </button>
                <button type="button" className="secondary state" onClick={() => onCambiarEstado(grado)}>
                  {grado.estado === "activo" ? "Desactivar" : "Activar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default GradosTable;

