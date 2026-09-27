"""Fábrica Flask que registra rutas, CORS y controles de seguridad transversales."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config, validar_configuracion_produccion
from routes.admin_routes import admin_bp
from routes.asignaciones_routes import asignaciones_bp
from routes.auth_routes import auth_bp
from routes.docente_routes import docente_bp
from routes.estudiante_routes import estudiante_bp
from routes.grados_routes import grados_bp
from routes.grupos_routes import grupos_bp
from routes.instituciones_routes import instituciones_bp
from routes.juego_routes import juego_bp
from routes.onboarding_routes import onboarding_bp
from routes.plantillas_routes import plantillas_bp
from routes.secciones_routes import secciones_bp
from routes.temas_routes import temas_bp
from services.security_service import aplicar_headers_seguridad, registrar_auditoria_desde_request, verificar_rate_limit


# Funcion: configurar_cors
# Descripcion:
#   Configura los origenes permitidos para las rutas /api/* durante el desarrollo con Vite.
#
# Es llamada desde:
#   crear_app() al construir la aplicacion Flask principal.
#
# Llama a:
#   CORS() de flask-cors usando Config.FRONTEND_URLS como lista explicita de origenes.
#
# Parametros:
#   app: instancia Flask que recibira la configuracion CORS.
#
# Retorna:
#   No retorna valores; modifica la instancia Flask recibida.
#
# Manejo de errores:
#   Si flask-cors falla durante el arranque, Flask detiene el inicio mostrando el error en consola.
def configurar_cors(app):
    CORS(app, resources={r"/api/*": {"origins": Config.FRONTEND_URLS}})


def configurar_seguridad(app):
    # Registra controles transversales de seguridad para toda la API.
    @app.before_request
    def _aplicar_rate_limit():
        permitido, datos = verificar_rate_limit(request)
        if permitido:
            return None
        respuesta = jsonify({
            "success": False,
            "message": "Demasiadas solicitudes. Intente nuevamente en unos segundos.",
            "data": None,
            "errors": {"rate_limit": f"Limite de {datos['limite']} solicitudes por minuto."},
        })
        respuesta.status_code = 429
        respuesta.headers["Retry-After"] = str(datos["retry_after"])
        return respuesta

    @app.after_request
    def _aplicar_seguridad_y_auditoria(response):
        aplicar_headers_seguridad(response)
        registrar_auditoria_desde_request(request, response)
        return response


def registrar_healthcheck(app):
    """Expone una comprobación liviana para Nginx y el supervisor del proceso.

    No consulta MySQL ni revela configuración: confirma exclusivamente que Flask
    está iniciado y puede responder a una solicitud HTTP.
    """
    @app.get("/api/health")
    def healthcheck():
        return jsonify({"success": True, "data": {"status": "ok"}})


# Funcion: crear_app
# Descripcion:
#   Construye y configura la aplicacion Flask principal del backend.
#
# Es llamada desde:
#   Este mismo archivo cuando se ejecuta python app.py.
#
# Llama a:
#   CORS() para permitir peticiones desde React y register_blueprint() para registrar rutas REST.
#
# Retorna:
#   Una instancia configurada de Flask.
#
# Manejo de errores:
#   Si algun blueprint no puede registrarse, Flask detiene el arranque y muestra el error en consola.
def crear_app():
    validar_configuracion_produccion()
    app = Flask(__name__)
    configurar_cors(app)
    configurar_seguridad(app)
    registrar_healthcheck(app)
    app.register_blueprint(admin_bp)
    app.register_blueprint(asignaciones_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(docente_bp)
    app.register_blueprint(estudiante_bp)
    app.register_blueprint(grados_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(instituciones_bp)
    app.register_blueprint(secciones_bp)
    app.register_blueprint(juego_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(temas_bp)
    app.register_blueprint(plantillas_bp)
    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)

