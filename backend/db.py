"""Conexión centralizada a MySQL para los servicios y modelos del backend."""

import mysql.connector
from mysql.connector import Error
from config import Config


def obtener_conexion():
    """Abre una conexión MySQL configurada para una operación de corta duración.

    Cada servicio asume la responsabilidad de confirmar o revertir su propia
    transacción y cerrar cursor/conexión en `finally`; así no quedan sesiones
    compartidas entre solicitudes Flask.
    """
    try:
        return mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )
    except Error:
        raise
