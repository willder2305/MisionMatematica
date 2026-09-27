import unittest
from unittest.mock import ANY, patch

from app import crear_app
from services.juego_adaptativo_service import (
    MAPAS_PERMITIDOS,
    _generar_siguiente_pregunta_partida,
    _validar_grado_estudiante,
    _validar_inicio,
    seleccionar_mapa_nueva_partida,
)


class CursorPerfilFake:
    # Simula las consultas de perfil y contexto institucional usadas para autorizar el grado.
    def __init__(self, perfil=None, institucional_permitido=False):
        self.perfil = perfil
        self.institucional_permitido = institucional_permitido
        self.ultima_consulta = ""

    def execute(self, query, _params=None):
        self.ultima_consulta = query

    def fetchone(self):
        if "INNER JOIN institucion_grados" in self.ultima_consulta:
            return {"id_perfil": 1} if self.institucional_permitido else None
        if "FROM perfiles_estudiante" in self.ultima_consulta:
            return self.perfil
        return None


class CursorMapaFake:
    # Simula la consulta del ultimo mapa usado por estudiante/asignacion.
    def __init__(self, ultimo_mapa):
        self.ultimo_mapa = ultimo_mapa

    def execute(self, _query, _params=None):
        return None

    def fetchone(self):
        return {"mapa": self.ultimo_mapa} if self.ultimo_mapa else None


class JuegoAutenticadoServiceTest(unittest.TestCase):
    def test_cuenta_propia_solo_permite_grado_del_perfil(self):
        cursor = CursorPerfilFake(perfil={"id_grado": 4, "modalidad": "cuenta_propia"})

        permitido, _, _ = _validar_grado_estudiante(10, 4, cursor)
        rechazado, _, errores = _validar_grado_estudiante(10, 5, cursor)

        self.assertTrue(permitido)
        self.assertFalse(rechazado)
        self.assertIn("id_grado", errores)

    def test_grupo_educativo_depende_de_perfil_institucional_activo(self):
        cursor_permitido = CursorPerfilFake(
            perfil={"id_grado": None, "modalidad": "grupo_educativo"},
            institucional_permitido=True,
        )
        cursor_rechazado = CursorPerfilFake(
            perfil={"id_grado": None, "modalidad": "grupo_educativo"},
            institucional_permitido=False,
        )

        permitido, _, _ = _validar_grado_estudiante(10, 4, cursor_permitido)
        rechazado, _, errores = _validar_grado_estudiante(10, 4, cursor_rechazado)

        self.assertTrue(permitido)
        self.assertFalse(rechazado)
        self.assertIn("id_grado", errores)
        self.assertIn("pe.id_perfil_estudiante", cursor_permitido.ultima_consulta)
        self.assertIn("ig.id_grado_base = %s", cursor_permitido.ultima_consulta)
        self.assertNotIn("pe.id_perfil\n", cursor_permitido.ultima_consulta)
        self.assertNotIn("ig.id_grado = %s", cursor_permitido.ultima_consulta)

    def test_requiere_perfil_estudiante(self):
        permitido, _, errores = _validar_grado_estudiante(10, 4, CursorPerfilFake())

        self.assertFalse(permitido)
        self.assertIn("onboarding", errores)

    def test_validar_inicio_acepta_request_id_para_idempotencia(self):
        datos, errores = _validar_inicio({
            "id_usuario_autenticado": 18,
            "personaje": "femenino",
            "mapa": "bosque",
            "id_grado": 1,
            "id_tema": 7,
            "id_asignacion": 6,
            "request_id": "inicio-unico",
        })

        self.assertEqual(errores, {})
        self.assertEqual(datos["id_usuario"], 18)
        self.assertEqual(datos["id_asignacion"], 6)
        self.assertEqual(datos["request_id"], "inicio-unico")
        self.assertNotIn("id_grado", datos)

    def test_validar_inicio_no_requiere_grado_manual(self):
        datos, errores = _validar_inicio({
            "id_usuario_autenticado": 18,
            "personaje": "femenino",
            "id_tema": 7,
            "request_id": "inicio-sin-grado",
        })

        self.assertEqual(errores, {})
        self.assertNotIn("id_grado", datos)

    def test_endpoint_partidas_requiere_autenticacion(self):
        cliente = crear_app().test_client()

        respuesta = cliente.post("/api/juego/partidas", json={
            "personaje": "femenino",
            "mapa": "bosque",
            "id_grado": 1,
            "id_tema": 7,
        })

        self.assertEqual(respuesta.status_code, 401, respuesta.get_json())

    def test_selector_mapa_evitar_repeticion_inmediata(self):
        for _ in range(10):
            mapa = seleccionar_mapa_nueva_partida(10, 6, CursorMapaFake("bosque"))
            self.assertIn(mapa, MAPAS_PERMITIDOS)
            self.assertNotEqual(mapa, "bosque")

    def test_siguiente_pregunta_no_recurre_al_banco_estatico(self):
        partida = {"id_partida": 1, "id_grado": 1, "id_tema": 1}
        with patch("services.juego_adaptativo_service.generar_y_guardar_ejercicio", return_value=None) as generar:
            pregunta = _generar_siguiente_pregunta_partida(partida, 1, object())

        self.assertIsNone(pregunta)
        generar.assert_called_once_with(1, 1, 1, 1, ANY)


if __name__ == "__main__":
    unittest.main()
