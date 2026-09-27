import os
from dotenv import load_dotenv

load_dotenv()


SECRETOS_JWT_INSEGUROS = {"", "dev-secret-change-me", "secret", "123456"}


class Config:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "tesis_matematica_app")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_EXPIRES = int(os.getenv("JWT_ACCESS_EXPIRES", "900"))
    JWT_REFRESH_EXPIRES = int(os.getenv("JWT_REFRESH_EXPIRES", "604800"))
    MAIL_HOST = os.getenv("MAIL_HOST", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USER = os.getenv("MAIL_USER", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@misionmatematica.local")
    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
    DEBUG = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes", "on") and APP_ENV == "development"
    TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes", "on")
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    RATE_LIMIT_AUTH_PER_MINUTE = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "10"))
    RATE_LIMIT_API_PER_MINUTE = int(os.getenv("RATE_LIMIT_API_PER_MINUTE", "240"))
    FRONTEND_URLS = [
        url.strip()
        for url in os.getenv(
            "FRONTEND_URLS",
            "http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:5173,http://localhost:5174",
        ).split(",")
        if url.strip()
    ]


def validar_configuracion_produccion():
    """Impide iniciar producción con el secreto JWT de ejemplo o vacío.

    Desarrollo conserva un valor local para simplificar las pruebas, pero una
    instancia marcada como producción debe recibir su secreto por entorno.
    """
    if Config.APP_ENV == "production" and Config.JWT_SECRET_KEY in SECRETOS_JWT_INSEGUROS:
        raise RuntimeError("JWT_SECRET_KEY debe configurarse con un secreto seguro en producción.")


