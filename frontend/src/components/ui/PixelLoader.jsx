import React from "react";

/**
 * Funcion: PixelLoader
 *
 * Descripcion:
 * Muestra un indicador de carga pixel-art con spinner CSS y texto.
 *
 * Es llamada desde:
 * SeccionesPage.jsx y GradosPage.jsx mientras cargan los registros.
 *
 * Llama a:
 * No llama funciones externas; solo renderiza estado visual de carga.
 *
 * Parametros:
 * text con el mensaje de carga visible.
 *
 * Retorna:
 * Bloque de carga accesible con role status.
 *
 * Manejo de errores:
 * Si no recibe text, usa un mensaje generico de carga.
 */
const PixelLoader = ({ text = "Cargando..." }) => (
  <div className="pixel-loader" role="status">
    <span className="pixel-spinner" aria-hidden="true" />
    <span>{text}</span>
  </div>
);

export default PixelLoader;
