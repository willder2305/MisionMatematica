import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [appSource, loginSource, helpSource] = await Promise.all([
  readFile(new URL("../src/main.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/pages/LoginPage.jsx", import.meta.url), "utf8"),
  readFile(new URL("../src/pages/HelpPage.jsx", import.meta.url), "utf8"),
]);

test("la ayuda es una ruta pública que conserva las sesiones activas", () => {
  assert.match(appSource, /"\/ayuda"/);
  assert.match(appSource, /rutaActual === "\/ayuda"/);
  assert.match(appSource, /<HelpPage \/>/);
});

test("el acceso del inicio abre la ayuda en una pestaña distinta", () => {
  assert.match(loginSource, /window\.open\("\/ayuda", "_blank", "noopener,noreferrer"\)/);
  assert.match(loginSource, /Ayuda/);
});

test("los recursos de ayuda apuntan a los tutoriales y manual solicitados", () => {
  assert.match(helpSource, /kCkCNJFPMeM/);
  assert.match(helpSource, /y4ZmzUGkFp0/);
  assert.match(helpSource, /Manual_Usuario_Mision_Matematica\.pdf/);
  assert.match(helpSource, /youtube-nocookie\.com\/embed/);
});
