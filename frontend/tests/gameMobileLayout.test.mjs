import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pagePath = new URL("../src/pages/JuegoPage.jsx", import.meta.url);
const panelPath = new URL("../src/components/juego/QuestionPanel.jsx", import.meta.url);
const stylesPath = new URL("../src/styles.css", import.meta.url);

test("los controles del juego se renderizan fuera del tablero", async () => {
  const [page, panel] = await Promise.all([
    readFile(pagePath, "utf8"),
    readFile(panelPath, "utf8"),
  ]);

  assert.match(panel, /export const GameBottomControls/);
  assert.match(page, /<\/GameBoard>\s*<GameBottomControls/s);
});

test("el modo móvil horizontal usa un HUD compacto sobre la zona decorativa", async () => {
  const css = await readFile(stylesPath, "utf8");

  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 600px\)/);
  assert.match(css, /grid-template-rows:\s*minmax\(0, 1fr\);/);
  assert.match(css, /\.game-bottom-controls\s*\{[\s\S]*?position:\s*absolute;/);
  assert.match(css, /width:\s*62vw;/);
  assert.match(css, /background:\s*rgba\(255, 253, 248, 0\.84\)/);
  assert.doesNotMatch(css, /--game-controls-height/);
});
