import json

from db import obtener_conexion


def _serializar_fila(fila):
    # Convierte una fila de bitacora a JSON para el panel administrador.
    detalles = fila.get("detalles_json")
    if isinstance(detalles, str):
        try:
            detalles = json.loads(detalles)
        except json.JSONDecodeError:
            detalles = {}
    return {
        "id_bitacora": fila["id_bitacora"],
        "id_usuario": fila.get("id_usuario"),
        "usuario": fila.get("usuario") or "Sistema/anonimo",
        "correo": fila.get("correo"),
        "accion": fila["accion"],
        "entidad": fila["entidad"],
        "id_entidad": fila.get("id_entidad"),
        "metodo": fila["metodo"],
        "ruta": fila["ruta"],
        "codigo_estado": fila["codigo_estado"],
        "resultado": fila["resultado"],
        "ip_cliente": fila.get("ip_cliente"),
        "user_agent": fila.get("user_agent"),
        "detalles_json": detalles or {},
        "fecha_creacion": fila["fecha_creacion"].isoformat(sep=" ") if fila.get("fecha_creacion") else None,
    }


def listar_auditoria_admin(filtros=None):
    # Lista eventos recientes de auditoria con filtros administrativos.
    filtros = filtros or {}
    condiciones = []
    parametros = []

    for campo in ("accion", "entidad", "resultado"):
        valor = (filtros.get(campo) or "").strip()
        if valor:
            condiciones.append(f"b.{campo} = %s")
            parametros.append(valor)

    limite = min(max(int(filtros.get("limite") or 100), 1), 300)
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT b.id_bitacora, b.id_usuario, b.accion, b.entidad, b.id_entidad,
                   b.metodo, b.ruta, b.codigo_estado, b.resultado, b.ip_cliente,
                   b.user_agent, b.detalles_json, b.fecha_creacion,
                   CONCAT(u.nombres, ' ', u.apellidos) AS usuario,
                   u.correo
            FROM bitacora_acciones b
            LEFT JOIN usuarios u ON u.id_usuario = b.id_usuario
            {where}
            ORDER BY b.fecha_creacion DESC, b.id_bitacora DESC
            LIMIT %s
            """,
            tuple(parametros + [limite]),
        )
        return "consultado", "Auditoria consultada correctamente.", [_serializar_fila(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()
