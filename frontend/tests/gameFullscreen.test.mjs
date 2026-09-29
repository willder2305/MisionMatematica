import assert from "node:assert/strict";
import test from "node:test";
import {
  debeMostrarAvisoSalidaFullscreen,
  esViewportLandscape,
  obtenerApiFullscreen,
  resolverModoFullscreen,
} from "../src/utils/gameFullscreen.mjs";

test("sin API nativa el juego usa pseudo-fullscreen y no genera una alerta", () => {
  const api = obtenerApiFullscreen({ documentElement: {} });

  assert.equal(api.soportado, false);
  assert.equal(resolverModoFullscreen({ soportado: api.soportado, fullscreenNativoActivo: false }), "pseudo");
  assert.equal(debeMostrarAvisoSalidaFullscreen({
    juegoActivo: true,
    fullscreenNativoIngresado: false,
    fullscreenNativoAnterior: false,
    fullscreenNativoActivo: false,
    salidaIntencional: false,
  }), false);
});

test("un rechazo de fullscreen conserva el modo pseudo-fullscreen", () => {
  assert.equal(resolverModoFullscreen({ soportado: true, fullscreenNativoActivo: false }), "pseudo");
});

test("la alerta solo se muestra después de una salida real de fullscreen nativo", () => {
  assert.equal(debeMostrarAvisoSalidaFullscreen({
    juegoActivo: true,
    fullscreenNativoIngresado: true,
    fullscreenNativoAnterior: true,
    fullscreenNativoActivo: false,
    salidaIntencional: false,
  }), true);
  assert.equal(debeMostrarAvisoSalidaFullscreen({
    juegoActivo: true,
    fullscreenNativoIngresado: true,
    fullscreenNativoAnterior: true,
    fullscreenNativoActivo: false,
    salidaIntencional: true,
  }), false);
});

test("landscape se reconoce por media query o dimensiones visibles", () => {
  assert.equal(esViewportLandscape({ coincideMedia: true, ancho: 440, alto: 956 }), true);
  assert.equal(esViewportLandscape({ coincideMedia: false, ancho: 956, alto: 440 }), true);
  assert.equal(esViewportLandscape({ coincideMedia: false, ancho: 440, alto: 956 }), false);
});
