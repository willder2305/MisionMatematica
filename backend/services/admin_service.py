import json
from datetime import datetime

from db import obtener_conexion


ESTADOS_USUARIO = ("activo", "inactivo", "bloqueado")
ROLES_VALIDOS = ("administrador", "docente", "estudiante")
ESTADOS_TEMA = ("activo", "inactivo")
ESTADOS_EJERCICIO = ("borrador", "publicado", "desactivado")
ACCIONES_REGLA = ("mantener", "aumentar", "reducir", "reforzar")
MODALIDADES_REPORTE = ("", "institucional", "independiente")


def _serializar_fecha(valor):
    # Convierte fechas MySQL a texto estable para respuestas JSON.
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _parse_json(valor):
    # Convierte columnas JSON de MySQL a objetos Python de forma tolerante.
    if isinstance(valor, dict):
        return valor
    if not valor:
        return {}
    return json.loads(valor)


def _json_para_db(valor, errores, campo="parametros_json"):
    # Valida objetos JSON enviados desde React antes de guardarlos.
    if isinstance(valor, dict):
        return valor
    if isinstance(valor, str):
        try:
            parsed = json.loads(valor)
        except json.JSONDecodeError:
            errores[campo] = "JSON invalido."
            return {}
        if isinstance(parsed, dict):
            return parsed
    errores[campo] = "Debe enviar un objeto JSON."
    return {}


def _entero(valor, campo, errores, requerido=True):
    # Normaliza IDs numericos y acumula errores por campo.
    if valor in (None, ""):
        if requerido:
            errores[campo] = "Campo obligatorio."
        return None


def _parse_fecha_reporte(valor, campo, errores):
    # Normaliza fechas de filtros de reportes admin.
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "").replace("T", " "))
    except ValueError:
        errores[campo] = "Fecha invalida."
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        errores[campo] = "Valor invalido."
        return None


def _serializar_usuario(fila):
    # Expone datos administrativos sin hashes ni tokens.
    return {
        "id_usuario": fila["id_usuario"],
        "nombres": fila["nombres"],
        "apellidos": fila["apellidos"],
        "correo": fila["correo"],
        "rol": fila["rol"],
        "id_rol": fila["id_rol"],
        "estado": fila["estado"],
        "correo_verificado": bool(fila["correo_verificado"]),
        "onboarding_completado": bool(fila["onboarding_completado"]),
        "ultimo_acceso": _serializar_fecha(fila.get("ultimo_acceso")),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "total_partidas": int(fila.get("total_partidas") or 0),
        "total_intentos": int(fila.get("total_intentos") or 0),
    }


def _serializar_tema(fila):
    # Convierte tema con datos de grado a JSON administrativo.
    return {
        "id_tema": fila["id_tema"],
        "id_grado": fila["id_grado"],
        "nombre_tema": fila["nombre_tema"],
        "descripcion": fila.get("descripcion") or "",
        "estado": fila["estado"],
        "codigo_grado": fila.get("codigo_grado"),
        "nombre_grado": fila.get("nombre_grado"),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
    }


def _serializar_ejercicio(fila, opciones=None):
    # Devuelve ejercicio manual con opciones visibles para administracion.
    return {
        "id_ejercicio": fila["id_ejercicio"],
        "id_tema": fila["id_tema"],
        "id_nivel": fila["id_nivel"],
        "enunciado": fila["enunciado"],
        "tipo_respuesta": fila["tipo_respuesta"],
        "respuesta_correcta": fila["respuesta_correcta"],
        "explicacion": fila.get("explicacion") or "",
        "pista": fila.get("pista") or "",
        "estado": fila["estado"],
        "es_demo": bool(fila.get("es_demo")),
        "nombre_tema": fila.get("nombre_tema"),
        "nombre_grado": fila.get("nombre_grado"),
        "nombre_nivel": fila.get("nombre_nivel"),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
        "opciones": opciones or [],
    }


def _serializar_regla(fila):
    # Normaliza regla adaptativa sin alterar decisiones historicas.
    return {
        "id_regla": fila["id_regla"],
        "codigo_regla": fila["codigo_regla"],
        "nombre": fila["nombre"],
        "descripcion": fila.get("descripcion") or "",
        "prioridad": fila["prioridad"],
        "parametros_json": _parse_json(fila.get("parametros_json")),
        "accion": fila["accion"],
        "estado": fila["estado"],
        "total_decisiones": int(fila.get("total_decisiones") or 0),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
    }


def obtener_panel_admin():
    # Calcula metricas globales de administracion sobre datos reales.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        conteos = {}
        for clave, consulta in {
            "usuarios": "SELECT COUNT(*) AS total FROM usuarios",
            "partidas": "SELECT COUNT(*) AS total FROM partidas_juego",
            "ejercicios_generados": "SELECT COUNT(*) AS total FROM ejercicios_generados",
            "plantillas": "SELECT COUNT(*) AS total FROM plantillas_ejercicios",
            "temas": "SELECT COUNT(*) AS total FROM temas",
            "decisiones_agente": "SELECT COUNT(*) AS total FROM decisiones_agente",
            "reglas_activas": "SELECT COUNT(*) AS total FROM reglas_adaptativas WHERE estado = 'activo'",
        }.items():
            cursor.execute(consulta)
            conteos[clave] = int((cursor.fetchone() or {}).get("total") or 0)

        cursor.execute(
            """
            SELECT r.nombre AS rol, COUNT(u.id_usuario) AS total
            FROM roles r
            LEFT JOIN usuarios u ON u.id_rol = r.id_rol
            GROUP BY r.id_rol, r.nombre
            ORDER BY r.nombre ASC
            """
        )
        conteos["usuarios_por_rol"] = [{"rol": fila["rol"], "total": int(fila["total"])} for fila in cursor.fetchall()]
        return "consultado", "Panel administrador consultado correctamente.", conteos, {}
    finally:
        cursor.close()
        conexion.close()


def listar_usuarios(filtros=None):
    # Lista usuarios con filtros administrativos basicos.
    filtros = filtros or {}
    condiciones = []
    parametros = []
    if filtros.get("rol"):
        condiciones.append("r.nombre = %s")
        parametros.append(filtros["rol"])
    if filtros.get("estado"):
        condiciones.append("u.estado = %s")
        parametros.append(filtros["estado"])
    if filtros.get("busqueda"):
        condiciones.append("(u.nombres LIKE %s OR u.apellidos LIKE %s OR u.correo LIKE %s)")
        termino = f"%{filtros['busqueda']}%"
        parametros.extend([termino, termino, termino])
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT u.*, r.nombre AS rol,
                   (
                       SELECT COUNT(*)
                       FROM partidas_juego p
                       WHERE p.id_usuario = u.id_usuario
                   ) AS total_partidas,
                   (
                       SELECT COUNT(*)
                       FROM intentos_juego i
                       INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
                       WHERE p.id_usuario = u.id_usuario
                   ) AS total_intentos
            FROM usuarios u
            INNER JOIN roles r ON r.id_rol = u.id_rol
            {where}
            ORDER BY u.fecha_creacion DESC
            """,
            tuple(parametros),
        )
        return "consultado", "Usuarios consultados correctamente.", [_serializar_usuario(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_usuario(id_usuario, estado, id_admin):
    # Cambia estado de usuario evitando bloquear la propia cuenta activa.
    if estado not in ESTADOS_USUARIO:
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Valor no permitido."}
    if id_usuario == id_admin and estado != "activo":
        return "datos_invalidos", "No puede desactivar su propio usuario.", None, {"estado": "Accion no permitida."}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE usuarios SET estado = %s WHERE id_usuario = %s", (estado, id_usuario))
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "El usuario solicitado no existe.", None, {}
        if estado != "activo":
            cursor.execute(
                "UPDATE refresh_tokens SET estado = 'revocado', fecha_revocacion = CURRENT_TIMESTAMP WHERE id_usuario = %s",
                (id_usuario,),
            )
        conexion.commit()
        return "actualizado", "Estado de usuario actualizado.", {"id_usuario": id_usuario, "estado": estado}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_rol_usuario(id_usuario, rol, id_admin):
    # Cambia rol de usuario con validacion contra la tabla roles.
    if rol not in ROLES_VALIDOS:
        return "datos_invalidos", "Rol invalido.", None, {"rol": "Valor no permitido."}
    if id_usuario == id_admin:
        return "datos_invalidos", "No puede cambiar su propio rol.", None, {"rol": "Accion no permitida."}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_rol FROM roles WHERE nombre = %s AND estado = 'activo'", (rol,))
        fila_rol = cursor.fetchone()
        if not fila_rol:
            return "datos_invalidos", "Rol no disponible.", None, {"rol": "Rol no configurado."}
        cursor.execute("UPDATE usuarios SET id_rol = %s WHERE id_usuario = %s", (fila_rol["id_rol"], id_usuario))
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "El usuario solicitado no existe.", None, {}
        conexion.commit()
        return "actualizado", "Rol de usuario actualizado.", {"id_usuario": id_usuario, "rol": rol}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def listar_temas_admin(filtros=None):
    # Lista temas para administracion, incluyendo inactivos.
    filtros = filtros or {}
    condiciones = []
    parametros = []
    if filtros.get("id_grado"):
        condiciones.append("t.id_grado = %s")
        parametros.append(filtros["id_grado"])
    if filtros.get("estado"):
        condiciones.append("t.estado = %s")
        parametros.append(filtros["estado"])
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT t.*, g.codigo_grado, g.nombre_grado
            FROM temas t
            INNER JOIN grados g ON g.id_grado = t.id_grado
            {where}
            ORDER BY g.orden_visualizacion ASC, t.nombre_tema ASC
            """,
            tuple(parametros),
        )
        return "consultado", "Temas consultados correctamente.", [_serializar_tema(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()


def _validar_tema(datos):
    errores = {}
    id_grado = _entero(datos.get("id_grado"), "id_grado", errores)
    nombre = (datos.get("nombre_tema") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    estado = (datos.get("estado") or "activo").strip()
    if len(nombre) < 2:
        errores["nombre_tema"] = "Ingrese un nombre valido."
    if estado not in ESTADOS_TEMA:
        errores["estado"] = "Estado invalido."
    return {"id_grado": id_grado, "nombre_tema": nombre, "descripcion": descripcion, "estado": estado}, errores


def crear_tema_admin(datos):
    # Crea tema curricular asociado a un grado.
    datos_limpios, errores = _validar_tema(datos)
    if errores:
        return "datos_invalidos", "Revise los datos del tema.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM grados WHERE id_grado = %s", (datos_limpios["id_grado"],))
        if not cursor.fetchone():
            return "datos_invalidos", "Grado no disponible.", None, {"id_grado": "Grado invalido."}
        cursor.execute(
            """
            INSERT INTO temas (id_grado, nombre_tema, descripcion, estado)
            VALUES (%s, %s, %s, %s)
            """,
            (datos_limpios["id_grado"], datos_limpios["nombre_tema"], datos_limpios["descripcion"], datos_limpios["estado"]),
        )
        id_tema = cursor.lastrowid
        conexion.commit()
        return "creado", "Tema creado correctamente.", {"id_tema": id_tema}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_tema_admin(id_tema, datos):
    # Actualiza tema sin borrar ejercicios ni historial asociado.
    datos_limpios, errores = _validar_tema(datos)
    if errores:
        return "datos_invalidos", "Revise los datos del tema.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT 1 FROM temas WHERE id_tema = %s", (id_tema,))
        if not cursor.fetchone():
            return "no_existe", "El tema solicitado no existe.", None, {}
        cursor.execute(
            """
            UPDATE temas
            SET id_grado = %s,
                nombre_tema = %s,
                descripcion = %s,
                estado = %s
            WHERE id_tema = %s
            """,
            (
                datos_limpios["id_grado"],
                datos_limpios["nombre_tema"],
                datos_limpios["descripcion"],
                datos_limpios["estado"],
                id_tema,
            ),
        )
        conexion.commit()
        return "actualizado", "Tema actualizado correctamente.", {"id_tema": id_tema}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_tema_admin(id_tema, estado):
    # Activa o desactiva un tema sin eliminar datos historicos.
    if estado not in ESTADOS_TEMA:
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Valor no permitido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE temas SET estado = %s WHERE id_tema = %s", (estado, id_tema))
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "El tema solicitado no existe.", None, {}
        conexion.commit()
        return "actualizado", "Estado de tema actualizado.", {"id_tema": id_tema, "estado": estado}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _opciones_ejercicio(id_ejercicio, cursor):
    cursor.execute(
        """
        SELECT id_opcion, texto_opcion, orden_visualizacion
        FROM opciones_ejercicio
        WHERE id_ejercicio = %s
        ORDER BY orden_visualizacion ASC, id_opcion ASC
        """,
        (id_ejercicio,),
    )
    return cursor.fetchall()


def listar_ejercicios_admin(filtros=None):
    # Lista ejercicios manuales con filtros para administracion.
    filtros = filtros or {}
    condiciones = []
    parametros = []
    if filtros.get("id_tema"):
        condiciones.append("e.id_tema = %s")
        parametros.append(filtros["id_tema"])
    if filtros.get("id_nivel"):
        condiciones.append("e.id_nivel = %s")
        parametros.append(filtros["id_nivel"])
    if filtros.get("estado"):
        condiciones.append("e.estado = %s")
        parametros.append(filtros["estado"])
    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT e.*, t.nombre_tema, g.nombre_grado, n.nombre AS nombre_nivel
            FROM ejercicios e
            INNER JOIN temas t ON t.id_tema = e.id_tema
            INNER JOIN grados g ON g.id_grado = t.id_grado
            INNER JOIN niveles_dificultad n ON n.id_nivel = e.id_nivel
            {where}
            ORDER BY e.fecha_creacion DESC, e.id_ejercicio DESC
            LIMIT 200
            """,
            tuple(parametros),
        )
        ejercicios = []
        for fila in cursor.fetchall():
            ejercicios.append(_serializar_ejercicio(fila, _opciones_ejercicio(fila["id_ejercicio"], cursor)))
        return "consultado", "Ejercicios consultados correctamente.", ejercicios, {}
    finally:
        cursor.close()
        conexion.close()


def _validar_ejercicio(datos):
    errores = {}
    id_tema = _entero(datos.get("id_tema"), "id_tema", errores)
    id_nivel = _entero(datos.get("id_nivel"), "id_nivel", errores)
    enunciado = (datos.get("enunciado") or "").strip()
    tipo_respuesta = (datos.get("tipo_respuesta") or "numerica").strip()
    respuesta_correcta = str(datos.get("respuesta_correcta") or "").strip()
    explicacion = (datos.get("explicacion") or "").strip()
    pista = (datos.get("pista") or "").strip()
    estado = (datos.get("estado") or "borrador").strip()
    opciones = datos.get("opciones") or []

    if len(enunciado) < 3:
        errores["enunciado"] = "Ingrese un enunciado valido."
    if tipo_respuesta not in ("seleccion_multiple", "numerica"):
        errores["tipo_respuesta"] = "Tipo de respuesta invalido."
    if not respuesta_correcta:
        errores["respuesta_correcta"] = "Ingrese la respuesta correcta."
    if estado not in ESTADOS_EJERCICIO:
        errores["estado"] = "Estado invalido."
    if not isinstance(opciones, list):
        errores["opciones"] = "Las opciones deben enviarse como lista."
        opciones = []
    opciones_limpias = [str(opcion).strip() for opcion in opciones if str(opcion).strip()]
    if tipo_respuesta == "seleccion_multiple" and len(opciones_limpias) < 2:
        errores["opciones"] = "Ingrese al menos dos opciones."
    if tipo_respuesta == "seleccion_multiple" and respuesta_correcta not in opciones_limpias:
        errores["respuesta_correcta"] = "La respuesta debe estar entre las opciones."

    return {
        "id_tema": id_tema,
        "id_nivel": id_nivel,
        "enunciado": enunciado,
        "tipo_respuesta": tipo_respuesta,
        "respuesta_correcta": respuesta_correcta,
        "explicacion": explicacion,
        "pista": pista,
        "estado": estado,
        "opciones": opciones_limpias,
    }, errores


def _guardar_opciones(id_ejercicio, opciones, cursor):
    # Conserva opciones historicas: las retiradas quedan inactivas.
    cursor.execute(
        """
        UPDATE opciones_ejercicio
        SET estado = 'inactivo',
            fecha_fin = CURRENT_TIMESTAMP
        WHERE id_ejercicio = %s
        """,
        (id_ejercicio,),
    )
    for indice, opcion in enumerate(opciones, start=1):
        cursor.execute(
            """
            INSERT INTO opciones_ejercicio (id_ejercicio, texto_opcion, orden_visualizacion, estado, fecha_fin)
            VALUES (%s, %s, %s, 'activo', NULL)
            ON DUPLICATE KEY UPDATE
                texto_opcion = VALUES(texto_opcion),
                orden_visualizacion = VALUES(orden_visualizacion),
                estado = 'activo',
                fecha_fin = NULL
            """,
            (id_ejercicio, opcion, indice),
        )


def crear_ejercicio_admin(datos):
    # Crea ejercicio manual publicado o en borrador.
    datos_limpios, errores = _validar_ejercicio(datos)
    if errores:
        return "datos_invalidos", "Revise los datos del ejercicio.", None, errores
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM temas WHERE id_tema = %s", (datos_limpios["id_tema"],))
        if not cursor.fetchone():
            return "datos_invalidos", "Tema no disponible.", None, {"id_tema": "Tema invalido."}
        cursor.execute("SELECT 1 FROM niveles_dificultad WHERE id_nivel = %s", (datos_limpios["id_nivel"],))
        if not cursor.fetchone():
            return "datos_invalidos", "Nivel no disponible.", None, {"id_nivel": "Nivel invalido."}
        cursor.execute(
            """
            INSERT INTO ejercicios
                (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                datos_limpios["id_tema"],
                datos_limpios["id_nivel"],
                datos_limpios["enunciado"],
                datos_limpios["tipo_respuesta"],
                datos_limpios["respuesta_correcta"],
                datos_limpios["explicacion"],
                datos_limpios["pista"],
                datos_limpios["estado"],
            ),
        )
        id_ejercicio = cursor.lastrowid
        if datos_limpios["tipo_respuesta"] == "seleccion_multiple":
            _guardar_opciones(id_ejercicio, datos_limpios["opciones"], cursor)
        conexion.commit()
        return "creado", "Ejercicio creado correctamente.", {"id_ejercicio": id_ejercicio}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_ejercicio_admin(id_ejercicio, datos):
    # Actualiza ejercicio manual y reemplaza opciones de seleccion multiple.
    datos_limpios, errores = _validar_ejercicio(datos)
    if errores:
        return "datos_invalidos", "Revise los datos del ejercicio.", None, errores
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM ejercicios WHERE id_ejercicio = %s", (id_ejercicio,))
        if not cursor.fetchone():
            return "no_existe", "El ejercicio solicitado no existe.", None, {}
        cursor.execute(
            """
            UPDATE ejercicios
            SET id_tema = %s,
                id_nivel = %s,
                enunciado = %s,
                tipo_respuesta = %s,
                respuesta_correcta = %s,
                explicacion = %s,
                pista = %s,
                estado = %s
            WHERE id_ejercicio = %s
            """,
            (
                datos_limpios["id_tema"],
                datos_limpios["id_nivel"],
                datos_limpios["enunciado"],
                datos_limpios["tipo_respuesta"],
                datos_limpios["respuesta_correcta"],
                datos_limpios["explicacion"],
                datos_limpios["pista"],
                datos_limpios["estado"],
                id_ejercicio,
            ),
        )
        _guardar_opciones(id_ejercicio, datos_limpios["opciones"] if datos_limpios["tipo_respuesta"] == "seleccion_multiple" else [], cursor)
        conexion.commit()
        return "actualizado", "Ejercicio actualizado correctamente.", {"id_ejercicio": id_ejercicio}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_ejercicio_admin(id_ejercicio, estado):
    # Cambia estado de ejercicio sin eliminarlo ni alterar intentos historicos.
    if estado not in ESTADOS_EJERCICIO:
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Valor no permitido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE ejercicios SET estado = %s WHERE id_ejercicio = %s", (estado, id_ejercicio))
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "El ejercicio solicitado no existe.", None, {}
        conexion.commit()
        return "actualizado", "Estado de ejercicio actualizado.", {"id_ejercicio": id_ejercicio, "estado": estado}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def listar_reglas_admin():
    # Lista reglas adaptativas y cantidad de decisiones historicas por regla.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT r.*,
                   (
                       SELECT COUNT(*)
                       FROM decisiones_agente d
                       WHERE d.regla_aplicada = r.codigo_regla
                   ) AS total_decisiones
            FROM reglas_adaptativas r
            ORDER BY r.prioridad ASC, r.id_regla ASC
            """
        )
        return "consultado", "Reglas consultadas correctamente.", [_serializar_regla(fila) for fila in cursor.fetchall()], {}
    finally:
        cursor.close()
        conexion.close()


def actualizar_regla_admin(id_regla, datos):
    # Actualiza parametros activos de una regla sin tocar decisiones existentes.
    errores = {}
    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    prioridad = _entero(datos.get("prioridad"), "prioridad", errores)
    parametros = _json_para_db(datos.get("parametros_json"), errores)
    accion = (datos.get("accion") or "").strip()
    estado = (datos.get("estado") or "activo").strip()
    if len(nombre) < 2:
        errores["nombre"] = "Ingrese un nombre valido."
    if accion not in ACCIONES_REGLA:
        errores["accion"] = "Accion invalida."
    if estado not in ESTADOS_TEMA:
        errores["estado"] = "Estado invalido."
    if errores:
        return "datos_invalidos", "Revise los datos de la regla.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT 1 FROM reglas_adaptativas WHERE id_regla = %s", (id_regla,))
        if not cursor.fetchone():
            return "no_existe", "La regla solicitada no existe.", None, {}
        cursor.execute(
            """
            UPDATE reglas_adaptativas
            SET nombre = %s,
                descripcion = %s,
                prioridad = %s,
                parametros_json = %s,
                accion = %s,
                estado = %s
            WHERE id_regla = %s
            """,
            (nombre, descripcion, prioridad, json.dumps(parametros), accion, estado, id_regla),
        )
        conexion.commit()
        return "actualizado", "Regla actualizada correctamente.", {"id_regla": id_regla}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_regla_admin(id_regla, estado):
    # Activa o desactiva una regla para decisiones futuras.
    if estado not in ESTADOS_TEMA:
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Valor no permitido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE reglas_adaptativas SET estado = %s WHERE id_regla = %s", (estado, id_regla))
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "La regla solicitada no existe.", None, {}
        conexion.commit()
        return "actualizado", "Estado de regla actualizado.", {"id_regla": id_regla, "estado": estado}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _validar_filtros_reporte_admin(filtros):
    # Valida filtros institucionales sin aceptar id_grupo como entrada.
    errores = {}
    modalidad = (filtros.get("modalidad") or "").strip()
    if modalidad not in ("", "institucional", "independiente"):
        errores["modalidad"] = "Modalidad invalida."
    datos = {
        "modalidad": modalidad,
        "id_institucion": _entero(filtros.get("id_institucion"), "id_institucion", errores, requerido=False),
        "id_grado_base": _entero(filtros.get("id_grado_base"), "id_grado_base", errores, requerido=False),
        "id_institucion_grado": _entero(filtros.get("id_institucion_grado"), "id_institucion_grado", errores, requerido=False),
        "id_seccion": _entero(filtros.get("id_seccion"), "id_seccion", errores, requerido=False),
        "id_docente": _entero(filtros.get("id_docente"), "id_docente", errores, requerido=False),
        "id_estudiante": _entero(filtros.get("id_estudiante"), "id_estudiante", errores, requerido=False),
        "id_tema": _entero(filtros.get("id_tema"), "id_tema", errores, requerido=False),
        "id_asignacion": _entero(filtros.get("id_asignacion"), "id_asignacion", errores, requerido=False),
        "fecha_inicio": _parse_fecha_reporte(filtros.get("fecha_inicio"), "fecha_inicio", errores),
        "fecha_fin": _parse_fecha_reporte(filtros.get("fecha_fin"), "fecha_fin", errores),
        "limite": min(max(_entero(filtros.get("limite") or 50, "limite", errores) or 50, 1), 200),
        "offset": max(_entero(filtros.get("offset") or 0, "offset", errores) or 0, 0),
    }
    if "id_grupo" in filtros and filtros.get("id_grupo") not in (None, ""):
        errores["id_grupo"] = "id_grupo es legacy y no forma parte de reportes nuevos."
    if datos["fecha_inicio"] and datos["fecha_fin"] and datos["fecha_inicio"] > datos["fecha_fin"]:
        errores["fecha_fin"] = "La fecha final debe ser posterior a la inicial."
    return datos, errores


def _where_reporte_admin(filtros):
    # Construye filtros SQL del reporte institucional usando el modelo nuevo.
    condiciones = ["p.id_usuario IS NOT NULL"]
    parametros = []
    if filtros["modalidad"] == "institucional":
        condiciones.append("pe.modalidad = 'grupo_educativo'")
    elif filtros["modalidad"] == "independiente":
        condiciones.append("(pe.modalidad = 'cuenta_propia' OR pe.modalidad IS NULL)")
    if filtros["id_institucion"]:
        condiciones.append("ig.id_institucion = %s")
        parametros.append(filtros["id_institucion"])
    if filtros["id_grado_base"]:
        condiciones.append("gb.id_grado = %s")
        parametros.append(filtros["id_grado_base"])
    if filtros["id_institucion_grado"]:
        condiciones.append("ig.id_institucion_grado = %s")
        parametros.append(filtros["id_institucion_grado"])
    if filtros["id_seccion"]:
        condiciones.append("sec.id_seccion = %s")
        parametros.append(filtros["id_seccion"])
    if filtros["id_docente"]:
        condiciones.append("a.id_docente = %s")
        parametros.append(filtros["id_docente"])
    if filtros["id_estudiante"]:
        condiciones.append("p.id_usuario = %s")
        parametros.append(filtros["id_estudiante"])
    if filtros["id_tema"]:
        condiciones.append("p.id_tema = %s")
        parametros.append(filtros["id_tema"])
    if filtros["id_asignacion"]:
        condiciones.append("p.id_asignacion = %s")
        parametros.append(filtros["id_asignacion"])
    if filtros["fecha_inicio"]:
        condiciones.append("COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio) >= %s")
        parametros.append(filtros["fecha_inicio"])
    if filtros["fecha_fin"]:
        condiciones.append("COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio) <= %s")
        parametros.append(filtros["fecha_fin"])
    return " AND ".join(condiciones), parametros


def _from_reporte_admin():
    # Define el origen comun de reportes sin usar grupos como eje.
    return """
        FROM partidas_juego p
        INNER JOIN usuarios est ON est.id_usuario = p.id_usuario
        LEFT JOIN perfiles_estudiante pe ON pe.id_usuario = p.id_usuario
        LEFT JOIN asignaciones a ON a.id_asignacion = p.id_asignacion
        LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(a.id_institucion_grado, pe.id_institucion_grado)
        LEFT JOIN instituciones inst ON inst.id_institucion = ig.id_institucion
        LEFT JOIN secciones sec ON sec.id_seccion = COALESCE(a.id_seccion, pe.id_seccion)
        LEFT JOIN usuarios doc ON doc.id_usuario = a.id_docente
        LEFT JOIN temas t ON t.id_tema = p.id_tema
        LEFT JOIN grados gb ON gb.id_grado = COALESCE(t.id_grado, ig.id_grado_base, pe.id_grado)
        LEFT JOIN intentos_juego ij ON ij.id_partida = p.id_partida
        LEFT JOIN niveles_dificultad nv ON nv.id_nivel = p.id_nivel_actual
        LEFT JOIN (
            SELECT d.*
            FROM decisiones_agente d
            INNER JOIN (
                SELECT id_partida, MAX(id_decision) AS id_decision
                FROM decisiones_agente
                GROUP BY id_partida
            ) ult ON ult.id_decision = d.id_decision
        ) da ON da.id_partida = p.id_partida
        LEFT JOIN niveles_dificultad na ON na.id_nivel = da.nivel_anterior
        LEFT JOIN niveles_dificultad nn ON nn.id_nivel = da.nivel_nuevo
    """


def listar_catalogos_reportes_admin(filtros=None):
    # Devuelve catalogos filtrables para reportes admin en cascada.
    datos, errores = _validar_filtros_reporte_admin(filtros or {})
    if errores:
        return "datos_invalidos", "Revise los filtros del reporte.", None, errores
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_institucion, nombre FROM instituciones WHERE estado = 'activo' ORDER BY nombre")
        instituciones = cursor.fetchall()
        cursor.execute("SELECT id_grado AS id_grado_base, nombre_grado FROM grados WHERE estado = 'activo' ORDER BY orden_visualizacion")
        grados_base = cursor.fetchall()

        condiciones_ig = ["ig.estado = 'activo'"]
        parametros_ig = []
        if datos["id_institucion"]:
            condiciones_ig.append("ig.id_institucion = %s")
            parametros_ig.append(datos["id_institucion"])
        if datos["id_grado_base"]:
            condiciones_ig.append("ig.id_grado_base = %s")
            parametros_ig.append(datos["id_grado_base"])
        cursor.execute(
            f"""
            SELECT ig.id_institucion_grado, ig.id_institucion, ig.id_grado_base,
                   i.nombre AS institucion, g.nombre_grado
            FROM institucion_grados ig
            INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = ig.id_grado_base
            WHERE {' AND '.join(condiciones_ig)}
            ORDER BY i.nombre, g.orden_visualizacion
            """,
            tuple(parametros_ig),
        )
        grados_institucionales = cursor.fetchall()

        condiciones_sec = ["s.estado = 'activo'"]
        parametros_sec = []
        if datos["id_institucion_grado"]:
            condiciones_sec.append("s.id_institucion_grado = %s")
            parametros_sec.append(datos["id_institucion_grado"])
        cursor.execute(
            f"""
            SELECT s.id_seccion, s.id_institucion_grado, s.nombre_seccion
            FROM secciones s
            WHERE {' AND '.join(condiciones_sec)}
            ORDER BY FIELD(s.nombre_seccion, 'A', 'B', 'C', 'D', 'Única'), s.nombre_seccion
            """,
            tuple(parametros_sec),
        )
        secciones = cursor.fetchall()

        cursor.execute(
            """
            SELECT u.id_usuario AS id_docente, CONCAT(u.nombres, ' ', u.apellidos) AS docente,
                   pd.id_institucion
            FROM usuarios u
            INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'docente'
            LEFT JOIN perfiles_docente pd ON pd.id_usuario = u.id_usuario
            WHERE u.estado = 'activo'
              AND (%s IS NULL OR pd.id_institucion = %s)
            ORDER BY docente
            """,
            (datos["id_institucion"], datos["id_institucion"]),
        )
        docentes = cursor.fetchall()

        cursor.execute(
            """
            SELECT u.id_usuario AS id_estudiante, CONCAT(u.nombres, ' ', u.apellidos) AS estudiante,
                   pe.modalidad, pe.id_institucion, pe.id_institucion_grado, pe.id_seccion
            FROM usuarios u
            INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'estudiante'
            LEFT JOIN perfiles_estudiante pe ON pe.id_usuario = u.id_usuario
            WHERE u.estado = 'activo'
              AND (%s = '' OR (%s = 'institucional' AND pe.modalidad = 'grupo_educativo') OR (%s = 'independiente' AND (pe.modalidad = 'cuenta_propia' OR pe.modalidad IS NULL)))
              AND (%s IS NULL OR pe.id_institucion = %s)
              AND (%s IS NULL OR pe.id_institucion_grado = %s)
              AND (%s IS NULL OR pe.id_seccion = %s)
            ORDER BY estudiante
            LIMIT 500
            """,
            (
                datos["modalidad"], datos["modalidad"], datos["modalidad"],
                datos["id_institucion"], datos["id_institucion"],
                datos["id_institucion_grado"], datos["id_institucion_grado"],
                datos["id_seccion"], datos["id_seccion"],
            ),
        )
        estudiantes = cursor.fetchall()

        cursor.execute(
            """
            SELECT id_tema, id_grado AS id_grado_base, nombre_tema
            FROM temas
            WHERE estado = 'activo'
              AND (%s IS NULL OR id_grado = %s)
            ORDER BY nombre_tema
            """,
            (datos["id_grado_base"], datos["id_grado_base"]),
        )
        temas = cursor.fetchall()

        cursor.execute(
            """
            SELECT a.id_asignacion, a.id_institucion_grado, a.id_seccion, a.id_docente, a.nombre
            FROM asignaciones a
            WHERE (%s IS NULL OR a.id_institucion_grado = %s)
              AND (%s IS NULL OR a.id_seccion = %s)
              AND (%s IS NULL OR a.id_docente = %s)
            ORDER BY a.fecha_creacion DESC
            LIMIT 500
            """,
            (
                datos["id_institucion_grado"], datos["id_institucion_grado"],
                datos["id_seccion"], datos["id_seccion"],
                datos["id_docente"], datos["id_docente"],
            ),
        )
        asignaciones = cursor.fetchall()

        return "consultado", "Catalogos de reportes consultados correctamente.", {
            "instituciones": instituciones,
            "grados_base": grados_base,
            "grados_institucionales": grados_institucionales,
            "secciones": secciones,
            "docentes": docentes,
            "estudiantes": estudiantes,
            "temas": temas,
            "asignaciones": asignaciones,
        }, {}
    finally:
        cursor.close()
        conexion.close()


def obtener_reporte_institucional_admin(filtros=None):
    # Genera reporte paginado de actividad academica por modelo institucional.
    datos, errores = _validar_filtros_reporte_admin(filtros or {})
    if errores:
        return "datos_invalidos", "Revise los filtros del reporte.", None, errores
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        origen = _from_reporte_admin()
        where, parametros = _where_reporte_admin(datos)
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT p.id_partida) AS partidas,
                   COUNT(DISTINCT p.id_usuario) AS estudiantes,
                   COUNT(ij.id_intento) AS intentos,
                   COALESCE(SUM(CASE WHEN ij.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS correctos,
                   COALESCE(SUM(CASE WHEN ij.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS incorrectos,
                   COUNT(DISTINCT p.id_asignacion) AS asignaciones,
                   MAX(COALESCE(ij.fecha_respuesta, p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio)) AS ultima_actividad
            {origen}
            WHERE {where}
            """,
            tuple(parametros),
        )
        resumen = cursor.fetchone() or {}
        intentos = int(resumen.get("intentos") or 0)
        correctos = int(resumen.get("correctos") or 0)

        cursor.execute(
            f"""
            SELECT p.id_usuario AS id_estudiante,
                   CONCAT(est.nombres, ' ', est.apellidos) AS estudiante,
                   CASE WHEN pe.modalidad = 'grupo_educativo' THEN 'Institucional' ELSE 'Independiente' END AS modalidad,
                   inst.id_institucion,
                   inst.nombre AS institucion,
                   a.id_docente,
                   CONCAT(doc.nombres, ' ', doc.apellidos) AS docente,
                   gb.id_grado AS id_grado_base,
                   gb.nombre_grado AS grado,
                   ig.id_institucion_grado,
                   sec.id_seccion,
                   sec.nombre_seccion AS seccion,
                   a.id_asignacion,
                   a.nombre AS asignacion,
                   t.id_tema,
                   t.nombre_tema AS tema,
                   COUNT(ij.id_intento) AS intentos,
                   COALESCE(SUM(CASE WHEN ij.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS correctos,
                   COALESCE(SUM(CASE WHEN ij.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS incorrectos,
                   COUNT(DISTINCT CASE WHEN p.estado = 'completada' THEN p.id_partida END) AS partidas_completadas,
                   MAX(nv.nombre) AS nivel_actual,
                   MAX(COALESCE(ij.fecha_respuesta, p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio)) AS ultima_actividad,
                   MAX(da.accion) AS ultima_decision,
                   MAX(na.nombre) AS nivel_anterior,
                   MAX(nn.nombre) AS nivel_nuevo,
                   MAX(da.motivo) AS motivo,
                   MAX(da.fecha_decision) AS fecha_decision
            {origen}
            WHERE {where}
            GROUP BY p.id_usuario, estudiante, modalidad, inst.id_institucion, inst.nombre,
                     a.id_docente, docente, gb.id_grado, gb.nombre_grado,
                     ig.id_institucion_grado, sec.id_seccion, sec.nombre_seccion,
                     a.id_asignacion, a.nombre, t.id_tema, t.nombre_tema
            ORDER BY ultima_actividad DESC, estudiante ASC
            LIMIT %s OFFSET %s
            """,
            tuple(parametros + [datos["limite"], datos["offset"]]),
        )
        filas = []
        for fila in cursor.fetchall():
            fila_intentos = int(fila.get("intentos") or 0)
            fila_correctos = int(fila.get("correctos") or 0)
            filas.append({
                "id_estudiante": fila["id_estudiante"],
                "estudiante": fila["estudiante"],
                "modalidad": fila["modalidad"],
                "id_institucion": fila.get("id_institucion"),
                "institucion": fila.get("institucion"),
                "id_docente": fila.get("id_docente"),
                "docente": fila.get("docente"),
                "id_grado_base": fila.get("id_grado_base"),
                "grado": fila.get("grado"),
                "id_institucion_grado": fila.get("id_institucion_grado"),
                "id_seccion": fila.get("id_seccion"),
                "seccion": fila.get("seccion"),
                "id_asignacion": fila.get("id_asignacion"),
                "asignacion": fila.get("asignacion"),
                "id_tema": fila.get("id_tema"),
                "tema": fila.get("tema"),
                "intentos": fila_intentos,
                "correctos": fila_correctos,
                "incorrectos": int(fila.get("incorrectos") or 0),
                "precision": round((fila_correctos / fila_intentos) * 100, 2) if fila_intentos else 0,
                "partidas_completadas": int(fila.get("partidas_completadas") or 0),
                "nivel_actual": fila.get("nivel_actual"),
                "ultima_actividad": _serializar_fecha(fila.get("ultima_actividad")),
                "ultima_decision": fila.get("ultima_decision"),
                "nivel_anterior": fila.get("nivel_anterior"),
                "nivel_nuevo": fila.get("nivel_nuevo"),
                "motivo": fila.get("motivo"),
                "fecha_decision": _serializar_fecha(fila.get("fecha_decision")),
            })

        cursor.execute(f"SELECT COUNT(DISTINCT p.id_partida) AS total {origen} WHERE {where}", tuple(parametros))
        total = int((cursor.fetchone() or {}).get("total") or 0)
        return "consultado", "Reporte institucional consultado correctamente.", {
            "resumen": {
                "estudiantes": int(resumen.get("estudiantes") or 0),
                "intentos": intentos,
                "precision_promedio": round((correctos / intentos) * 100, 2) if intentos else 0,
                "partidas": int(resumen.get("partidas") or 0),
                "actividad_periodo": _serializar_fecha(resumen.get("ultima_actividad")),
                "asignaciones": int(resumen.get("asignaciones") or 0),
                "correctos": correctos,
                "incorrectos": int(resumen.get("incorrectos") or 0),
            },
            "filas": filas,
            "paginacion": {"total": total, "limite": datos["limite"], "offset": datos["offset"]},
        }, {}
    finally:
        cursor.close()
        conexion.close()
