const LABELS = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
  activo: "Activo",
  activa: "Activa",
  inactivo: "Inactivo",
  inactiva: "Inactiva",
  bloqueado: "Bloqueado",
  pendiente: "Pendiente",
  en_progreso: "En progreso",
  completada: "Completada",
  completado: "Completado",
  abandonada: "Abandonada",
  sin_vidas: "Sin vidas",
  esperando_continuacion: "Esperando continuación",
  requiere_revision: "Requiere revisión",
  pendiente_revision: "Pendiente de revisión",
  borrador: "Borrador",
  pausada: "Pausada",
  finalizada: "Finalizada",
  cancelada: "Cancelada",
  publicado: "Publicado",
  publicada: "Publicada",
  desactivado: "Desactivado",
  desactivada: "Desactivada",
  respuesta_correcta: "Respuesta correcta",
  saldo_monedas: "Monedas",
  recompensa_partida: "Recompensa por partida",
  recompensa_partida_perfecta: "Recompensa por partida perfecta",
  continuar_partida: "Continuación de partida",
  compra_personaje: "Compra de personaje",
  compra_mapa: "Compra de mapa",
  generacion_automatica: "Generación automática",
  ejercicios_especificos: "Ejercicios específicos",
  numerica: "Numérica",
  seleccion_multiple: "Selección múltiple",
  facil: "Fácil",
  intermedio: "Intermedio",
  dificil: "Difícil",
  suma: "Suma",
  resta: "Resta",
  multiplicacion: "Multiplicación",
  division: "División",
  potencias: "Potencias",
  potencia: "Potencias",
  raiz_cuadrada: "Raíz cuadrada",
  operaciones_combinadas: "Operaciones combinadas",
  suma_fracciones: "Suma de fracciones",
  resta_fracciones: "Resta de fracciones",
  multiplicacion_fracciones: "Multiplicación de fracciones",
  division_fracciones: "División de fracciones",
  suma_decimales: "Suma de decimales",
  resta_decimales: "Resta de decimales",
  multiplicacion_decimales: "Multiplicación de decimales",
  division_decimales: "División de decimales",
  porcentaje: "Porcentajes",
  regla_tres_directa: "Regla de tres directa",
  regla_tres_inversa: "Regla de tres inversa",
  operaciones_combinadas_fracciones: "Operaciones combinadas de fracciones",
  conversion_fracciones: "Conversiones de fracciones",
  conversiones_fracciones: "Conversiones de fracciones",
  geometria: "Geometría",
  area: "Área",
  perimetro: "Perímetro",
  rectangulo: "Rectángulo",
  triangulo: "Triángulo",
  circulo: "Círculo",
  poligono_regular: "Polígono regular",
  poligonos_regulares: "Polígonos regulares",
  cuadrado: "Cuadrado",
  rombo: "Rombo",
  seccion_unica: "Sección única",
  propia: "Propia",
  ocupada: "Ocupada",
  disponible: "Disponible",
  exitoso: "Exitoso",
  fallido: "Fallido",
  mantener: "Mantener",
  aumentar: "Aumentar",
  reducir: "Reducir",
  reforzar: "Reforzar",
  institucional: "Institucional",
  independiente: "Independiente",
  cuenta_propia: "Cuenta propia",
  grupo_educativo: "Grupo educativo",
  personal: "Juego personal",
  asignacion: "Actividad asignada",
  plantilla_generadora: "Plantilla generadora",
  ejercicio_fijo: "Ejercicio fijo",
  archivo_importado: "Archivo importado",
  grado_anterior: "Grado anterior",
  grado_nuevo: "Grado nuevo",
  dificultad_anterior: "Dificultad anterior",
  dificultad_nueva: "Dificultad nueva",
  motivo_cambio: "Motivo del cambio",
  fecha_creacion: "Fecha de creación",
  fecha_modificacion: "Fecha de modificación",
  ultima_actividad: "Última actividad",
  tipo_contexto: "Contexto",
  true: "Sí",
  false: "No",
};

/** Convierte valores técnicos de la API en etiquetas claras sin modificar el dato original. */
export const formatLabel = (value, fallback = "Sin información") => {
  if (value === null || value === undefined || value === "") return fallback;

  const key = String(value).trim().toLowerCase();
  if (LABELS[key]) return LABELS[key];

  return key
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .replace(/^./, (character) => character.toUpperCase());
};

/** Formatea fechas de la API para tablas sin exponer marcas de tiempo técnicas. */
export const formatDateTime = (value, fallback = "Sin datos") => {
  if (!value) return fallback;

  const normalized = String(value).trim().replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return fallback;

  const includesTime = /T\d{2}:\d{2}/.test(normalized);
  return new Intl.DateTimeFormat("es-GT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(includesTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(date);
};

/** Devuelve un texto con plural correcto para cantidades mostradas al usuario. */
export const pluralize = (quantity, singular, plural = `${singular}s`) => (
  `${quantity} ${Number(quantity) === 1 ? singular : plural}`
);

export const UI_LABELS = LABELS;
