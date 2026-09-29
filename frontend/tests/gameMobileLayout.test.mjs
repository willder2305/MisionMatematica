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

test("el modo móvil horizontal reserva una fila para los controles", async () => {
  const css = await readFile(stylesPath, "utf8");

  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 600px\)/);
  assert.match(css, /--game-controls-height:\s*clamp\(108px, 28dvh, 124px\)/);
  assert.match(css, /grid-template-rows:\s*minmax\(0, 1fr\) var\(--game-controls-height\)/);
  assert.match(css, /\.game-bottom-controls\s*\{[\s\S]*?position:\s*static;/);
});
