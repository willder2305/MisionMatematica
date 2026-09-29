import unittest

from services.puntuaciones_service import (
    PUNTOS_POR_ACIERTO,
    _consulta_clasificacion,
    acreditar_puntuacion_tema,
    obtener_clasificacion_estudiante,
    puntos_por_aciertos,
)


class CursorPuntuacionFake:
    """Captura consultas SQL para verificar contrato y orden de parámetros."""

    def __init__(self):
        self.consultas = []

    def execute(self, consulta, parametros=None):
        self.consultas.append((consulta, parametros))

    def fetchall(self):
        return [{"nombre": "Ana Prueba", "personaje_key": "femenino", "tema": "Suma", "puntos": 10}]


class PuntuacionesServiceTest(unittest.TestCase):
    def test_cada_acierto_vale_dos_puntos_y_cinco_valen_diez(self):
        self.assertEqual(PUNTOS_POR_ACIERTO, 2)
        self.assertEqual(puntos_por_aciertos(1), 2)
        self.assertEqual(puntos_por_aciertos(5), 10)
        self.assertEqual(puntos_por_aciertos(-2), 0)

    def test_respuesta_incorrecta_no_ejecuta_acreditacion(self):
        cursor = CursorPuntuacionFake()

        otorgados = acreditar_puntuacion_tema(9, 4, False, cursor)

        self.assertEqual(otorgados, 0)
        self.assertEqual(cursor.consultas, [])

    def test_respuesta_correcta_acumula_en_el_tema_real(self):
        cursor = CursorPuntuacionFake()

        otorgados = acreditar_puntuacion_tema(9, 14, True, cursor)

        self.assertEqual(otorgados, 2)
        consulta, parametros = cursor.consultas[0]
        self.assertIn("ON DUPLICATE KEY UPDATE", consulta)
        self.assertIn("puntos_acumulados", consulta)
        self.assertEqual(parametros, (9, 14, 2))

    def test_tabla_de_grupo_usa_parametros_canonicos_antes_del_tema(self):
        cursor = CursorPuntuacionFake()
        grupo = {"id_institucion": 3, "id_institucion_grado": 7, "id_seccion": 11}

        participantes = _consulta_clasificacion(14, grupo, 25, 0, cursor)

        self.assertEqual(participantes[0]["puntos"], 10)
        consulta, parametros = cursor.consultas[0]
        self.assertIn("pe.id_seccion = %s", consulta)
        self.assertEqual(parametros, (3, 7, 11, 14, 25, 0))

    def test_tema_invalido_no_abre_conexion(self):
        codigo, _, _, errores = obtener_clasificacion_estudiante(
            {"id_usuario": 9}, "tema-invalido", "general"
        )

        self.assertEqual(codigo, "datos_invalidos")
        self.assertIn("tema_id", errores)


if __name__ == "__main__":
    unittest.main()
