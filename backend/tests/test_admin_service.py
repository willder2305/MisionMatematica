import unittest

from services.admin_service import _entero, _json_para_db, _validar_ejercicio, _validar_tema


class AdminServiceTest(unittest.TestCase):
    def test_entero_valida_campo_requerido(self):
        errores = {}
        self.assertIsNone(_entero("", "id_tema", errores))
        self.assertIn("id_tema", errores)

    def test_json_para_db_acepta_texto_json(self):
        errores = {}
        self.assertEqual(_json_para_db('{"min": 1}', errores), {"min": 1})
        self.assertEqual(errores, {})

    def test_validar_tema_requiere_nombre(self):
        _, errores = _validar_tema({"id_grado": 1, "nombre_tema": "", "estado": "activo"})
        self.assertIn("nombre_tema", errores)

    def test_validar_ejercicio_seleccion_multiple_requiere_respuesta_en_opciones(self):
        _, errores = _validar_ejercicio({
            "id_tema": 1,
            "id_nivel": 1,
            "enunciado": "Cuanto es 2 + 2?",
            "tipo_respuesta": "seleccion_multiple",
            "respuesta_correcta": "4",
            "opciones": ["3", "5"],
            "estado": "publicado",
        })
        self.assertIn("respuesta_correcta", errores)


if __name__ == "__main__":
    unittest.main()
