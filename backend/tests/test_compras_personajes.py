import unittest
from pathlib import Path
from unittest.mock import patch

from services.personalizacion_service import comprar_item_estudiante


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "backend" / "services" / "personalizacion_service.py"
MIGRACION = ROOT / "database" / "corregir_inventario_personajes.sql"
MIGRACION_BASE = ROOT / "database" / "actualizar_personalizacion_tienda.sql"
FRONTEND_STATE = ROOT / "frontend" / "src" / "utils" / "characterOwnership.js"


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_falso = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, dictionary=True):
        return self.cursor_falso

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


class CursorCompraFalsa:
    def __init__(self, propiedad=None, saldo=500):
        self.propiedad = propiedad
        self.saldo = saldo
        self.consultas = []

    def execute(self, consulta, parametros=None):
        self.consultas.append((" ".join(consulta.split()), parametros))

    def fetchone(self):
        consulta = self.consultas[-1][0]
        if "FROM tienda_items" in consulta:
            return {"id_item": 11, "tipo": "personaje", "item_key": "topo", "nombre": "Topo", "precio_monedas": 25}
        if "FROM usuario_items" in consulta:
            return self.propiedad
        return None

    def close(self):
        pass


class ComprasPersonajesTest(unittest.TestCase):
    usuario = {"id_usuario": 44, "rol": "estudiante"}

    def _comprar(self, propiedad=None, saldo=500):
        cursor = CursorCompraFalsa(propiedad=propiedad, saldo=saldo)
        conexion = ConexionFalsa(cursor)
        with patch("services.personalizacion_service.obtener_conexion", return_value=conexion), patch(
            "services.personalizacion_service.asegurar_estado_estudiante"
        ), patch(
            "services.personalizacion_service.bloquear_monedero_estudiante", return_value={"saldo_monedas": saldo}
        ), patch(
            "services.personalizacion_service._leer_personalizacion", return_value={"saldo_monedas": saldo - 25, "personajes": []}
        ), patch("services.personalizacion_service.registrar_movimiento_monedas") as movimiento:
            respuesta = comprar_item_estudiante(self.usuario, 11)
        return respuesta, cursor, conexion, movimiento

    def test_relacion_inactiva_se_reactiva_y_cobra_una_sola_vez(self):
        resultado, cursor, conexion, movimiento = self._comprar({"id_usuario_item": 9, "estado": "inactivo"})

        self.assertEqual(resultado[0], "consultado")
        self.assertIn("Topo ahora es tuyo", resultado[1])
        self.assertEqual(conexion.commits, 1)
        self.assertEqual(conexion.rollbacks, 0)
        self.assertTrue(any("UPDATE usuario_items SET estado = 'activo'" in consulta for consulta, _ in cursor.consultas))
        self.assertTrue(any("UPDATE monederos SET saldo_monedas = %s" in consulta for consulta, _ in cursor.consultas))
        movimiento.assert_called_once()
        self.assertEqual(movimiento.call_args.kwargs["cantidad"], -25)

    def test_personaje_activo_no_duplica_cobro_ni_inventario(self):
        resultado, cursor, conexion, movimiento = self._comprar({"id_usuario_item": 9, "estado": "activo"})

        self.assertEqual(resultado[0], "articulo_ya_adquirido")
        self.assertTrue(resultado[2]["resultado_compra"]["adquirido"])
        self.assertEqual(conexion.commits, 1)
        self.assertFalse(any("UPDATE monederos SET saldo_monedas = %s" in consulta for consulta, _ in cursor.consultas))
        self.assertFalse(any("INSERT INTO usuario_items" in consulta for consulta, _ in cursor.consultas))
        movimiento.assert_not_called()

    def test_saldo_insuficiente_no_modifica_inventario(self):
        resultado, cursor, conexion, movimiento = self._comprar(None, saldo=24)

        self.assertEqual(resultado[0], "datos_invalidos")
        self.assertEqual(conexion.commits, 0)
        self.assertEqual(conexion.rollbacks, 1)
        self.assertFalse(any("INSERT INTO usuario_items" in consulta for consulta, _ in cursor.consultas))
        movimiento.assert_not_called()

    def test_fuentes_y_contrato_mantienen_identidad_estable(self):
        servicio = SERVICE.read_text(encoding="utf-8")
        migracion = MIGRACION.read_text(encoding="utf-8")
        migracion_base = MIGRACION_BASE.read_text(encoding="utf-8")
        estado_frontend = FRONTEND_STATE.read_text(encoding="utf-8")

        self.assertIn("def _propiedad_item", servicio)
        self.assertIn("propiedad[\"estado\"] == \"activo\"", servicio)
        self.assertIn("articulo_ya_adquirido", servicio)
        self.assertIn("0xC3816E67656C", migracion)
        self.assertIn("getCharacterOwnershipState", estado_frontend)
        self.assertIn("character.adquirido", estado_frontend)

    def test_compra_serializa_peticiones_del_mismo_usuario(self):
        """El bloqueo de monedero y la restricción única impiden doble compra concurrente."""
        servicio = SERVICE.read_text(encoding="utf-8")
        migracion_base = MIGRACION_BASE.read_text(encoding="utf-8")

        self.assertIn("bloquear_monedero_estudiante(id_usuario, cursor)", servicio)
        self.assertIn("_propiedad_item(id_usuario, id_item, cursor, bloquear=True)", servicio)
        self.assertIn("uk_usuario_items_usuario_item UNIQUE (id_usuario, id_item)", migracion_base)


if __name__ == "__main__":
    unittest.main()
