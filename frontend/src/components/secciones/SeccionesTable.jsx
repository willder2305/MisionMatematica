import React from "react";
import PixelEmptyState from "../ui/PixelEmptyState";
import { formatLabel } from "../../constants/uiLabels";

/**
 * Funcion: SeccionesTable
 *
 * Descripcion:
 * Muestra una tabla con las secciones recibidas desde SeccionesPage.
 *
 * Es llamada desde:
 * SeccionesPage.jsx despues de cargar los registros desde obtenerSecciones().
 *
 * Llama a:
 * onEditar(seccion) y onCambiarEstado(seccion) segun la accion seleccionada.
 *
 * Resultado:
 * Renderiza ID, grado, seccion, descripcion, estado y botones de accion.
 *
 * Manejo de errores:
 * No realiza solicitudes HTTP; cualquier error lo maneja SeccionesPage mediante los callbacks.
 */
const renderCodigos = (codigos) => {
  // Muestra uno o varios PIN activos segun el rol que consulta la tabla.
  if (!codigos?.length) return <span className="pin-empty">Sin PIN activo</span>;
  return (
    <div className="pin-code-list">
      {codigos.map((codigo) => (
        <span key={codigo.id_pin} className="pin-code">
          <strong>{codigo.pin}</strong>
          {codigo.docente && <small>{codigo.docente}</small>}
        </span>
      ))}
    </div>
  );
};

const SeccionesTable = ({ secciones, codigosPorSeccion, onEditar, onCambiarEstado }) => {
  if (secciones.length === 0) {
    return (
      <PixelEmptyState
        title="No existen secciones registradas."
        description="Crea la primera sección para comenzar."
      />
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Grado</th>
            <th>Sección</th>
            <th>Código/PIN</th>
            <th>Descripción</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {secciones.map((seccion) => (
            <tr key={seccion.id_seccion}>
              <td>{seccion.id_seccion}</td>
              <td>{seccion.grado?.nombre_grado || "Sin grado"}</td>
              <td>{seccion.nombre_seccion}</td>
              <td>{renderCodigos(codigosPorSeccion[seccion.id_seccion])}</td>
              <td>{seccion.descripcion || "Sin descripción"}</td>
              <td>
                <span className={`badge ${seccion.estado}`}>{formatLabel(seccion.estado)}</span>
              </td>
              <td className="actions">
                <button type="button" className="secondary edit" onClick={() => onEditar(seccion)}>
                  Editar
                </button>
                <button type="button" className="secondary state" onClick={() => onCambiarEstado(seccion)}>
                  {seccion.estado === "activo" ? "Desactivar" : "Activar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SeccionesTable;


