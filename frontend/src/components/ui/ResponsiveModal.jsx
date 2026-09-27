import React, { useEffect } from "react";

/**
 * Modal pixel-art reutilizable con cierre por Escape y clic en el fondo.
 * Mantiene el contenido accesible dentro de pantallas verticales y horizontales.
 */
const ResponsiveModal = ({ abierto, children, onCerrar, titulo }) => {
  useEffect(() => {
    if (!abierto) return undefined;
    const cerrarConEscape = (evento) => {
      if (evento.key === "Escape") onCerrar?.();
    };
    window.addEventListener("keydown", cerrarConEscape);
    return () => window.removeEventListener("keydown", cerrarConEscape);
  }, [abierto, onCerrar]);

  if (!abierto) return null;
  return (
    <div className="responsive-modal-backdrop" role="presentation" onMouseDown={onCerrar}>
      <section className="responsive-modal" role="dialog" aria-modal="true" aria-label={titulo} onMouseDown={(evento) => evento.stopPropagation()}>
        {children}
      </section>
    </div>
  );
};

export default ResponsiveModal;
