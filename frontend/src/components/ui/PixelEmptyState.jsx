import React from "react";
import estadoVacio from "../../assets/pixel/estado_vacio_isla_cartel.png";

/**
 * Funcion: PixelEmptyState
 *
 * Descripcion:
 * Muestra una ilustracion pixel-art y texto cuando una lista no tiene registros.
 *
 * Es llamada desde:
 * SeccionesTable.jsx y GradosTable.jsx cuando el arreglo recibido esta vacio.
 *
 * Llama a:
 * No llama servicios; usa la imagen estado_vacio_isla_cartel.png.
 *
 * Parametros:
 * title y description para personalizar el mensaje vacio.
 *
 * Retorna:
 * Estado vacio accesible con imagen y texto.
 *
 * Manejo de errores:
 * Si no recibe description, muestra solo el titulo.
 */
const PixelEmptyState = ({ title, description }) => (
  <div className="pixel-empty-state">
    <img className="pixel-art" src={estadoVacio} alt="Isla pixel-art con cartel" loading="lazy" decoding="async" />
    <div>
      <p>{title}</p>
      {description && <span>{description}</span>}
    </div>
  </div>
);

export default PixelEmptyState;
