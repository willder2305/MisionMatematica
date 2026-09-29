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

test("el modal de explicación conserva cabecera y pie, con scroll solo en su contenido", async () => {
  const [page, css] = await Promise.all([
    readFile(pagePath, "utf8"),
    readFile(stylesPath, "utf8"),
  ]);

  assert.match(page, /className="game-explanation-header"/);
  assert.match(page, /className="game-explanation-content" ref=\{contenidoExplicacionRef\}/);
  assert.match(page, /className="game-explanation-footer"/);
  assert.match(page, /scrollTo\(\{ top: 0, behavior: "auto" \}\)/);
  assert.match(page, /onClick=\{cerrarExplicacion\} autoFocus/);
  assert.match(page, /if \(cierreExplicacionRef\.current\)/);
  assert.match(css, /\.game-explanation-panel\s*\{[\s\S]*?display:\s*flex;[\s\S]*?flex-direction:\s*column;/);
  assert.match(css, /\.game-explanation-panel\s*\{[\s\S]*?position:\s*fixed;[\s\S]*?max-height:\s*min\(90dvh, calc\(100dvh - 1rem\)\);/);
  assert.match(css, /\.game-explanation-content\s*\{[\s\S]*?min-height:\s*0;[\s\S]*?overflow-y:\s*auto;/);
  assert.match(css, /\.game-explanation-footer\s*\{\s*background:\s*#fffef1;\s*\}/);
});
