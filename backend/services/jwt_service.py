import base64
import hashlib
import hmac
import json
import time
import uuid

from config import Config


class TokenError(ValueError):
    pass


def _base64url_encode(data):
    # Codifica bytes en Base64 URL-safe sin padding, formato requerido por JWT.
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data):
    # Restaura padding y decodifica Base64 URL-safe.
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _firmar(mensaje):
    # Firma el token con HMAC-SHA256 usando el secreto configurado.
    return hmac.new(Config.JWT_SECRET_KEY.encode("utf-8"), mensaje.encode("ascii"), hashlib.sha256).digest()


def crear_token(usuario, tipo="access", expires_seconds=None):
    # Crea un JWT HS256 con identidad, rol, tipo y expiracion.
    ahora = int(time.time())
    expires_seconds = expires_seconds or (
        Config.JWT_ACCESS_EXPIRES if tipo == "access" else Config.JWT_REFRESH_EXPIRES
    )
    payload = {
        "sub": usuario["id_usuario"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "type": tipo,
        "iat": ahora,
        "exp": ahora + int(expires_seconds),
        "jti": str(uuid.uuid4()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    firma_b64 = _base64url_encode(_firmar(f"{header_b64}.{payload_b64}"))
    return f"{header_b64}.{payload_b64}.{firma_b64}", payload


def decodificar_token(token, tipo=None):
    # Valida firma, expiracion y tipo de token antes de devolver el payload.
    try:
        header_b64, payload_b64, firma_b64 = token.split(".")
    except ValueError as exc:
        raise TokenError("Token mal formado.") from exc

    try:
        header = json.loads(_base64url_decode(header_b64))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise TokenError("Encabezado del token inválido.") from exc

    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise TokenError("Algoritmo del token inválido.")

    firma_esperada = _base64url_encode(_firmar(f"{header_b64}.{payload_b64}"))
    if not hmac.compare_digest(firma_b64, firma_esperada):
        raise TokenError("Firma inválida.")

    try:
        payload = json.loads(_base64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError) as exc:
        raise TokenError("Contenido del token inválido.") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise TokenError("Token expirado.")
    if tipo and payload.get("type") != tipo:
        raise TokenError("Tipo de token inválido.")
    return payload


def hash_token(token):
    # Guarda solo el hash de refresh/reset tokens para evitar almacenar secretos reutilizables.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
