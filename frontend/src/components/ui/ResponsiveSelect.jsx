import React, { Children, useEffect, useId, useMemo, useRef, useState } from "react";

/**
 * Selector responsive reutilizable.
 * Mantiene las opciones dentro del viewport y conserva la firma onChange de un select nativo.
 */
const ResponsiveSelect = ({ children, className = "", disabled = false, name, onChange, value, ...props }) => {
  const [abierto, setAbierto] = useState(false);
  const [abrirArriba, setAbrirArriba] = useState(false);
  const [indiceActivo, setIndiceActivo] = useState(-1);
  const contenedorRef = useRef(null);
  const botonRef = useRef(null);
  const idLista = useId();

  const opciones = useMemo(() => {
    const extraer = (nodos, grupo = "") => Children.toArray(nodos).flatMap((nodo) => {
      if (!React.isValidElement(nodo)) return [];
      if (nodo.type === "optgroup") return extraer(nodo.props.children, nodo.props.label || "");
      if (nodo.type !== "option") return [];
      return [{
        disabled: Boolean(nodo.props.disabled),
        etiqueta: nodo.props.children,
        grupo,
        valor: String(nodo.props.value ?? nodo.props.children ?? ""),
      }];
    });
    return extraer(children);
  }, [children]);

  const seleccionada = opciones.find((opcion) => opcion.valor === String(value ?? ""));
  const etiqueta = seleccionada?.etiqueta || opciones.find((opcion) => opcion.valor === "")?.etiqueta || "Seleccione una opción";

  /** Selecciona una opción y emite un evento compatible con formularios existentes. */
  const seleccionar = (opcion) => {
    if (opcion.disabled) return;
    onChange?.({ target: { name, value: opcion.valor } });
    setAbierto(false);
    botonRef.current?.focus();
  };

  /** Calcula si el panel debe abrir hacia arriba antes de mostrarlo. */
  const alternar = () => {
    if (disabled) return;
    if (!abierto && botonRef.current) {
      const espacioInferior = window.innerHeight - botonRef.current.getBoundingClientRect().bottom;
      setAbrirArriba(espacioInferior < 260);
      setIndiceActivo(Math.max(0, opciones.findIndex((opcion) => opcion.valor === String(value ?? ""))));
    }
    setAbierto((actual) => !actual);
  };

  /** Maneja teclado para navegar el selector sin usar el ratón. */
  const manejarTeclado = (evento) => {
    if (disabled) return;
    const habilitadas = opciones.map((opcion, indice) => (!opcion.disabled ? indice : -1)).filter((indice) => indice >= 0);
    if (["ArrowDown", "ArrowUp"].includes(evento.key)) {
      evento.preventDefault();
      if (!abierto) {
        alternar();
        return;
      }
      const posicion = habilitadas.indexOf(indiceActivo);
      const siguiente = evento.key === "ArrowDown"
        ? habilitadas[Math.min(posicion + 1, habilitadas.length - 1)]
        : habilitadas[Math.max(posicion - 1, 0)];
      setIndiceActivo(siguiente);
    }
    if (["Enter", " "].includes(evento.key)) {
      evento.preventDefault();
      if (abierto && opciones[indiceActivo]) seleccionar(opciones[indiceActivo]);
      else alternar();
    }
    if (evento.key === "Escape") {
      setAbierto(false);
      botonRef.current?.focus();
    }
  };

  useEffect(() => {
    const cerrarAlExterior = (evento) => {
      if (!contenedorRef.current?.contains(evento.target)) setAbierto(false);
    };
    document.addEventListener("pointerdown", cerrarAlExterior);
    return () => document.removeEventListener("pointerdown", cerrarAlExterior);
  }, []);

  return (
    <div ref={contenedorRef} className={`responsive-select ${className} ${abierto ? "is-open" : ""}`}>
      <button
        {...props}
        ref={botonRef}
        type="button"
        className="responsive-select-trigger"
        disabled={disabled}
        aria-controls={idLista}
        aria-expanded={abierto}
        aria-haspopup="listbox"
        onClick={alternar}
        onKeyDown={manejarTeclado}
      >
        <span>{etiqueta}</span><span aria-hidden="true">⌄</span>
      </button>
      {abierto && (
        <div id={idLista} className={`responsive-select-options ${abrirArriba ? "open-up" : ""}`} role="listbox" aria-label={props["aria-label"] || name}>
          {opciones.map((opcion, indice) => (
            <React.Fragment key={`${opcion.grupo}-${opcion.valor}-${indice}`}>
              {opcion.grupo && (indice === 0 || opciones[indice - 1]?.grupo !== opcion.grupo) && <span className="responsive-select-group">{opcion.grupo}</span>}
              <button
                type="button"
                className={opcion.valor === String(value ?? "") ? "selected" : ""}
                disabled={opcion.disabled}
                role="option"
                aria-selected={opcion.valor === String(value ?? "")}
                tabIndex={indice === indiceActivo ? 0 : -1}
                onMouseEnter={() => setIndiceActivo(indice)}
                onClick={() => seleccionar(opcion)}
              >
                {opcion.etiqueta}
              </button>
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResponsiveSelect;
