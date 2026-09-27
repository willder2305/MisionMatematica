import React from "react";

/**
 * Funcion: PixelAlert
 *
 * Descripcion:
 * Muestra mensajes de exito o error con estilo pixel-art sin ocultar errores reales de API.
 *
 * Es llamada desde:
 * SeccionesPage.jsx y GradosPage.jsx cuando existe mensaje visible.
 *
 * Llama a:
 * No llama funciones externas; renderiza el texto recibido.
 *
 * Parametros:
 * tipo y texto del mensaje.
 *
 * Retorna:
 * Un bloque accesible con icono textual y mensaje.
 *
 * Manejo de errores:
 * Si texto esta vacio, retorna null para no ocupar espacio en la interfaz.
 */
const PixelAlert = ({ tipo, texto }) => {
  if (!texto) {
    return null;
  }

  return (
    <div className={`pixel-alert ${tipo}`} role={tipo === "error" ? "alert" : "status"}>
      <span className="alert-icon" aria-hidden="true">
        {tipo === "error" ? "!" : "OK"}
      </span>
      <span>{texto}</span>
    </div>
  );
};

export default PixelAlert;
