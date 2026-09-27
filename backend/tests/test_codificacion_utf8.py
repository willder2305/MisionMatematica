"""Pruebas de extremo a extremo ligero para la conservación de texto UTF-8."""

import os
import unittest

from app import crear_app
from db import obtener_conexion
from scripts.corregir_mojibake_utf8 import recuperar_latin1_utf8


TEXTO_PRUEBA = "Ángel — División — Raíz cuadrada — ¿Cómo se resuelve?"


class CodificacionUtf8Test(unittest.TestCase):
    def test_recupera_solo_el_patron_latin1_utf8_confirmado(self):
        danado = "Â¿CuÃ¡nto es 6 / 2?"
        correcto = "¿Cuánto es 6 / 2?"

        self.assertEqual(recuperar_latin1_utf8(danado), correcto)
        self.assertEqual(recuperar_latin1_utf8(correcto), correcto)

    def test_json_flask_conserva_unicode_sin_escape_ascii(self):
        app = crear_app()
        with app.app_context():
            respuesta = app.json.response({"enunciado": "¿Cuánto es 6 / 2?"})

        self.assertEqual(respuesta.mimetype, "application/json")
        self.assertEqual(respuesta.get_json()["enunciado"], "¿Cuánto es 6 / 2?")
        self.assertIn("¿Cuánto es 6 / 2?".encode("utf-8"), respuesta.data)


@unittest.skipUnless(os.getenv("RUN_DB_UTF8_INTEGRATION") == "1", "requiere MySQL de integración")
class CodificacionUtf8BaseDatosTest(unittest.TestCase):
    def test_roundtrip_mysql_usa_utf8mb4(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT @@character_set_client, @@character_set_connection, @@character_set_results")
            self.assertEqual(cursor.fetchone(), ("utf8mb4", "utf8mb4", "utf8mb4"))
            cursor.execute("CREATE TEMPORARY TABLE qa_utf8 (texto VARCHAR(255) CHARACTER SET utf8mb4 NOT NULL)")
            cursor.execute("INSERT INTO qa_utf8 (texto) VALUES (%s)", (TEXTO_PRUEBA,))
            cursor.execute("SELECT texto FROM qa_utf8")
            self.assertEqual(cursor.fetchone()[0], TEXTO_PRUEBA)
        finally:
            cursor.close()
            conexion.close()


if __name__ == "__main__":
    unittest.main()
