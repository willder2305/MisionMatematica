import bosqueAsset from "../assets/juego/escenarios/escenario_1_base_1983x793.png";
import mapa2Asset from "../assets/juego/escenarios/escenario_2_alineado_1983x793.png";
import mapa3Asset from "../assets/juego/escenarios/escenario_3_alineado_1983x793.png";
import espacioAsset from "../assets/juego/recompensas/escenarios/escenario_4_espacio_1983x793.png";
import castilloAsset from "../assets/juego/recompensas/escenarios/escenario_5_castillo_magico_1983x793.png";
import baloncestoAsset from "../assets/juego/recompensas/escenarios/escenario_6_baloncesto_1983x793.png";
import marinoAsset from "../assets/juego/recompensas/escenarios/escenario_7_fondo_marino_1983x793.png";
import atardecerAsset from "../assets/juego/recompensas/escenarios/escenario_8_cielo_atardecer_1983x793.png";
import cristalesAsset from "../assets/juego/recompensas/escenarios/escenario_9_cueva_cristales_1983x793.png";

export const MAPA_PREDETERMINADO = "bosque";
export const DEBUG_POSITIONS = false;
export const MAP_BASE_WIDTH = 1983;
export const MAP_BASE_HEIGHT = 793;

const crearCasillasAlineadas = () => ({
  0: { tile: 0, x: 78, y: 480 },
  1: { tile: 1, x: 140, y: 480 },
  2: { tile: 2, x: 320, y: 480 },
  3: { tile: 3, x: 512, y: 480 },
  4: { tile: 4, x: 704, y: 480 },
  5: { tile: 5, x: 896, y: 480 },
  6: { tile: 6, x: 1088, y: 480 },
  7: { tile: 7, x: 1280, y: 480 },
  8: { tile: 8, x: 1464, y: 480 },
  9: { tile: 9, x: 1648, y: 480 },
  10: { tile: 10, x: 1830, y: 480 },
});

const crearMapa = (id, nombre, asset, inicial = false) => ({
  id,
  nombre,
  asset,
  inicial,
  // Cada escenario conserva sus casillas propias y alineadas en el lienzo real 1983x793.
  casillas: crearCasillasAlineadas(),
});

export const mapasConfig = {
  bosque: crearMapa("bosque", "Bosque inicial", bosqueAsset, true),
  mapa_2: crearMapa("mapa_2", "Desierto de pirámides", mapa2Asset, true),
  mapa_3: crearMapa("mapa_3", "Montañas nevadas", mapa3Asset, true),
  mapa_4_espacio: crearMapa("mapa_4_espacio", "Misión espacial", espacioAsset),
  mapa_5_castillo_magico: crearMapa("mapa_5_castillo_magico", "Castillo mágico", castilloAsset),
  mapa_6_baloncesto: crearMapa("mapa_6_baloncesto", "Cancha de baloncesto", baloncestoAsset),
  mapa_7_fondo_marino: crearMapa("mapa_7_fondo_marino", "Fondo marino", marinoAsset),
  mapa_8_cielo_atardecer: crearMapa("mapa_8_cielo_atardecer", "Cielo al atardecer", atardecerAsset),
  mapa_9_cueva_cristales: crearMapa("mapa_9_cueva_cristales", "Cueva de cristales", cristalesAsset),
};

export const MAPAS_DISPONIBLES = Object.keys(mapasConfig);

export const obtenerMapaConfig = (mapaId) => mapasConfig[mapaId] || mapasConfig[MAPA_PREDETERMINADO];

// Devuelve el punto de apoyo del personaje dentro del mapa solicitado.
export const obtenerPosicionCasilla = (mapaId, numeroCasilla) => {
  const mapa = obtenerMapaConfig(mapaId);
  const casilla = mapa.casillas[Number(numeroCasilla)] || mapa.casillas[0];
  return { ...casilla };
};

export const obtenerPosicionesDebug = (mapaId = MAPA_PREDETERMINADO) => (
  Object.values(obtenerMapaConfig(mapaId).casillas)
    .filter((posicion) => posicion.tile > 0)
    .map((posicion) => ({ ...posicion }))
);
