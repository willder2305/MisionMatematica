import unittest
from pathlib import Path

from services.personalizacion_service import puede_usar_personaje


ROOT = Path(__file__).resolve().parents[2]
ONBOARDING_SERVICE = ROOT / "backend" / "services" / "onboarding_service.py"
ONBOARDING_ROUTES = ROOT / "backend" / "routes" / "onboarding_routes.py"
PERSONALIZACION_SERVICE = ROOT / "backend" / "services" / "personalizacion_service.py"
ONBOARDING_PAGE = ROOT / "frontend" / "src" / "pages" / "OnboardingPage.jsx"
ONBOARDING_CLIENT = ROOT / "frontend" / "src" / "services" / "onboardingService.js"
MIGRACION = ROOT / "database" / "actualizar_personajes_iniciales.sql"


class CursorPersonaje:
    def __init__(self, personaje):
        self.personaje = personaje
        self.parametros = None

    def execute(self, _consulta, parametros):
        self.parametros = parametros

    def fetchone(self):
        return self.personaje


class PersonajesInicialesTest(unittest.TestCase):
    def test_personaje_starter_o_desbloqueado_puede_usarse(self):
        self.assertTrue(puede_usar_personaje(8, "masculino", CursorPersonaje({"es_inicial": 1, "desbloqueado": 0})))
        self.assertTrue(puede_usar_personaje(8, "astronauta", CursorPersonaje({"es_inicial": 0, "desbloqueado": 1})))

    def test_personaje_premium_bloqueado_no_puede_usarse(self):
        self.assertFalse(puede_usar_personaje(8, "astronauta", CursorPersonaje({"es_inicial": 0, "desbloqueado": 0})))
        self.assertFalse(puede_usar_personaje(8, "inexistente", CursorPersonaje(None)))

    def test_onboarding_consulta_solo_starters_desde_backend(self):
        servicio = ONBOARDING_SERVICE.read_text(encoding="utf-8")
        rutas = ONBOARDING_ROUTES.read_text(encoding="utf-8")
        cliente = ONBOARDING_CLIENT.read_text(encoding="utf-8")
        self.assertIn("tipo = 'personaje' AND es_inicial = 1 AND estado = 'activo'", servicio)
        self.assertIn('"/personajes-iniciales"', rutas)
        self.assertIn('"/onboarding/personajes-iniciales"', cliente)
        self.assertNotIn("PERSONAJES_VALIDOS", servicio)

    def test_onboarding_rechaza_personaje_premium_manipulado(self):
        servicio = ONBOARDING_SERVICE.read_text(encoding="utf-8")
        self.assertIn("_personaje_inicial_activo(personaje, cursor)", servicio)
        self.assertIn("Selecciona uno de los personajes disponibles.", servicio)
        self.assertIn("Este personaje todavía no está desbloqueado.", servicio)

    def test_frontend_no_renderiza_catalogo_completo_de_personajes(self):
        pagina = ONBOARDING_PAGE.read_text(encoding="utf-8")
        self.assertIn("obtenerPersonajesIniciales", pagina)
        self.assertIn("personajesIniciales.map", pagina)
        self.assertNotIn("Object.values(personajesConfig)", pagina)
        self.assertNotIn("Comprar", pagina)
        self.assertNotIn("precio_monedas", pagina)

    def test_migracion_activa_solo_los_dos_starters_y_preserva_premium(self):
        migracion = MIGRACION.read_text(encoding="utf-8")
        self.assertIn("item_key IN ('masculino', 'femenino')", migracion)
        self.assertIn("item_key NOT IN ('masculino', 'femenino')", migracion)
        self.assertIn("ti.es_inicial = 1", migracion)
        self.assertNotIn("DELETE", migracion.upper())

    def test_partida_y_cambio_reutilizan_validacion_central(self):
        servicio = PERSONALIZACION_SERVICE.read_text(encoding="utf-8")
        self.assertGreaterEqual(servicio.count("puede_usar_personaje("), 3)
        self.assertIn("resolver_personalizacion_partida", servicio)


if __name__ == "__main__":
    unittest.main()
