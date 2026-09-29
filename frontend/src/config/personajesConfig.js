import femeninoSeleccion from "../assets/juego/sprits/sprit F1/S1Venfrente.png";
import femeninoIdle from "../assets/juego/sprits/sprit F1/S1Vlateral.png";
import masculinoSeleccion from "../assets/juego/sprits/sprit M1/S1Venfrente.png";
import masculinoIdle from "../assets/juego/sprits/sprit M1/S1Vlateral.png";

const assetsRecompensas = import.meta.glob("../assets/juego/recompensas/personajes/**/*.png", {
  eager: true,
  import: "default",
  query: "?url",
});
const assetsBase = import.meta.glob("../assets/juego/sprits/**/*.png", { eager: true, import: "default", query: "?url" });

const assetRecompensa = (ruta) => assetsRecompensas[`../assets/juego/recompensas/personajes/${ruta}`];
const assetBase = (ruta) => assetsBase[`../assets/juego/sprits/${ruta}`];
const secuenciaRecompensa = (carpeta, tipo) => Array.from({ length: 6 }, (_, indice) => assetRecompensa(`${carpeta}/${tipo}/${indice + 1}.png`));
const secuenciaBase = (carpeta) => Array.from({ length: 6 }, (_, indice) => assetBase(`${carpeta}/${indice + 1}.png`));
const vistas = (carpeta, frente, lateral, trasera) => [
  assetRecompensa(`${carpeta}/${frente}`),
  assetRecompensa(`${carpeta}/${lateral}`),
  assetRecompensa(`${carpeta}/${trasera}`),
];

const SPRITE_BOX = { width: "clamp(104px, 18vw, 225px)", height: "clamp(72px, 12vw, 150px)" };
const FRAME_OFFSET_NEUTRO = { x: 0, y: 0 };

const crearPersonaje = (id, nombre, vistasTienda, correcto, error, inicial = false) => ({
  id,
  nombre,
  inicial,
  seleccion: vistasTienda[0],
  vistas: vistasTienda,
  feetAnchor: { x: 0.5, y: 0.96 },
  spriteBox: SPRITE_BOX,
  idle: vistasTienda[1] || vistasTienda[0],
  correcto,
  error,
});

export const personajesConfig = {
  masculino: crearPersonaje("masculino", "Explorador", [masculinoSeleccion, masculinoIdle, masculinoSeleccion],
    secuenciaBase("sprit M1/movimiento/moviientosprits/movimiento acierto"),
    secuenciaBase("sprit M1/movimiento/moviientosprits/movimiento error"), true),
  femenino: crearPersonaje("femenino", "Exploradora", [femeninoSeleccion, femeninoIdle, femeninoSeleccion],
    secuenciaBase("sprit F1/movimiento/movimiento correcto"),
    secuenciaBase("sprit F1/movimiento/movimiento error"), true),
  angel: crearPersonaje("angel", "Ángel", vistas("angel", "V enfrente.png", "V lateral.png", "V trasera.png"), secuenciaRecompensa("angel", "correcta"), secuenciaRecompensa("angel", "error")),
  astronauta: crearPersonaje("astronauta", "Astronauta", vistas("astronauta", "V enfrente.png", "V lateral.png", "V trasera.png"), secuenciaRecompensa("astronauta", "correcto"), secuenciaRecompensa("astronauta", "error")),
  basketman: crearPersonaje("basketman", "Basket Man", vistas("BasketMan", "v efrente.png", "v lateral.png", "v trasera.png"), secuenciaRecompensa("BasketMan", "correcta"), secuenciaRecompensa("BasketMan", "error")),
  princesa: crearPersonaje("princesa", "Princesa", vistas("princesa", "v enfrete.png", "v lado.png", "v trasera.png"), secuenciaRecompensa("princesa", "correcta"), secuenciaRecompensa("princesa", "error")),
  rey_pulpo: crearPersonaje("rey_pulpo", "Rey Pulpo", vistas("Rey pulpo", "V efrente.png", "V lateral.png", "V trasera.png"), secuenciaRecompensa("Rey pulpo", "correcta"), secuenciaRecompensa("Rey pulpo", "error")),
  topo: crearPersonaje("topo", "Topo", vistas("topo", "V enfrente.png", "V lateral.png", "V trasera.png"), secuenciaRecompensa("topo", "correcta"), secuenciaRecompensa("topo", "error")),
};

const validarAsset = (personajeKey, tipo, asset) => {
  if (typeof asset !== "string" || !asset.trim()) {
    throw new Error(`El personaje '${personajeKey}' no tiene un asset válido para ${tipo}.`);
  }
};

/** Verifica que cada personaje activo pueda mostrarse antes de iniciar una partida. */
export const validarPersonajesConfig = () => {
  Object.entries(personajesConfig).forEach(([personajeKey, config]) => {
    validarAsset(personajeKey, "el frame inicial", config.idle);
    ["correcto", "error"].forEach((tipo) => {
      const frames = config[tipo];
      if (!Array.isArray(frames) || !frames.length) {
        throw new Error(`El personaje '${personajeKey}' no tiene frames de ${tipo}.`);
      }
      frames.forEach((frame, indice) => validarAsset(personajeKey, `${tipo} #${indice + 1}`, frame));
    });
  });
};

// No se permite iniciar con un personaje activo cuyos assets estén incompletos.
validarPersonajesConfig();

export const obtenerPersonajeConfig = (personajeId) => {
  const config = personajesConfig[personajeId];
  if (config) {
    return config;
  }
  if (personajeId) {
    console.error(`Personaje no reconocido en preferencias: '${personajeId}'. Se usa el starter de respaldo.`);
  }
  return personajesConfig.masculino;
};

export const normalizarFramePersonaje = (frame) => {
  if (typeof frame === "string") return { src: frame, offset: FRAME_OFFSET_NEUTRO, feetAnchor: null };
  return { src: frame.src, offset: frame.offset || { x: frame.offsetX || 0, y: frame.offsetY || 0 }, feetAnchor: frame.feetAnchor || null };
};

export const obtenerFrameActual = (personajeConfig, tipoAnimacion, frameIndex) => {
  const secuenciaActual = personajeConfig[tipoAnimacion] || [];
  const frameBase = tipoAnimacion === "idle" ? personajeConfig.idle : secuenciaActual[frameIndex % secuenciaActual.length] || personajeConfig.idle;
  return normalizarFramePersonaje(frameBase);
};

/** Reúne las vistas y secuencias del personaje para dejarlas disponibles antes de animar. */
export const obtenerAssetsPrecargaPersonaje = (personajeId) => {
  const config = obtenerPersonajeConfig(personajeId);
  return [...config.vistas, config.idle, ...config.correcto, ...config.error]
    .filter(Boolean)
    .map((frame) => normalizarFramePersonaje(frame).src)
    .filter((src, indice, lista) => typeof src === "string" && lista.indexOf(src) === indice);
};
