import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PersonalizacionContractTest(unittest.TestCase):
    def setUp(self):
        self.migracion = (ROOT / "database" / "actualizar_personalizacion_tienda.sql").read_text(encoding="utf-8")
        self.rutas = (ROOT / "backend" / "routes" / "estudiante_routes.py").read_text(encoding="utf-8")
        self.servicio = (ROOT / "backend" / "services" / "personalizacion_service.py").read_text(encoding="utf-8")
        self.juego = (ROOT / "backend" / "services" / "juego_adaptativo_service.py").read_text(encoding="utf-8")
        self.ejercicios = (ROOT / "backend" / "services" / "ejercicios_service.py").read_text(encoding="utf-8")

    def test_catalogo_separa_personajes_mapas_y_precios(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS tienda_items", self.migracion)
        self.assertIn("('personaje', 'angel', 'Ángel', 25, 0)", self.migracion)
        self.assertIn("('mapa', 'mapa_4_espacio', 'Mision espacial', 20, 0)", self.migracion)
        self.assertIn("CREATE TABLE IF NOT EXISTS monederos", self.migracion)
        self.assertIn("CREATE TABLE IF NOT EXISTS usuario_items", self.migracion)
        self.assertIn("CREATE TABLE IF NOT EXISTS movimientos_monedas", self.migracion)

    def test_compra_no_confia_en_precio_del_cliente(self):
        self.assertIn('datos.get("id_item")', self.rutas)
        self.assertNotIn('datos.get("precio")', self.rutas)
        self.assertIn("FOR UPDATE", self.servicio)
        self.assertIn("saldo_anterior < precio", self.servicio)
        self.assertIn("INSERT INTO usuario_items", self.servicio)
        self.assertIn('"compra_personaje"', self.servicio)
        self.assertIn('"compra_mapa"', self.servicio)

    def test_personaje_y_mapa_exigen_inventario(self):
        self.assertIn("def puede_usar_personaje", self.servicio)
        self.assertIn("puede_usar_personaje(id_usuario, personaje_key, cursor)", self.servicio)
        self.assertIn('"mapa", mapa_key', self.servicio)
        self.assertIn("resolver_personalizacion_partida", self.juego)
        self.assertNotIn('datos_limpios["personaje"]', self.juego)

    def test_respuesta_correcta_solo_regresa_tras_el_intento(self):
        self.assertIn('"respuesta_correcta": None if es_correcta else ejercicio.get("respuesta_correcta")', self.juego)
        self.assertIn('"explicacion_pasos": obtener_explicacion_pasos_ejercicio(ejercicio) if not es_correcta else None', self.juego)
        self.assertIn('"explicacion_pasos": obtener_explicacion_pasos_ejercicio(intento) if not intento["es_correcta"] else None', self.juego)
        self.assertIn("def obtener_explicacion_pasos_ejercicio(ejercicio):", self.ejercicios)


if __name__ == "__main__":
    unittest.main()
