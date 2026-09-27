import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const stylesPath = new URL("../src/styles.css", import.meta.url);
const configPath = new URL("../src/config/personajesConfig.js", import.meta.url);

test("el sprite parte del origen del stage antes de aplicar translate3d", async () => {
  const css = await readFile(stylesPath, "utf8");
  const regla = css.match(/\.character-position\s*\{([^}]*)\}/);

  assert.ok(regla, "Debe existir la regla de posicionamiento del personaje.");
  assert.match(regla[1], /left:\s*0;/, "El origen horizontal debe ser el stage, no la posición estática posterior al mapa.");
  assert.match(regla[1], /top:\s*0;/, "El origen vertical debe ser el stage, no la posición estática posterior al mapa.");
  assert.match(regla[1], /position:\s*absolute;/);
  assert.match(regla[1], /z-index:\s*5;/);
});

test("la configuración exige frame inicial y secuencias completas para cada personaje", async () => {
  const config = await readFile(configPath, "utf8");

  assert.match(config, /export const validarPersonajesConfig/);
  assert.match(config, /validarAsset\(personajeKey, "el frame inicial", config\.idle\)/);
  assert.match(config, /\["correcto", "error"\]/);
  assert.match(config, /validarPersonajesConfig\(\);/);
});
