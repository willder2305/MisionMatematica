/**
 * Deriva el estado visual desde el contrato de inventario confirmado por Flask.
 * Ninguna pantalla usa índice de carrusel ni nombre visible para decidir propiedad.
 */
export const getCharacterOwnershipState = (character) => {
  if (!character) return "unavailable";
  if (character.seleccionado) return "selected";
  if (character.adquirido || character.desbloqueado || character.es_inicial) return "owned";
  return "locked";
};

/** Mantiene el filtro de inventario alineado con el mismo estado usado por Tienda. */
export const isCharacterOwned = (character) => getCharacterOwnershipState(character) !== "locked";
