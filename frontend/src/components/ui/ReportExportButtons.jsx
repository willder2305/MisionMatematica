import React from "react";

/**
 * Botones reutilizables para descargar reportes filtrados.
 * Bloquea acciones duplicadas mientras el backend genera el archivo.
 */
const ReportExportButtons = ({ cargando, onExportar }) => (
  <div className="report-export-actions">
    <button type="button" disabled={cargando} onClick={() => onExportar("pdf")}>
      {cargando === "pdf" ? "Generando PDF..." : "Exportar PDF"}
    </button>
    <button type="button" className="secondary" disabled={cargando} onClick={() => onExportar("xlsx")}>
      {cargando === "xlsx" ? "Generando Excel..." : "Exportar Excel"}
    </button>
  </div>
);

export default ReportExportButtons;
