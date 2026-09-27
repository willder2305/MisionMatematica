"""Catalogo, monedero e inventario persistente del estudiante."""

import random

from db import obtener_conexion


TIPOS_ITEM = ("personaje", "mapa")
MODO_ALEATORIO = "aleatorio"
MODO_FIJO = "fijo"
RECOMPENSA_NORMAL = 1
RECOMPENSA_PERFECTA = 2
COSTO_CONTINUACION = 1


def asegurar_estado_estudiante(id_usuario, cursor):
    """Crea monedero, inventario starter y preferencias para usuarios existentes."""
    cursor.execute("INSERT IGNORE INTO monederos (id_usuario, saldo_monedas) VALUES (%s, 0)", (id_usuario,))
    cursor.execute(
        """
        INSERT IGNORE INTO usuario_items (id_usuario, id_item)
        SELECT %s, id_item FROM tienda_items
        WHERE es_inicial = 1 AND estado = 'activo'
        """,
        (id_usuario,),
    )
    cursor.execute(
        """
        INSERT IGNORE INTO preferencias_estudiante (id_usuario, personaje_key, modo_mapa)
        VALUES (%s, 'masculino', 'aleatorio')
        """,
        (id_usuario,),
    )


def obtener_saldo_en_cursor(id_usuario, cursor):
    """Lee el saldo existente para incluirlo en respuestas ya autorizadas."""
    asegurar_estado_estudiante(id_usuario, cursor)
    cursor.execute("SELECT saldo_monedas FROM monederos WHERE id_usuario = %s", (id_usuario,))
    monedero = cursor.fetchone() or {"saldo_monedas": 0}
    return int(monedero["saldo_monedas"])


def bloquear_monedero_estudiante(id_usuario, cursor):
    """Obtiene el monedero bloqueado para que compras, premios y continuaciones no compitan."""
    asegurar_estado_estudiante(id_usuario, cursor)
    cursor.execute("SELECT saldo_monedas FROM monederos WHERE id_usuario = %s FOR UPDATE", (id_usuario,))
    return cursor.fetchone() or {"saldo_monedas": 0}


def registrar_movimiento_monedas(
    cursor,
    *,
    id_usuario,
    tipo,
    cantidad,
    saldo_anterior,
    saldo_nuevo,
    id_partida=None,
    id_item_tienda=None,
    descripcion=None,
    referencia=None,
    request_id=None,
):
    """Guarda un movimiento inmutable con los saldos antes y despues de la operacion."""
    cursor.execute(
        """
        INSERT INTO movimientos_monedas
            (id_usuario, id_partida, id_item_tienda, tipo, cantidad, saldo_anterior, saldo_nuevo,
             referencia, descripcion, request_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            id_usuario,
            id_partida,
            id_item_tienda,
            tipo,
            cantidad,
            saldo_anterior,
            saldo_nuevo,
            referencia,
            descripcion,
            request_id,
        ),
    )


def calcular_recompensa_partida(partida):
    """Devuelve la unica recompensa valida cuando una partida alcanzo la meta real."""
    completada = (
        partida.get("estado") == "completada"
        and int(partida.get("total_correctos") or 0) >= 10
        and int(partida.get("casilla_actual") or 0) == 10
    )
    if not completada:
        return None

    perfecta = (
        int(partida.get("total_errores") or 0) == 0
        and int(partida.get("vidas_perdidas_total") or 0) == 0
        and int(partida.get("continuaciones_compradas") or 0) == 0
    )
    if perfecta:
        return {
            "tipo": "perfecta",
            "movimiento": "recompensa_partida_perfecta",
            "monedas_ganadas": RECOMPENSA_PERFECTA,
            "descripcion": "Partida perfecta completada.",
        }
    return {
        "tipo": "normal",
        "movimiento": "recompensa_partida",
        "monedas_ganadas": RECOMPENSA_NORMAL,
        "descripcion": "Partida completada.",
    }


def acreditar_recompensa_partida(partida, cursor):
    """Acredita una vez la recompensa de una partida bloqueada dentro de su misma transaccion."""
    recompensa = calcular_recompensa_partida(partida)
    if not recompensa or int(partida.get("recompensa_otorgada") or 0):
        return None

    id_partida = partida["id_partida"]
    cursor.execute("SELECT recompensa_otorgada FROM partidas_juego WHERE id_partida = %s FOR UPDATE", (id_partida,))
    control = cursor.fetchone() or {"recompensa_otorgada": 1}
    if int(control.get("recompensa_otorgada") or 0):
        return None

    id_usuario = partida["id_usuario"]
    monedero = bloquear_monedero_estudiante(id_usuario, cursor)
    saldo_anterior = int(monedero["saldo_monedas"])
    saldo_nuevo = saldo_anterior + recompensa["monedas_ganadas"]
    cursor.execute("UPDATE monederos SET saldo_monedas = %s WHERE id_usuario = %s", (saldo_nuevo, id_usuario))
    registrar_movimiento_monedas(
        cursor,
        id_usuario=id_usuario,
        id_partida=id_partida,
        tipo=recompensa["movimiento"],
        cantidad=recompensa["monedas_ganadas"],
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        referencia=f"recompensa:partida:{id_partida}",
        descripcion=recompensa["descripcion"],
    )
    cursor.execute("UPDATE partidas_juego SET recompensa_otorgada = 1 WHERE id_partida = %s", (id_partida,))
    return {**recompensa, "saldo_actual": saldo_nuevo}


def obtener_saldo_estudiante(usuario):
    """Entrega el saldo del estudiante autenticado sin exponer monederos ajenos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        saldo = obtener_saldo_en_cursor(usuario["id_usuario"], cursor)
        conexion.commit()
        return "consultado", "Saldo consultado correctamente.", {"saldo": saldo}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _item_desbloqueado(id_usuario, tipo, item_key, cursor):
    cursor.execute(
        """
        SELECT ti.id_item, ti.item_key
        FROM usuario_items ui
        INNER JOIN tienda_items ti ON ti.id_item = ui.id_item
        WHERE ui.id_usuario = %s AND ui.estado = 'activo'
          AND ti.estado = 'activo' AND ti.tipo = %s AND ti.item_key = %s
        LIMIT 1
        """,
        (id_usuario, tipo, item_key),
    )
    return cursor.fetchone()


def _propiedad_item(id_usuario, id_item, cursor, bloquear=False):
    """Consulta una sola relación de inventario y, al comprar, la bloquea para evitar doble cobro."""
    bloqueo = " FOR UPDATE" if bloquear else ""
    cursor.execute(
        f"""
        SELECT id_usuario_item, estado
        FROM usuario_items
        WHERE id_usuario = %s AND id_item = %s
        LIMIT 1{bloqueo}
        """,
        (id_usuario, id_item),
    )
    return cursor.fetchone()


def _item_adquirido(fila):
    """Determina propiedad desde el catálogo y una relación activa de inventario."""
    return bool(fila.get("es_inicial") or fila.get("desbloqueado"))


def puede_usar_personaje(id_usuario, personaje_key, cursor):
    """Autoriza personajes starter o registrados en el inventario real del estudiante."""
    cursor.execute(
        """
        SELECT ti.es_inicial, CASE WHEN ui.id_usuario_item IS NULL THEN 0 ELSE 1 END AS desbloqueado
        FROM tienda_items ti
        LEFT JOIN usuario_items ui
            ON ui.id_item = ti.id_item AND ui.id_usuario = %s AND ui.estado = 'activo'
        WHERE ti.tipo = 'personaje' AND ti.item_key = %s AND ti.estado = 'activo'
        LIMIT 1
        """,
        (id_usuario, personaje_key),
    )
    personaje = cursor.fetchone()
    return bool(personaje and _item_adquirido(personaje))


def _serializar_item(fila, personaje_actual=None, mapa_fijo=None):
    adquirido = _item_adquirido(fila)
    return {
        "id_item": fila["id_item"],
        "tipo": fila["tipo"],
        "key": fila["item_key"],
        "nombre": fila["nombre"],
        "precio_monedas": int(fila["precio_monedas"]),
        "es_inicial": bool(fila["es_inicial"]),
        "desbloqueado": adquirido,
        "adquirido": adquirido,
        "activo": fila["estado"] == "activo",
        "seleccionado": (
            fila["tipo"] == "personaje" and fila["item_key"] == personaje_actual and adquirido
        ) or (
            fila["tipo"] == "mapa" and fila["item_key"] == mapa_fijo and adquirido
        ),
    }


def _leer_personalizacion(id_usuario, cursor):
    cursor.execute(
        "SELECT saldo_monedas FROM monederos WHERE id_usuario = %s",
        (id_usuario,),
    )
    monedero = cursor.fetchone() or {"saldo_monedas": 0}
    cursor.execute(
        """
        SELECT personaje_key, modo_mapa, mapa_key, ultimo_mapa_key
        FROM preferencias_estudiante WHERE id_usuario = %s
        """,
        (id_usuario,),
    )
    preferencias = cursor.fetchone() or {
        "personaje_key": "masculino",
        "modo_mapa": MODO_ALEATORIO,
        "mapa_key": None,
        "ultimo_mapa_key": None,
    }
    cursor.execute(
        """
        SELECT ti.*, CASE WHEN ui.id_usuario_item IS NULL THEN 0 ELSE 1 END AS desbloqueado
        FROM tienda_items ti
        LEFT JOIN usuario_items ui ON ui.id_item = ti.id_item AND ui.id_usuario = %s AND ui.estado = 'activo'
        WHERE ti.estado = 'activo'
        ORDER BY FIELD(ti.tipo, 'personaje', 'mapa'), ti.es_inicial DESC, ti.nombre ASC
        """,
        (id_usuario,),
    )
    items = cursor.fetchall()
    personaje_actual = preferencias["personaje_key"]
    mapa_fijo = preferencias["mapa_key"] if preferencias["modo_mapa"] == MODO_FIJO else None
    return {
        "saldo_monedas": int(monedero["saldo_monedas"]),
        "preferencias": {
            "personaje": personaje_actual,
            "modo_mapa": preferencias["modo_mapa"],
            "mapa": preferencias["mapa_key"],
        },
        "personajes": [_serializar_item(item, personaje_actual, mapa_fijo) for item in items if item["tipo"] == "personaje"],
        "mapas": [_serializar_item(item, personaje_actual, mapa_fijo) for item in items if item["tipo"] == "mapa"],
    }


def obtener_tienda_estudiante(usuario):
    """Devuelve saldo real, catalogo e inventario del estudiante autenticado."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        asegurar_estado_estudiante(usuario["id_usuario"], cursor)
        datos = _leer_personalizacion(usuario["id_usuario"], cursor)
        conexion.commit()
        return "consultado", "Tienda consultada correctamente.", datos, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def comprar_item_estudiante(usuario, id_item):
    """Compra una sola vez usando bloqueo de saldo e inventario dentro de una transaccion."""
    try:
        id_item = int(id_item)
    except (TypeError, ValueError):
        return "datos_invalidos", "El artículo seleccionado no es válido.", None, {"id_item": "Artículo inválido."}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        id_usuario = usuario["id_usuario"]
        asegurar_estado_estudiante(id_usuario, cursor)
        monedero = bloquear_monedero_estudiante(id_usuario, cursor)
        cursor.execute(
            "SELECT * FROM tienda_items WHERE id_item = %s AND estado = 'activo' FOR UPDATE",
            (id_item,),
        )
        item = cursor.fetchone()
        if not item:
            conexion.rollback()
            return "datos_invalidos", "El artículo no está disponible.", None, {"id_item": "Artículo no disponible."}
        propiedad = _propiedad_item(id_usuario, id_item, cursor, bloquear=True)
        if propiedad and propiedad["estado"] == "activo":
            datos = _leer_personalizacion(id_usuario, cursor)
            conexion.commit()
            return "articulo_ya_adquirido", f"{item['nombre']} ya es tuyo.", {
                **datos,
                "resultado_compra": {"id_item": id_item, "key": item["item_key"], "adquirido": True},
            }, {}

        saldo_anterior = int(monedero["saldo_monedas"])
        precio = int(item["precio_monedas"])
        if saldo_anterior < precio:
            conexion.rollback()
            return "datos_invalidos", "Necesitas más monedas.", None, {"saldo": "Saldo insuficiente."}

        saldo_nuevo = saldo_anterior - precio
        cursor.execute("UPDATE monederos SET saldo_monedas = %s WHERE id_usuario = %s", (saldo_nuevo, id_usuario))
        if propiedad:
            # Conserva el historial de inventario y reactiva una relación que estaba inactiva.
            cursor.execute(
                "UPDATE usuario_items SET estado = 'activo', fecha_desbloqueo = CURRENT_TIMESTAMP WHERE id_usuario_item = %s",
                (propiedad["id_usuario_item"],),
            )
        else:
            cursor.execute("INSERT INTO usuario_items (id_usuario, id_item) VALUES (%s, %s)", (id_usuario, id_item))
        registrar_movimiento_monedas(
            cursor,
            id_usuario=id_usuario,
            id_item_tienda=id_item,
            tipo="compra_personaje" if item["tipo"] == "personaje" else "compra_mapa",
            cantidad=-precio,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            referencia=f"tienda:{id_usuario}:{item['tipo']}:{item['item_key']}",
            descripcion=f"Compra de {item['nombre']}.",
        )
        datos = _leer_personalizacion(id_usuario, cursor)
        conexion.commit()
        return "consultado", f"¡{item['nombre']} ahora es tuyo!", {
            **datos,
            "resultado_compra": {"id_item": id_item, "key": item["item_key"], "adquirido": True},
        }, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_personaje_estudiante(usuario, personaje_key):
    """Guarda un personaje solo si existe en el inventario real del estudiante."""
    personaje_key = str(personaje_key or "").strip().lower()
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        id_usuario = usuario["id_usuario"]
        asegurar_estado_estudiante(id_usuario, cursor)
        if not puede_usar_personaje(id_usuario, personaje_key, cursor):
            conexion.rollback()
            return "no_autorizado", "Este personaje todavía no está desbloqueado.", None, {"personaje": "Personaje no desbloqueado."}
        cursor.execute("UPDATE preferencias_estudiante SET personaje_key = %s WHERE id_usuario = %s", (personaje_key, id_usuario))
        datos = _leer_personalizacion(id_usuario, cursor)
        conexion.commit()
        return "consultado", "Personaje actualizado.", datos, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_mapa_estudiante(usuario, modo_mapa, mapa_key=None):
    """Persiste el modo aleatorio o un mapa fijo previamente desbloqueado."""
    modo_mapa = str(modo_mapa or "").strip().lower()
    mapa_key = str(mapa_key or "").strip().lower() or None
    if modo_mapa not in (MODO_ALEATORIO, MODO_FIJO):
        return "datos_invalidos", "Seleccione un modo de mapa válido.", None, {"modo_mapa": "Modo inválido."}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        id_usuario = usuario["id_usuario"]
        asegurar_estado_estudiante(id_usuario, cursor)
        if modo_mapa == MODO_FIJO and not _item_desbloqueado(id_usuario, "mapa", mapa_key, cursor):
            conexion.rollback()
            return "no_autorizado", "Primero debes desbloquear ese mapa.", None, {"mapa": "Mapa no desbloqueado."}
        cursor.execute(
            "UPDATE preferencias_estudiante SET modo_mapa = %s, mapa_key = %s WHERE id_usuario = %s",
            (modo_mapa, mapa_key if modo_mapa == MODO_FIJO else None, id_usuario),
        )
        datos = _leer_personalizacion(id_usuario, cursor)
        conexion.commit()
        return "consultado", "Preferencia de mapa actualizada.", datos, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def resolver_personalizacion_partida(id_usuario, cursor):
    """Obtiene personaje y mapa permitidos para una partida sin aceptar decisiones del frontend."""
    asegurar_estado_estudiante(id_usuario, cursor)
    cursor.execute(
        "SELECT personaje_key, modo_mapa, mapa_key, ultimo_mapa_key FROM preferencias_estudiante WHERE id_usuario = %s FOR UPDATE",
        (id_usuario,),
    )
    preferencias = cursor.fetchone() or {"personaje_key": "masculino", "modo_mapa": MODO_ALEATORIO, "mapa_key": None, "ultimo_mapa_key": None}
    personaje = preferencias.get("personaje_key") or "masculino"
    if not puede_usar_personaje(id_usuario, personaje, cursor):
        personaje = "masculino"
        cursor.execute("UPDATE preferencias_estudiante SET personaje_key = %s WHERE id_usuario = %s", (personaje, id_usuario))

    cursor.execute(
        """
        SELECT ti.item_key FROM usuario_items ui
        INNER JOIN tienda_items ti ON ti.id_item = ui.id_item
        WHERE ui.id_usuario = %s AND ui.estado = 'activo' AND ti.tipo = 'mapa' AND ti.estado = 'activo'
        ORDER BY ti.item_key
        """,
        (id_usuario,),
    )
    mapas = [fila["item_key"] for fila in cursor.fetchall()]
    if not mapas:
        mapas = ["bosque"]
    mapa_fijo = preferencias.get("mapa_key")
    if preferencias.get("modo_mapa") == MODO_FIJO and mapa_fijo in mapas:
        mapa = mapa_fijo
    else:
        ultimo = preferencias.get("ultimo_mapa_key")
        candidatos = [mapa_key for mapa_key in mapas if mapa_key != ultimo] if len(mapas) > 1 else mapas
        mapa = random.choice(candidatos or mapas)
    cursor.execute("UPDATE preferencias_estudiante SET ultimo_mapa_key = %s WHERE id_usuario = %s", (mapa, id_usuario))
    return personaje, mapa
