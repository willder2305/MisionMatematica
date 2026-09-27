import secrets
from datetime import datetime, timedelta

from db import obtener_conexion


PIN_DIAS_VIGENCIA = 30


def _serializar_fecha(valor):
    # Convierte fechas MySQL a texto JSON estable.
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _serializar_grupo(fila):
    # Convierte una fila de grupo a la forma esperada por API.
    if not fila:
        return None
    return {
        "id_grupo": fila["id_grupo"],
        "id_docente": fila["id_docente"],
        "id_grado": fila["id_grado"],
        "id_institucion": fila.get("id_institucion"),
        "id_institucion_grado": fila.get("id_institucion_grado"),
        "nombre": fila["nombre"],
        "descripcion": fila.get("descripcion"),
        "estado": fila["estado"],
        "codigo_grado": fila.get("codigo_grado"),
        "nombre_grado": fila.get("nombre_grado"),
        "institucion": fila.get("institucion"),
        "docente": fila.get("docente"),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
    }


def _serializar_pin(fila):
    # Convierte un PIN a JSON manteniendo el string de seis digitos.
    if not fila:
        return None
    return {
        "id_pin": fila["id_pin"],
        "pin": fila["pin"],
        "id_grupo": fila["id_grupo"],
        "id_seccion": fila.get("id_seccion"),
        "id_grado": fila.get("id_grado"),
        "id_institucion": fila.get("id_institucion"),
        "id_institucion_grado": fila.get("id_institucion_grado"),
        "estado": fila["estado"],
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_expiracion": _serializar_fecha(fila.get("fecha_expiracion")),
        "grupo": fila.get("grupo"),
        "seccion": fila.get("seccion"),
        "grado": fila.get("grado"),
        "institucion": fila.get("institucion"),
        "docente": fila.get("docente"),
    }


def _grupo_por_id(id_grupo, cursor):
    # Consulta grupo con datos de grado/docente para validar ownership.
    cursor.execute(
        """
        SELECT gr.*, g.codigo_grado, g.nombre_grado,
               CONCAT(u.nombres, ' ', u.apellidos) AS docente
        FROM grupos gr
        INNER JOIN grados g ON g.id_grado = gr.id_grado
        INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
        WHERE gr.id_grupo = %s
        """,
        (id_grupo,),
    )
    return cursor.fetchone()


def _nombre_grupo_interno(cursor, id_docente, id_grado, id_institucion_grado=None):
    # Genera el nombre tecnico del grupo sin pedirlo al usuario.
    if id_institucion_grado:
        cursor.execute(
            """
            SELECT g.nombre_grado, i.nombre AS institucion,
                   CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM institucion_grados ig
            INNER JOIN grados g ON g.id_grado = ig.id_grado_base
            INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN usuarios u ON u.id_usuario = %s
            WHERE ig.id_institucion_grado = %s
            """,
            (id_docente, id_institucion_grado),
        )
    else:
        cursor.execute(
            """
            SELECT g.nombre_grado, NULL AS institucion, CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM grados g
            INNER JOIN usuarios u ON u.id_usuario = %s
            WHERE g.id_grado = %s
            """,
            (id_docente, id_grado),
        )
    fila = cursor.fetchone()
    if not fila:
        return f"Grupo interno {id_docente}-{id_grado}"
    contexto = f"{fila['nombre_grado']} - {fila['institucion']}" if fila.get("institucion") else fila["nombre_grado"]
    return f"{contexto} - {fila['docente']}"


def obtener_o_crear_grupo_docente_grado(id_docente, id_grado, cursor, id_institucion_grado=None):
    # Reutiliza el grupo tecnico unico por docente y grado; si no existe, lo crea.
    if id_institucion_grado:
        cursor.execute(
            """
            SELECT id_grupo
            FROM grupos
            WHERE id_docente = %s
              AND id_institucion_grado = %s
            ORDER BY id_grupo ASC
            LIMIT 1
            """,
            (id_docente, id_institucion_grado),
        )
    else:
        cursor.execute(
            """
            SELECT id_grupo
            FROM grupos
            WHERE id_docente = %s
              AND id_grado = %s
              AND id_institucion_grado IS NULL
            ORDER BY id_grupo ASC
            LIMIT 1
            """,
            (id_docente, id_grado),
        )
    grupo = cursor.fetchone()
    if grupo:
        cursor.execute("UPDATE grupos SET estado = 'activo' WHERE id_grupo = %s", (grupo["id_grupo"],))
        return grupo["id_grupo"]

    nombre = _nombre_grupo_interno(cursor, id_docente, id_grado, id_institucion_grado)
    cursor.execute(
        """
        INSERT INTO grupos (id_docente, id_grado, id_institucion_grado, nombre, descripcion, estado)
        VALUES (%s, %s, %s, %s, %s, 'activo')
        """,
        (id_docente, id_grado, id_institucion_grado, nombre, "Grupo interno generado automaticamente."),
    )
    return cursor.lastrowid


def asociar_seccion_interna(id_grupo, id_seccion, cursor):
    # Vincula una seccion al grupo interno sin duplicar la relacion.
    cursor.execute(
        """
        SELECT 1
        FROM grupo_secciones
        WHERE id_grupo = %s
          AND id_seccion = %s
        """,
        (id_grupo, id_seccion),
    )
    if cursor.fetchone():
        return
    cursor.execute(
        "INSERT INTO grupo_secciones (id_grupo, id_seccion) VALUES (%s, %s)",
        (id_grupo, id_seccion),
    )


def asegurar_pin_activo(id_creador, id_grupo, id_seccion, cursor):
    # Crea un PIN activo solo si no hay uno vigente para el grupo/seccion indicado.
    if id_seccion is None:
        cursor.execute(
            """
            SELECT id_pin
            FROM pines_acceso
            WHERE id_grupo = %s
              AND id_seccion IS NULL
              AND estado = 'activo'
              AND fecha_expiracion > CURRENT_TIMESTAMP
            LIMIT 1
            """,
            (id_grupo,),
        )
    else:
        cursor.execute(
            """
            SELECT id_pin
            FROM pines_acceso
            WHERE id_seccion = %s
              AND estado = 'activo'
              AND fecha_expiracion > CURRENT_TIMESTAMP
            LIMIT 1
            """,
            (id_seccion,),
        )
    if cursor.fetchone():
        return None

    pin = _generar_pin_unico(cursor)
    cursor.execute(
        """
        INSERT INTO pines_acceso (pin, id_grupo, id_seccion, estado, fecha_expiracion, creado_por)
        VALUES (%s, %s, %s, 'activo', %s, %s)
        """,
        (pin, id_grupo, id_seccion, datetime.utcnow() + timedelta(days=PIN_DIAS_VIGENCIA), id_creador),
    )
    return cursor.lastrowid


def desactivar_pin_general_grupo(id_grupo, cursor):
    # Desactiva el PIN general cuando el grupo pasa a trabajar por secciones.
    cursor.execute(
        """
        UPDATE pines_acceso
        SET estado = 'inactivo'
        WHERE id_grupo = %s
          AND id_seccion IS NULL
          AND estado = 'activo'
        """,
        (id_grupo,),
    )


def sincronizar_codigos_grado_docente(id_docente, id_grado, cursor, id_institucion_grado=None):
    # Asegura el grupo interno y decide si usa PIN general o PIN por seccion.
    id_grupo = obtener_o_crear_grupo_docente_grado(id_docente, id_grado, cursor, id_institucion_grado)
    if id_institucion_grado:
        cursor.execute(
            """
            SELECT s.id_seccion
            FROM secciones s
            INNER JOIN docente_secciones ds
                ON ds.id_seccion = s.id_seccion
               AND ds.id_docente = %s
               AND ds.estado = 'activo'
            WHERE s.id_institucion_grado = %s
              AND s.estado = 'activo'
            ORDER BY s.nombre_seccion ASC
            """,
            (id_docente, id_institucion_grado),
        )
    else:
        cursor.execute(
            """
            SELECT id_seccion
            FROM secciones
            WHERE id_grado = %s
              AND id_institucion_grado IS NULL
              AND estado = 'activo'
            ORDER BY nombre_seccion ASC
            """,
            (id_grado,),
        )
    secciones = [fila["id_seccion"] for fila in cursor.fetchall()]
    if not secciones:
        asegurar_pin_activo(id_docente, id_grupo, None, cursor)
        return id_grupo

    desactivar_pin_general_grupo(id_grupo, cursor)
    for id_seccion in secciones:
        asociar_seccion_interna(id_grupo, id_seccion, cursor)
        asegurar_pin_activo(id_docente, id_grupo, id_seccion, cursor)
    return id_grupo


def listar_codigos_secciones(usuario):
    # Devuelve PIN activos por seccion para mostrarlos desde la vista Secciones.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        filtro = ""
        parametros = []
        if usuario["rol"] == "docente":
            filtro = "AND (gr.id_docente = %s OR ds.id_docente = %s)"
            parametros.append(usuario["id_usuario"])
            parametros.append(usuario["id_usuario"])
        elif usuario["rol"] != "administrador":
            return "no_autorizado", "Permisos insuficientes.", None, {}

        cursor.execute(
            f"""
            SELECT p.id_pin, p.pin, p.id_grupo, p.id_seccion, p.estado,
                   gr.id_docente, g.id_grado, g.nombre_grado AS grado,
                   ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
                   s.nombre_seccion AS seccion, CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM pines_acceso p
            INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
            INNER JOIN secciones s ON s.id_seccion = p.id_seccion
            LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = s.id_institucion_grado
            LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
            INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
            LEFT JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion AND ds.estado = 'activo'
            WHERE p.estado = 'activo'
              AND p.fecha_expiracion > CURRENT_TIMESTAMP
              AND s.nombre_seccion <> 'Única'
              {filtro}
            ORDER BY i.nombre ASC, g.orden_visualizacion ASC, s.nombre_seccion ASC, u.nombres ASC
            """,
            tuple(parametros),
        )
        return "consultado", "Codigos de secciones consultados correctamente.", [
            _serializar_pin(fila) for fila in cursor.fetchall()
        ], {}
    finally:
        cursor.close()
        conexion.close()


def listar_codigos_grados_unicos(usuario):
    # Devuelve PIN generales de grupos sin secciones para mostrarlos desde Grados.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        filtro = ""
        parametros = []
        if usuario["rol"] == "docente":
            filtro = "AND (gr.id_docente = %s OR ds.id_docente = %s)"
            parametros.append(usuario["id_usuario"])
            parametros.append(usuario["id_usuario"])
        elif usuario["rol"] != "administrador":
            return "no_autorizado", "Permisos insuficientes.", None, {}

        cursor.execute(
            f"""
            SELECT p.id_pin, p.pin, p.id_grupo, p.id_seccion, p.estado,
                   gr.id_docente, g.id_grado, g.nombre_grado AS grado,
                   ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
                   COALESCE(s.nombre_seccion, 'Seccion unica') AS seccion,
                   CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM pines_acceso p
            INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
            LEFT JOIN secciones s ON s.id_seccion = p.id_seccion
            LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(s.id_institucion_grado, gr.id_institucion_grado)
            LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
            INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
            LEFT JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion AND ds.estado = 'activo'
            WHERE p.estado = 'activo'
              AND p.fecha_expiracion > CURRENT_TIMESTAMP
              AND (p.id_seccion IS NULL OR s.nombre_seccion = 'Única')
              {filtro}
            ORDER BY i.nombre ASC, g.orden_visualizacion ASC, u.nombres ASC
            """,
            tuple(parametros),
        )
        return "consultado", "Codigos de grados sin secciones consultados correctamente.", [
            _serializar_pin(fila) for fila in cursor.fetchall()
        ], {}
    finally:
        cursor.close()
        conexion.close()


def _puede_administrar_grupo(usuario, grupo):
    # Administra si es administrador o docente propietario del grupo.
    return usuario["rol"] == "administrador" or (
        usuario["rol"] == "docente" and grupo and grupo["id_docente"] == usuario["id_usuario"]
    )


def _seccion_valida_para_grupo(id_seccion, grupo, cursor):
    # Valida que la seccion exista, este activa y pertenezca al grado del grupo.
    if not id_seccion:
        return True
    cursor.execute(
        """
        SELECT id_seccion
        FROM secciones
        WHERE id_seccion = %s
          AND id_grado = %s
          AND estado = 'activo'
        """,
        (id_seccion, grupo["id_grado"]),
    )
    return cursor.fetchone() is not None


def _seccion_asociada_al_grupo(id_seccion, id_grupo, cursor):
    # Confirma que la seccion opcional ya esta vinculada al grupo.
    if not id_seccion:
        return True
    cursor.execute(
        """
        SELECT 1
        FROM grupo_secciones
        WHERE id_grupo = %s
          AND id_seccion = %s
        """,
        (id_grupo, id_seccion),
    )
    return cursor.fetchone() is not None


def listar_grupos(usuario):
    # Lista grupos propios para docente; administrador consulta todos.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        filtro = ""
        parametros = []
        if usuario["rol"] == "docente":
            filtro = "WHERE gr.id_docente = %s"
            parametros.append(usuario["id_usuario"])
        elif usuario["rol"] != "administrador":
            return "no_autorizado", "Permisos insuficientes.", None, {}

        cursor.execute(
            f"""
            SELECT gr.*, g.codigo_grado, g.nombre_grado,
                   ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
                   CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM grupos gr
            LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = gr.id_institucion_grado
            LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
            INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
            {filtro}
            ORDER BY i.nombre ASC, g.orden_visualizacion ASC, gr.fecha_creacion DESC
            """,
            tuple(parametros),
        )
        return "consultado", "Grupos consultados correctamente.", [_serializar_grupo(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()


def asociar_secciones_grupo(usuario, id_grupo, ids_seccion):
    # Agrega secciones al grupo interno sin borrar relaciones historicas existentes.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        grupo = _grupo_por_id(id_grupo, cursor)
        if not grupo:
            return "no_existe", "El grupo solicitado no existe.", None, {}
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede administrar este grupo.", None, {}

        try:
            secciones = sorted({int(id_seccion) for id_seccion in (ids_seccion or [])})
        except (TypeError, ValueError):
            return "datos_invalidos", "Revise las secciones.", None, {"secciones": "Lista invalida."}
        for id_seccion in secciones:
            if not _seccion_valida_para_grupo(id_seccion, grupo, cursor):
                return "datos_invalidos", "Una seccion no pertenece al grado del grupo.", None, {"id_seccion": "Seccion invalida."}

        for id_seccion in secciones:
            asociar_seccion_interna(id_grupo, id_seccion, cursor)
        conexion.commit()
        return "actualizado", "Secciones del grupo actualizadas.", {"id_grupo": id_grupo, "secciones": secciones}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def listar_secciones_grupo(usuario, id_grupo):
    # Lista secciones vinculadas al grupo validando ownership.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        grupo = _grupo_por_id(id_grupo, cursor)
        if not grupo:
            return "no_existe", "El grupo solicitado no existe.", None, {}
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede consultar este grupo.", None, {}
        cursor.execute(
            """
            SELECT s.id_seccion, s.nombre_seccion, s.id_grado
            FROM grupo_secciones gs
            INNER JOIN secciones s ON s.id_seccion = gs.id_seccion
            WHERE gs.id_grupo = %s
            ORDER BY s.nombre_seccion ASC
            """,
            (id_grupo,),
        )
        return "consultado", "Secciones consultadas correctamente.", cursor.fetchall(), {}
    finally:
        cursor.close()
        conexion.close()


def _generar_pin_unico(cursor):
    # Genera PIN criptograficamente seguro y unico entre activos.
    for _ in range(25):
        pin = f"{secrets.randbelow(1000000):06d}"
        cursor.execute(
            "SELECT 1 FROM pines_acceso WHERE pin = %s AND estado = 'activo'",
            (pin,),
        )
        if not cursor.fetchone():
            return pin
    raise ValueError("No se pudo generar un PIN unico.")


def _pin_activo_por_codigo(pin, cursor):
    # Resuelve PIN con institucion, grado, seccion y docente sin abrir otra conexion.
    cursor.execute(
        """
        SELECT p.*, gr.nombre AS grupo, s.nombre_seccion AS seccion, g.nombre_grado AS grado,
               g.id_grado, g.orden_visualizacion,
               ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
               CONCAT(u.nombres, ' ', u.apellidos) AS docente
        FROM pines_acceso p
        INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
        INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
        LEFT JOIN secciones s ON s.id_seccion = p.id_seccion
        LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(s.id_institucion_grado, gr.id_institucion_grado)
        LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
        INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
        WHERE p.pin = %s
          AND p.estado = 'activo'
          AND p.fecha_expiracion > CURRENT_TIMESTAMP
          AND gr.estado = 'activo'
          AND (s.id_seccion IS NULL OR s.estado = 'activo')
        LIMIT 1
        """,
        (str(pin).strip(),),
    )
    return cursor.fetchone()


def crear_pin(usuario, id_grupo, datos):
    # Genera un PIN activo para un grupo y seccion opcional.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        grupo = _grupo_por_id(id_grupo, cursor)
        if not grupo:
            return "no_existe", "El grupo solicitado no existe.", None, {}
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede generar PIN para este grupo.", None, {}

        id_seccion = datos.get("id_seccion")
        id_seccion = int(id_seccion) if id_seccion else None
        if not _seccion_valida_para_grupo(id_seccion, grupo, cursor):
            return "datos_invalidos", "La seccion no pertenece al grado del grupo.", None, {"id_seccion": "Seccion invalida."}
        if not _seccion_asociada_al_grupo(id_seccion, id_grupo, cursor):
            return "datos_invalidos", "La seccion no esta asociada al grupo.", None, {"id_seccion": "Asocie la seccion al grupo primero."}

        pin = _generar_pin_unico(cursor)
        expira = datetime.utcnow() + timedelta(days=PIN_DIAS_VIGENCIA)
        cursor.execute(
            """
            INSERT INTO pines_acceso (pin, id_grupo, id_seccion, estado, fecha_expiracion, creado_por)
            VALUES (%s, %s, %s, 'activo', %s, %s)
            """,
            (pin, id_grupo, id_seccion, expira, usuario["id_usuario"]),
        )
        id_pin = cursor.lastrowid
        conexion.commit()
        return "creado", "PIN generado correctamente.", obtener_pin_por_id(id_pin, cursor), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_pin_por_id(id_pin, cursor):
    # Recupera PIN con datos de grupo, grado y docente.
    cursor.execute(
        """
        SELECT p.*, gr.nombre AS grupo, s.nombre_seccion AS seccion, g.nombre_grado AS grado,
               ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
               CONCAT(u.nombres, ' ', u.apellidos) AS docente
        FROM pines_acceso p
        INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
        INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
        LEFT JOIN secciones s ON s.id_seccion = p.id_seccion
        LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(s.id_institucion_grado, gr.id_institucion_grado)
        LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
        INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
        WHERE p.id_pin = %s
        """,
        (id_pin,),
    )
    return _serializar_pin(cursor.fetchone())


def listar_pines_grupo(usuario, id_grupo):
    # Lista PIN de un grupo validando ownership.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        grupo = _grupo_por_id(id_grupo, cursor)
        if not grupo:
            return "no_existe", "El grupo solicitado no existe.", None, {}
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede consultar PIN de este grupo.", None, {}
        cursor.execute(
            """
            SELECT p.*, gr.nombre AS grupo, s.nombre_seccion AS seccion, g.nombre_grado AS grado,
                   ig.id_institucion_grado, i.id_institucion, i.nombre AS institucion,
                   CONCAT(u.nombres, ' ', u.apellidos) AS docente
            FROM pines_acceso p
            INNER JOIN grupos gr ON gr.id_grupo = p.id_grupo
            INNER JOIN usuarios u ON u.id_usuario = gr.id_docente
            LEFT JOIN secciones s ON s.id_seccion = p.id_seccion
            LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(s.id_institucion_grado, gr.id_institucion_grado)
            LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, gr.id_grado)
            WHERE p.id_grupo = %s
            ORDER BY p.fecha_creacion DESC
            """,
            (id_grupo,),
        )
        return "consultado", "PIN consultados correctamente.", [_serializar_pin(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_pin(usuario, id_pin, estado):
    # Activa o desactiva un PIN existente si el usuario administra su grupo.
    if estado not in ("activo", "inactivo", "expirado"):
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Valor no permitido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        pin_actual = obtener_pin_por_id(id_pin, cursor)
        if not pin_actual:
            return "no_existe", "El PIN solicitado no existe.", None, {}
        grupo = _grupo_por_id(pin_actual["id_grupo"], cursor)
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede modificar este PIN.", None, {}
        cursor.execute(
            "UPDATE pines_acceso SET estado = %s WHERE id_pin = %s",
            (estado, id_pin),
        )
        conexion.commit()
        return "actualizado", "Estado del PIN actualizado.", obtener_pin_por_id(id_pin, cursor), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def regenerar_pin(usuario, id_pin):
    # Invalida el PIN anterior y crea uno nuevo para el mismo grupo/seccion.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        pin_actual = obtener_pin_por_id(id_pin, cursor)
        if not pin_actual:
            return "no_existe", "El PIN solicitado no existe.", None, {}
        grupo = _grupo_por_id(pin_actual["id_grupo"], cursor)
        if not _puede_administrar_grupo(usuario, grupo):
            return "no_autorizado", "No puede regenerar este PIN.", None, {}
        cursor.execute("UPDATE pines_acceso SET estado = 'inactivo' WHERE id_pin = %s", (id_pin,))
        nuevo_pin = _generar_pin_unico(cursor)
        cursor.execute(
            """
            INSERT INTO pines_acceso (pin, id_grupo, id_seccion, estado, fecha_expiracion, creado_por)
            VALUES (%s, %s, %s, 'activo', %s, %s)
            """,
            (
                nuevo_pin,
                pin_actual["id_grupo"],
                pin_actual["id_seccion"],
                datetime.utcnow() + timedelta(days=PIN_DIAS_VIGENCIA),
                usuario["id_usuario"],
            ),
        )
        id_nuevo = cursor.lastrowid
        conexion.commit()
        return "creado", "PIN regenerado correctamente.", obtener_pin_por_id(id_nuevo, cursor), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def validar_pin(pin):
    # Consulta datos visibles antes de confirmar ingreso al grupo.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        fila = _pin_activo_por_codigo(pin, cursor)
        if not fila:
            return "datos_invalidos", "PIN invalido o expirado.", None, {"pin": "PIN no disponible."}
        return "consultado", "PIN valido.", _serializar_pin(fila), {}
    finally:
        cursor.close()
        conexion.close()


def ingresar_con_pin(usuario, pin):
    # Vincula al estudiante autenticado con el grupo del PIN.
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden ingresar con PIN.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        pin_fila = _pin_activo_por_codigo(pin, cursor)
        if not pin_fila:
            return "datos_invalidos", "PIN invalido o expirado.", None, {"pin": "PIN no disponible."}
        data_pin = _serializar_pin(pin_fila)

        cursor.execute(
            """
            UPDATE estudiantes_grupos
            SET estado = 'inactivo',
                fecha_salida = CURRENT_TIMESTAMP
            WHERE id_usuario_estudiante = %s
              AND estado = 'activo'
              AND NOT (id_grupo = %s AND COALESCE(id_seccion, 0) = COALESCE(%s, 0))
            """,
            (usuario["id_usuario"], data_pin["id_grupo"], data_pin["id_seccion"]),
        )

        cursor.execute(
            """
            INSERT INTO estudiantes_grupos (id_usuario_estudiante, id_grupo, id_seccion, estado)
            VALUES (%s, %s, %s, 'activo')
            ON DUPLICATE KEY UPDATE estado = 'activo', fecha_salida = NULL
            """,
            (usuario["id_usuario"], data_pin["id_grupo"], data_pin["id_seccion"]),
        )
        cursor.execute(
            """
            INSERT INTO perfiles_estudiante
                (id_usuario, id_grado, id_institucion, id_institucion_grado, id_seccion, modalidad, personaje)
            VALUES (%s, %s, %s, %s, %s, 'grupo_educativo', 'masculino')
            ON DUPLICATE KEY UPDATE
                id_grado = VALUES(id_grado),
                id_institucion = VALUES(id_institucion),
                id_institucion_grado = VALUES(id_institucion_grado),
                id_seccion = VALUES(id_seccion),
                modalidad = 'grupo_educativo'
            """,
            (
                usuario["id_usuario"],
                data_pin.get("id_grado"),
                data_pin.get("id_institucion"),
                data_pin.get("id_institucion_grado"),
                data_pin.get("id_seccion"),
            ),
        )
        conexion.commit()
        return "creado", "Estudiante vinculado al grupo correctamente.", data_pin, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _perfil_estudiante_institucional(id_usuario, cursor):
    cursor.execute(
        """
        SELECT pe.*, g.orden_visualizacion, g.nombre_grado
        FROM perfiles_estudiante pe
        INNER JOIN grados g ON g.id_grado = pe.id_grado
        WHERE pe.id_usuario = %s
          AND pe.modalidad = 'grupo_educativo'
        LIMIT 1
        """,
        (id_usuario,),
    )
    return cursor.fetchone()


def validar_actualizacion_grado(usuario, pin):
    # Valida un nuevo PIN y devuelve confirmacion sin modificar matricula.
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden actualizar grado.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        perfil = _perfil_estudiante_institucional(usuario["id_usuario"], cursor)
        if not perfil:
            return "no_autorizado", "Esta funcion es solo para estudiantes de grupo educativo.", None, {}
        pin_fila = _pin_activo_por_codigo(pin, cursor)
        if not pin_fila:
            return "datos_invalidos", "PIN invalido o expirado.", None, {"pin": "PIN no disponible."}
        if pin_fila["orden_visualizacion"] == perfil["orden_visualizacion"]:
            return "datos_invalidos", "El PIN corresponde al mismo grado actual.", {"pin": _serializar_pin(pin_fila)}, {"pin": "Mismo grado."}
        if pin_fila["orden_visualizacion"] != perfil["orden_visualizacion"] + 1:
            return "datos_invalidos", "El PIN no corresponde al siguiente grado escolar.", {"pin": _serializar_pin(pin_fila)}, {"pin": "Avance no permitido."}
        return "consultado", "PIN valido para actualizar grado.", {
            "actual": {
                "id_grado": perfil["id_grado"],
                "grado": perfil["nombre_grado"],
            },
            "nuevo": _serializar_pin(pin_fila),
        }, {}
    finally:
        cursor.close()
        conexion.close()


def confirmar_actualizacion_grado(usuario, pin):
    # Cierra la matricula institucional activa e inserta la nueva definida por el PIN.
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden actualizar grado.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        perfil = _perfil_estudiante_institucional(usuario["id_usuario"], cursor)
        if not perfil:
            return "no_autorizado", "Esta funcion es solo para estudiantes de grupo educativo.", None, {}
        pin_fila = _pin_activo_por_codigo(pin, cursor)
        if not pin_fila:
            return "datos_invalidos", "PIN invalido o expirado.", None, {"pin": "PIN no disponible."}
        if pin_fila["orden_visualizacion"] != perfil["orden_visualizacion"] + 1:
            return "datos_invalidos", "Solo se permite avanzar al siguiente grado escolar.", None, {"pin": "Avance no permitido."}

        cursor.execute(
            """
            SELECT id_estudiante_grupo
            FROM estudiantes_grupos
            WHERE id_usuario_estudiante = %s
              AND estado = 'activo'
            FOR UPDATE
            """,
            (usuario["id_usuario"],),
        )
        cursor.fetchall()
        cursor.execute(
            """
            UPDATE estudiantes_grupos
            SET estado = 'inactivo',
                fecha_salida = CURRENT_TIMESTAMP
            WHERE id_usuario_estudiante = %s
              AND estado = 'activo'
            """,
            (usuario["id_usuario"],),
        )
        cursor.execute(
            """
            INSERT INTO estudiantes_grupos (id_usuario_estudiante, id_grupo, id_seccion, estado)
            VALUES (%s, %s, %s, 'activo')
            """,
            (usuario["id_usuario"], pin_fila["id_grupo"], pin_fila["id_seccion"]),
        )
        cursor.execute(
            """
            UPDATE perfiles_estudiante
            SET id_grado = %s,
                id_institucion = %s,
                id_institucion_grado = %s,
                id_seccion = %s,
                modalidad = 'grupo_educativo'
            WHERE id_usuario = %s
            """,
            (
                pin_fila["id_grado"],
                pin_fila.get("id_institucion"),
                pin_fila.get("id_institucion_grado"),
                pin_fila.get("id_seccion"),
                usuario["id_usuario"],
            ),
        )
        conexion.commit()
        return "actualizado", "Grado actualizado correctamente.", _serializar_pin(pin_fila), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()
