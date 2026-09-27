import json
import time
from collections import defaultdict, deque

from flask import g
from mysql.connector import Error

from config import Config
from db import obtener_conexion


_VENTANAS_RATE_LIMIT = defaultdict(deque)
_CAMPOS_SENSIBLES = {"password", "refresh_token", "token", "access_token", "password_hash"}


def _cliente_ip(request):
    """Obtiene la IP para rate limiting y auditoría sin confiar en cabeceras públicas.

    `X-Forwarded-For` solo se acepta cuando el despliegue marca explícitamente
    que existe un proxy confiable que sobrescribe esa cabecera. En desarrollo
    y despliegues directos se usa `REMOTE_ADDR` para evitar suplantación.
    """
    if Config.TRUST_PROXY_HEADERS:
        forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.remote_addr or "desconocido"


def _limite_para_peticion(request):
    # Aplica un limite mas estricto a rutas de autenticacion.
    endpoint = request.endpoint or ""
    if endpoint.startswith("auth_bp."):
        return Config.RATE_LIMIT_AUTH_PER_MINUTE
    return Config.RATE_LIMIT_API_PER_MINUTE


def verificar_rate_limit(request):
    # Rate limit simple en memoria por IP, endpoint y minuto.
    if not Config.RATE_LIMIT_ENABLED or not request.path.startswith("/api/"):
        return True, {}
    limite = _limite_para_peticion(request)
    ahora = time.time()
    clave = (_cliente_ip(request), request.endpoint or request.path)
    ventana = _VENTANAS_RATE_LIMIT[clave]
    while ventana and ventana[0] <= ahora - 60:
        ventana.popleft()
    if len(ventana) >= limite:
        retry_after = max(1, int(60 - (ahora - ventana[0])))
        return False, {"limite": limite, "retry_after": retry_after}
    ventana.append(ahora)
    return True, {"limite": limite}


def limpiar_rate_limit():
    # Limpia memoria de rate limit para pruebas automatizadas.
    _VENTANAS_RATE_LIMIT.clear()


def aplicar_headers_seguridad(response):
    # Agrega headers seguros a las respuestas sin cambiar el payload.
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if getattr(response, "mimetype", "") == "application/json":
        response.headers.setdefault("Cache-Control", "no-store")
    return response


def _resolver_accion_entidad(request):
    # Deriva una accion legible desde metodo y endpoint Flask.
    endpoint = request.endpoint or ""
    partes = endpoint.split(".", 1)
    nombre = partes[1] if len(partes) == 2 else endpoint or request.path.strip("/").replace("/", "_")
    entidad = nombre.split("_")[0] if "_" in nombre else nombre
    prefijo = {
        "POST": "crear",
        "PUT": "actualizar",
        "PATCH": "actualizar",
        "DELETE": "eliminar",
        "GET": "consultar",
    }.get(request.method, request.method.lower())
    if nombre in ("login", "register", "logout", "refresh", "forgot_password", "reset_password", "verify_email"):
        return nombre, "auth"
    return f"{prefijo}_{nombre}", entidad or "api"


def _id_entidad_desde_request(request):
    # Usa parametros de ruta tipo id_* para identificar el registro afectado.
    for clave, valor in (request.view_args or {}).items():
        if clave.startswith("id_"):
            return str(valor)
    return None


def _detalles_seguros(request):
    # Guarda solo nombres de campos para no persistir contrasenas o tokens.
    detalles = {"endpoint": request.endpoint, "args": sorted(request.args.keys())}
    datos = request.get_json(silent=True)
    if isinstance(datos, dict):
        detalles["campos_json"] = sorted(k for k in datos.keys() if k not in _CAMPOS_SENSIBLES)
    if request.view_args:
        detalles["ruta_ids"] = request.view_args
    return detalles


def registrar_auditoria_desde_request(request, response):
    # Persiste acciones sensibles; nunca debe romper la respuesta original.
    if not request.path.startswith("/api/") or request.method in ("GET", "HEAD", "OPTIONS"):
        return
    accion, entidad = _resolver_accion_entidad(request)
    usuario = getattr(g, "usuario_actual", None)
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO bitacora_acciones
                (id_usuario, accion, entidad, id_entidad, metodo, ruta, codigo_estado,
                 resultado, ip_cliente, user_agent, detalles_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usuario["id_usuario"] if usuario else None,
                accion[:80],
                entidad[:80],
                _id_entidad_desde_request(request),
                request.method,
                request.path[:255],
                response.status_code,
                "exitoso" if response.status_code < 400 else "fallido",
                _cliente_ip(request)[:45],
                (request.headers.get("User-Agent") or "")[:255],
                json.dumps(_detalles_seguros(request), ensure_ascii=False),
            ),
        )
        conexion.commit()
    except Error:
        if conexion:
            conexion.rollback()
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
