import unittest
from pathlib import Path

from services.personalizacion_service import calcular_recompensa_partida


ROOT = Path(__file__).resolve().parents[2]


def partida_base(**cambios):
    partida = {
        "estado": "completada",
        "total_correctos": 10,
        "casilla_actual": 10,
        "total_errores": 0,
        "vidas_perdidas_total": 0,
        "continuaciones_compradas": 0,
    }
    partida.update(cambios)
    return partida


class RecompensasMonedasTest(unittest.TestCase):
    def setUp(self):
        self.migracion = (ROOT / "database" / "actualizar_personalizacion_tienda.sql").read_text(encoding="utf-8")
        self.juego = (ROOT / "backend" / "services" / "juego_adaptativo_service.py").read_text(encoding="utf-8")
        self.monedas = (ROOT / "backend" / "services" / "personalizacion_service.py").read_text(encoding="utf-8")

    def test_estudiante_nuevo_empieza_sin_monedas(self):
        self.assertIn("INSERT IGNORE INTO monederos (id_usuario, saldo_monedas) VALUES (%s, 0)", self.monedas)
        self.assertIn("saldo_monedas INT NOT NULL DEFAULT 0", self.migracion)

    def test_victoria_normal_acredita_una_moneda(self):
        recompensa = calcular_recompensa_partida(partida_base(total_errores=1, vidas_perdidas_total=1))
        self.assertEqual(recompensa["tipo"], "normal")
        self.assertEqual(recompensa["monedas_ganadas"], 1)

    def test_victoria_perfecta_acredita_dos_no_tres(self):
        recompensa = calcular_recompensa_partida(partida_base())
        self.assertEqual(recompensa["tipo"], "perfecta")
        self.assertEqual(recompensa["monedas_ganadas"], 2)

    def test_error_o_continuacion_elimina_elegibilidad_perfecta(self):
        self.assertEqual(calcular_recompensa_partida(partida_base(vidas_perdidas_total=1))["monedas_ganadas"], 1)
        self.assertEqual(calcular_recompensa_partida(partida_base(continuaciones_compradas=1))["monedas_ganadas"], 1)

    def test_partida_incompleta_no_entrega_moneda(self):
        self.assertIsNone(calcular_recompensa_partida(partida_base(estado="sin_vidas", total_correctos=7, casilla_actual=7)))

    def test_migracion_y_servicio_protegen_idempotencia(self):
        self.assertIn("recompensa_otorgada", self.migracion)
        self.assertIn("uk_movimientos_request_id", self.migracion)
        self.assertIn("WHERE request_id = %s AND tipo = 'continuar_partida'", self.juego)
        self.assertIn("vidas_restantes = %s", self.juego)
        self.assertIn("continuaciones_compradas = continuaciones_compradas + 1", self.juego)


if __name__ == "__main__":
    unittest.main()
