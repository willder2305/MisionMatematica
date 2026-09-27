import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../src/constants/uiLabels.js", import.meta.url), "utf8");
const labels = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

test("las etiquetas técnicas conocidas se muestran en español", () => {
  assert.equal(labels.formatLabel("regla_tres_directa"), "Regla de tres directa");
  assert.equal(labels.formatLabel("operaciones_combinadas_fracciones"), "Operaciones combinadas de fracciones");
  assert.equal(labels.formatLabel("raiz_cuadrada"), "Raíz cuadrada");
  assert.equal(labels.formatLabel("en_progreso"), "En progreso");
  assert.equal(labels.formatLabel("pendiente_revision"), "Pendiente de revisión");
});

test("el respaldo elimina guiones bajos sin modificar el valor original", () => {
  const technicalValue = "estado_no_registrado";
  assert.equal(labels.formatLabel(technicalValue), "Estado no registrado");
  assert.equal(technicalValue, "estado_no_registrado");
});

test("las fechas de la API no se muestran como timestamps", () => {
  const formatted = labels.formatDateTime("2026-09-26T15:42:13");
  assert.match(formatted, /^26\/09\/2026/);
  assert.equal(labels.formatDateTime(null), "Sin datos");
});
