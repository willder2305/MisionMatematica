import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_JSX = ROOT / "frontend" / "src" / "main.jsx"
API_CLIENT_JS = ROOT / "frontend" / "src" / "services" / "apiClient.js"
SESSION_SERVICE_JS = ROOT / "frontend" / "src" / "services" / "sessionService.js"
LAYOUT_JSX = ROOT / "frontend" / "src" / "components" / "layout" / "PixelAdminLayout.jsx"
GRADOS_SERVICE_JS = ROOT / "frontend" / "src" / "services" / "gradosService.js"
SECCIONES_SERVICE_JS = ROOT / "frontend" / "src" / "services" / "seccionesService.js"
GRUPOS_SERVICE_JS = ROOT / "frontend" / "src" / "services" / "gruposService.js"
GRADOS_TABLE_JSX = ROOT / "frontend" / "src" / "components" / "grados" / "GradosTable.jsx"
SECCIONES_TABLE_JSX = ROOT / "frontend" / "src" / "components" / "secciones" / "SeccionesTable.jsx"
SECCION_FORM_JSX = ROOT / "frontend" / "src" / "components" / "secciones" / "SeccionForm.jsx"
ONBOARDING_PAGE_JSX = ROOT / "frontend" / "src" / "pages" / "OnboardingPage.jsx"
GRADOS_ROUTES = ROOT / "backend" / "routes" / "grados_routes.py"
SECCIONES_ROUTES = ROOT / "backend" / "routes" / "secciones_routes.py"
GRUPOS_ROUTES = ROOT / "backend" / "routes" / "grupos_routes.py"
APP_PY = ROOT / "backend" / "app.py"
ASIGNACIONES_PAGE_JSX = ROOT / "frontend" / "src" / "pages" / "AsignacionesPage.jsx"
REPORTES_DOCENTE_PAGE_JSX = ROOT / "frontend" / "src" / "pages" / "ReportesDocentePage.jsx"
ADMIN_PAGE_JSX = ROOT / "frontend" / "src" / "pages" / "AdminPage.jsx"
ADMIN_SERVICE_JS = ROOT / "frontend" / "src" / "services" / "adminService.js"
ADMIN_ROUTES = ROOT / "backend" / "routes" / "admin_routes.py"


class FrontendRoutingContractTest(unittest.TestCase):
    def setUp(self):
        self.codigo = MAIN_JSX.read_text(encoding="utf-8")

    def test_home_y_login_son_rutas_publicas(self):
        self.assertIn('const RUTAS_PUBLICAS = new Set(["/", "/login", "/registro", "/recuperar-password"])', self.codigo)
        self.assertIn("rutaActual === \"/registro\"", self.codigo)
        self.assertIn("LoginPage", self.codigo)

    def test_redireccion_por_rol_no_usa_secciones_como_home(self):
        self.assertIn("estudiante: \"/juego\"", self.codigo)
        self.assertIn("docente: \"/mi-institucion\"", self.codigo)
        self.assertIn("administrador: \"/admin\"", self.codigo)
        self.assertNotIn("return <SeccionesPage />;", self.codigo)

    def test_rutas_privadas_redirigen_a_login_si_no_hay_usuario(self):
        self.assertIn("if (!usuario)", self.codigo)
        self.assertIn("redirigir(\"/login\")", self.codigo)
        self.assertIn("NotFoundPage", self.codigo)

    def test_navegacion_interna_no_recarga_react(self):
        layout = LAYOUT_JSX.read_text(encoding="utf-8")
        self.assertIn("navegarInternamente(ruta)", layout)
        self.assertIn('href: "/admin/plantillas"', layout)
        self.assertIn("window.addEventListener(\"popstate\", sincronizarRuta)", self.codigo)
        self.assertIn("window.addEventListener(\"mm:navigation\", sincronizarRuta)", self.codigo)

    def test_api_client_renueva_access_token_una_vez(self):
        api_client = API_CLIENT_JS.read_text(encoding="utf-8")
        self.assertIn("const refrescarSesion = async ()", api_client)
        self.assertIn("`${API_URL}/auth/refresh`", api_client)
        self.assertIn("originalRequest._retry", api_client)
        self.assertIn("status !== 401", api_client)
        self.assertNotIn("status === 403", api_client)
        self.assertNotIn("status === 404", api_client)
        self.assertNotIn("status === 500", api_client)

    def test_sesion_usa_storage_centralizado(self):
        session_service = SESSION_SERVICE_JS.read_text(encoding="utf-8")
        self.assertIn('const ACCESS_TOKEN_KEY = "mm_access_token"', session_service)
        self.assertIn('const REFRESH_TOKEN_KEY = "mm_refresh_token"', session_service)
        self.assertIn("export const limpiarSesion", session_service)
        self.assertIn("mm:auth-updated", session_service)
        self.assertIn("mm:auth-invalid", session_service)

    def test_sesion_se_verifica_solo_en_bootstrap(self):
        self.assertIn("}, []);", self.codigo)
        self.assertNotIn("}, [rutaActual]);", self.codigo)
        self.assertIn("Verificando sesión", self.codigo)
        self.assertIn("Cargando módulo", self.codigo)

    def test_rutas_admin_canonicas_y_alias_plantillas(self):
        self.assertIn('"/admin/secciones"', self.codigo)
        self.assertIn('"/admin/grados"', self.codigo)
        self.assertIn('"/admin/asignaciones"', self.codigo)
        self.assertIn('"/admin/reportes"', self.codigo)
        self.assertIn('"/admin/plantillas"', self.codigo)
        self.assertIn('if (ruta === "/plantillas") return "/admin/plantillas";', self.codigo)
        self.assertIn('"/admin/plantillas": { componente: PlantillasPage', self.codigo)

    def test_grupos_no_tiene_ruta_ni_menu_visible(self):
        layout = LAYOUT_JSX.read_text(encoding="utf-8")
        self.assertNotIn('href: "/grupos"', layout)
        self.assertNotIn('label: "Grupos"', layout)
        self.assertNotIn('"/grupos"', self.codigo)
        self.assertNotIn("esGrupos", self.codigo)
        self.assertFalse((ROOT / "frontend" / "src" / "pages" / "GruposPage.jsx").exists())

    def test_frontend_no_expone_eliminacion_funcional(self):
        for ruta in (GRADOS_SERVICE_JS, SECCIONES_SERVICE_JS, GRUPOS_SERVICE_JS):
            codigo = ruta.read_text(encoding="utf-8")
            self.assertNotIn("api.delete", codigo)
            self.assertNotIn("Eliminar", codigo)

    def test_backend_no_expone_delete_grados_secciones_ni_post_grupos(self):
        grados = GRADOS_ROUTES.read_text(encoding="utf-8-sig")
        secciones = SECCIONES_ROUTES.read_text(encoding="utf-8")
        grupos = GRUPOS_ROUTES.read_text(encoding="utf-8")
        self.assertNotIn('methods=["DELETE"]', grados)
        self.assertNotIn('methods=["DELETE"]', secciones)
        self.assertNotIn('@grupos_bp.route("/grupos", methods=["POST"])', grupos)

    def test_codigos_visibles_desde_grados_y_secciones(self):
        grupos_service = GRUPOS_SERVICE_JS.read_text(encoding="utf-8")
        grados_table = GRADOS_TABLE_JSX.read_text(encoding="utf-8")
        secciones_table = SECCIONES_TABLE_JSX.read_text(encoding="utf-8")
        grupos_routes = GRUPOS_ROUTES.read_text(encoding="utf-8")
        self.assertIn("/codigos/secciones", grupos_service)
        self.assertIn("/codigos/grados-unicos", grupos_service)
        self.assertIn('Código/PIN', secciones_table)
        self.assertIn('Código de sección única', grados_table)
        self.assertIn('Sección única', grados_table)
        self.assertIn('"/codigos/secciones"', grupos_routes)
        self.assertIn('"/codigos/grados-unicos"', grupos_routes)

    def test_docente_no_ve_plantillas_como_modulo(self):
        layout = LAYOUT_JSX.read_text(encoding="utf-8")
        self.assertIn('roles: ["administrador"]', layout)
        self.assertIn('"/mi-institucion": { componente: MiInstitucionPage', self.codigo)
        self.assertIn('href: "/mi-institucion"', layout)

    def test_onboarding_docente_busca_institucion_y_secciones_a_d(self):
        onboarding = ONBOARDING_PAGE_JSX.read_text(encoding="utf-8")
        self.assertIn("buscarInstituciones", onboarding)
        self.assertIn("crearOReutilizarInstitucion", onboarding)
        self.assertIn('const SECCIONES_CONFIGURABLES = ["A", "B", "C", "D"]', onboarding)
        self.assertIn("secciones_por_grado", onboarding)

    def test_formulario_secciones_no_usa_nombre_libre_ni_unica(self):
        formulario = SECCION_FORM_JSX.read_text(encoding="utf-8")
        self.assertIn('const SECCIONES_PERMITIDAS = ["A", "B", "C", "D"]', formulario)
        self.assertNotIn('type="text"', formulario)
        self.assertNotIn("Unica", formulario)

    def test_backend_registra_rutas_instituciones(self):
        app = APP_PY.read_text(encoding="utf-8")
        self.assertIn("instituciones_bp", app)

    def test_asignaciones_usa_contexto_institucional_sin_grupos(self):
        pagina = ASIGNACIONES_PAGE_JSX.read_text(encoding="utf-8")
        self.assertIn("obtenerContextoAsignaciones", pagina)
        self.assertIn("id_institucion_grado", pagina)
        self.assertNotIn("obtenerGrupos", pagina)
        self.assertNotIn('name="id_grupo"', pagina)

    def test_reportes_docente_no_filtra_por_grupo(self):
        pagina = REPORTES_DOCENTE_PAGE_JSX.read_text(encoding="utf-8")
        self.assertIn("id_institucion_grado", pagina)
        self.assertNotIn("obtenerGrupos", pagina)
        self.assertNotIn('name="id_grupo"', pagina)

    def test_admin_reportes_institucionales_expuestos(self):
        pagina = ADMIN_PAGE_JSX.read_text(encoding="utf-8")
        servicio = ADMIN_SERVICE_JS.read_text(encoding="utf-8")
        rutas = ADMIN_ROUTES.read_text(encoding="utf-8")
        self.assertIn("obtenerCatalogosReportesAdmin", pagina)
        self.assertIn("obtenerReporteInstitucionalAdmin", pagina)
        self.assertIn("/admin/reportes/filtros", servicio)
        self.assertIn("/admin/reportes/institucional", servicio)
        self.assertIn('"/reportes/filtros"', rutas)
        self.assertIn('"/reportes/institucional"', rutas)


if __name__ == "__main__":
    unittest.main()
