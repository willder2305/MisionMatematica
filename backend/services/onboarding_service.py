from db import obtener_conexion
from services.grupos_service import sincronizar_codigos_grado_docente
from services.instituciones_service import (
    SECCION_FALLBACK,
    SeccionAsignadaError,
    configurar_secciones_docente,
    garantizar_grados_institucion,
    normalizar_secciones_configurables,
    obtener_id_institucion_grado,
    obtener_institucion_activa_por_id,
)
from services.personalizacion_service import asegurar_estado_estudiante


MODALIDADES_ESTUDIANTE = ("cuenta_propia", "grupo_educativo")


def obtener_personajes_iniciales_onboarding(usuario):
    """Entrega solo los personajes starter activos para el selector de una cuenta nueva."""
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden consultar personajes iniciales.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id_item, item_key AS personaje, nombre
            FROM tienda_items
            WHERE tipo = 'personaje' AND es_inicial = 1 AND estado = 'activo'
            ORDER BY nombre ASC
            """
        )
        return "consultado", "Personajes iniciales consultados correctamente.", {"personajes": cursor.fetchall()}, {}
    finally:
        cursor.close()
        conexion.close()


def _personaje_inicial_activo(personaje, cursor):
    """Confirma que la elección de onboarding pertenece al catálogo starter activo."""
    cursor.execute(
        """
        SELECT id_item FROM tienda_items
        WHERE tipo = 'personaje' AND item_key = %s AND es_inicial = 1 AND estado = 'activo'
        LIMIT 1
        """,
        (personaje,),
    )
    return cursor.fetchone() is not None


def _serializar_perfil_estudiante(fila):
    # Normaliza el perfil estudiante para respuesta JSON.
    if not fila:
        return None
    return {
        "id_perfil_estudiante": fila["id_perfil_estudiante"],
        "id_usuario": fila["id_usuario"],
        "id_grado": fila["id_grado"],
        "id_institucion": fila.get("id_institucion"),
        "id_institucion_grado": fila.get("id_institucion_grado"),
        "id_seccion": fila.get("id_seccion"),
        "codigo_grado": fila.get("codigo_grado"),
        "nombre_grado": fila.get("nombre_grado"),
        "modalidad": fila["modalidad"],
        "personaje": fila["personaje"],
    }


def _serializar_perfil_docente(fila, grados):
    # Normaliza el perfil docente con los grados asociados.
    if not fila:
        return None
    return {
        "id_perfil_docente": fila["id_perfil_docente"],
        "id_usuario": fila["id_usuario"],
        "id_institucion": fila.get("id_institucion"),
        "institucion": fila.get("institucion"),
        "grados": grados,
    }


def obtener_perfil_onboarding(usuario):
    # Devuelve el perfil segun rol para rehidratar frontend.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if usuario["rol"] == "estudiante":
            cursor.execute(
                """
                SELECT pe.*, g.codigo_grado, g.nombre_grado
                FROM perfiles_estudiante pe
                LEFT JOIN grados g ON g.id_grado = pe.id_grado
                WHERE pe.id_usuario = %s
                """,
                (usuario["id_usuario"],),
            )
            return "consultado", "Perfil consultado correctamente.", {
                "perfil": _serializar_perfil_estudiante(cursor.fetchone())
            }, {}

        if usuario["rol"] == "docente":
            cursor.execute(
                """
                SELECT pd.*, i.nombre AS institucion
                FROM perfiles_docente pd
                LEFT JOIN instituciones i ON i.id_institucion = pd.id_institucion
                WHERE pd.id_usuario = %s
                """,
                (usuario["id_usuario"],),
            )
            perfil = cursor.fetchone()
            cursor.execute(
                """
                SELECT g.id_grado, g.codigo_grado, g.nombre_grado,
                       ig.id_institucion_grado,
                       GROUP_CONCAT(s.nombre_seccion ORDER BY s.nombre_seccion SEPARATOR ',') AS secciones
                FROM docente_grados dg
                LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = dg.id_institucion_grado
                INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, dg.id_grado)
                LEFT JOIN secciones s ON s.id_institucion_grado = ig.id_institucion_grado
                LEFT JOIN docente_secciones ds
                    ON ds.id_seccion = s.id_seccion
                   AND ds.id_docente = dg.id_usuario_docente
                   AND ds.estado = 'activo'
                WHERE dg.id_usuario_docente = %s
                  AND COALESCE(dg.estado, 'activo') = 'activo'
                GROUP BY g.id_grado, g.codigo_grado, g.nombre_grado, ig.id_institucion_grado
                ORDER BY g.orden_visualizacion ASC
                """,
                (usuario["id_usuario"],),
            )
            grados = []
            for grado in cursor.fetchall():
                grados.append({
                    **grado,
                    "secciones": [valor for valor in (grado.get("secciones") or "").split(",") if valor],
                })
            return "consultado", "Perfil consultado correctamente.", {
                "perfil": _serializar_perfil_docente(perfil, grados)
            }, {}

        return "consultado", "Perfil consultado correctamente.", {"perfil": None}, {}
    finally:
        cursor.close()
        conexion.close()


def completar_onboarding(usuario, datos):
    # Completa onboarding segun rol y marca el usuario como configurado.
    if usuario["rol"] == "estudiante":
        return _completar_estudiante(usuario, datos)
    if usuario["rol"] == "docente":
        return _completar_docente(usuario, datos)
    if usuario["rol"] == "administrador":
        return _completar_admin(usuario)
    return "no_autorizado", "Rol no autorizado para onboarding.", None, {}


def _completar_estudiante(usuario, datos):
    # Guarda modalidad, grado opcional y personaje del estudiante.
    errores = {}
    modalidad = (datos.get("modalidad") or "").strip()
    personaje = (datos.get("personaje") or "masculino").strip().lower()
    id_grado = None

    if modalidad not in MODALIDADES_ESTUDIANTE:
        errores["modalidad"] = "Seleccione una modalidad valida."
    if modalidad == "cuenta_propia":
        try:
            id_grado = int(datos.get("id_grado")) if datos.get("id_grado") not in (None, "") else None
        except (TypeError, ValueError):
            errores["id_grado"] = "Grado invalido."

    if errores:
        return "datos_invalidos", "Revise los datos de onboarding.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if not _personaje_inicial_activo(personaje, cursor):
            conexion.rollback()
            return "no_autorizado", "Selecciona uno de los personajes disponibles.", None, {
                "personaje": "Este personaje todavía no está desbloqueado."
            }
        # Desbloquea ambos starters antes de persistir la elección del estudiante.
        asegurar_estado_estudiante(usuario["id_usuario"], cursor)
        if modalidad == "cuenta_propia" and not id_grado:
            cursor.execute(
                """
                SELECT id_grado
                FROM grados
                WHERE codigo_grado = '4P'
                  AND estado = 'activo'
                LIMIT 1
                """
            )
            grado_inicial = cursor.fetchone()
            id_grado = grado_inicial["id_grado"] if grado_inicial else None
        if id_grado:
            cursor.execute("SELECT id_grado FROM grados WHERE id_grado = %s AND estado = 'activo'", (id_grado,))
            if not cursor.fetchone():
                return "datos_invalidos", "Grado no disponible.", None, {"id_grado": "Grado inactivo o inexistente."}

        cursor.execute(
            """
            INSERT INTO perfiles_estudiante (id_usuario, id_grado, modalidad, personaje)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                id_grado = CASE WHEN VALUES(modalidad) = 'cuenta_propia' THEN VALUES(id_grado) ELSE id_grado END,
                id_institucion = CASE WHEN VALUES(modalidad) = 'cuenta_propia' THEN NULL ELSE id_institucion END,
                id_institucion_grado = CASE WHEN VALUES(modalidad) = 'cuenta_propia' THEN NULL ELSE id_institucion_grado END,
                id_seccion = CASE WHEN VALUES(modalidad) = 'cuenta_propia' THEN NULL ELSE id_seccion END,
                modalidad = VALUES(modalidad),
                personaje = VALUES(personaje)
            """,
            (usuario["id_usuario"], id_grado, modalidad, personaje),
        )
        cursor.execute(
            """
            INSERT INTO preferencias_estudiante (id_usuario, personaje_key, modo_mapa)
            VALUES (%s, %s, 'aleatorio')
            ON DUPLICATE KEY UPDATE personaje_key = VALUES(personaje_key)
            """,
            (usuario["id_usuario"], personaje),
        )
        cursor.execute(
            "UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s",
            (usuario["id_usuario"],),
        )
        conexion.commit()
        return obtener_perfil_onboarding(usuario)
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _completar_docente(usuario, datos):
    # Guarda institucion, grados institucionales y secciones A-D del docente.
    errores = {}
    id_institucion = None
    grados = datos.get("grados") or []
    secciones_por_grado = datos.get("secciones_por_grado") or {}
    try:
        id_institucion = int(datos.get("id_institucion"))
    except (TypeError, ValueError):
        errores["id_institucion"] = "Seleccione una institucion existente o cree una nueva."
    try:
        ids_grado = sorted({int(id_grado) for id_grado in grados})
    except (TypeError, ValueError):
        ids_grado = []
        errores["grados"] = "Seleccione grados validos."

    if not ids_grado:
        errores["grados"] = "Seleccione al menos un grado."
    for id_grado in ids_grado:
        try:
            normalizar_secciones_configurables(secciones_por_grado.get(str(id_grado), []))
        except ValueError as error:
            errores[f"secciones_{id_grado}"] = str(error)
    if errores:
        return "datos_invalidos", "Revise los datos de onboarding.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        institucion_fila = obtener_institucion_activa_por_id(id_institucion, cursor)
        if not institucion_fila:
            return "no_encontrado", "La institucion seleccionada no existe.", None, {
                "id_institucion": "Institucion inexistente o inactiva."
            }

        formato = ",".join(["%s"] * len(ids_grado))
        cursor.execute(
            f"SELECT id_grado FROM grados WHERE estado = 'activo' AND id_grado IN ({formato})",
            tuple(ids_grado),
        )
        existentes = {fila["id_grado"] for fila in cursor.fetchall()}
        if existentes != set(ids_grado):
            return "datos_invalidos", "Uno o mas grados no estan disponibles.", None, {"grados": "Grado invalido."}

        garantizar_grados_institucion(institucion_fila["id_institucion"], cursor)

        cursor.execute(
            """
            INSERT INTO perfiles_docente (id_usuario, institucion, id_institucion)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                institucion = VALUES(institucion),
                id_institucion = VALUES(id_institucion)
            """,
            (usuario["id_usuario"], institucion_fila["nombre"], institucion_fila["id_institucion"]),
        )
        cursor.execute(
            """
            UPDATE docente_grados
            SET estado = 'inactivo'
            WHERE id_usuario_docente = %s
            """,
            (usuario["id_usuario"],),
        )
        for id_grado in ids_grado:
            id_institucion_grado = obtener_id_institucion_grado(institucion_fila["id_institucion"], id_grado, cursor)
            if not id_institucion_grado:
                return "datos_invalidos", "No fue posible resolver el grado institucional.", None, {"grados": "Grado institucional no disponible."}
            cursor.execute(
                """
                SELECT 1
                FROM docente_grados
                WHERE id_usuario_docente = %s
                  AND (id_institucion_grado = %s OR id_grado = %s)
                """,
                (usuario["id_usuario"], id_institucion_grado, id_grado),
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO docente_grados (id_usuario_docente, id_grado, id_institucion_grado, estado)
                    VALUES (%s, %s, %s, 'activo')
                    """,
                    (usuario["id_usuario"], id_grado, id_institucion_grado),
                )
            else:
                cursor.execute(
                    """
                    UPDATE docente_grados
                    SET id_grado = %s,
                        id_institucion_grado = %s,
                        estado = 'activo'
                    WHERE id_usuario_docente = %s
                      AND (id_institucion_grado = %s OR id_grado = %s)
                    """,
                    (id_grado, id_institucion_grado, usuario["id_usuario"], id_institucion_grado, id_grado),
                )
            try:
                configurar_secciones_docente(
                    usuario["id_usuario"],
                    id_institucion_grado,
                    secciones_por_grado.get(str(id_grado), []),
                    cursor,
                )
            except SeccionAsignadaError as error:
                if error.nombre_seccion == SECCION_FALLBACK:
                    return "conflicto", "La sección Única de este grado ya está asignada. Selecciona una sección disponible.", None, {
                        "secciones": "Seccion unica no disponible."
                    }
                return "conflicto", str(error), None, {
                    "secciones": f"La seccion {error.nombre_seccion} no esta disponible."
                }
            sincronizar_codigos_grado_docente(usuario["id_usuario"], id_grado, cursor, id_institucion_grado)
        cursor.execute(
            "UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s",
            (usuario["id_usuario"],),
        )
        conexion.commit()
        return obtener_perfil_onboarding(usuario)
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def _completar_admin(usuario):
    # Administrador no requiere datos iniciales adicionales en esta fase.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE usuarios SET onboarding_completado = 1 WHERE id_usuario = %s",
            (usuario["id_usuario"],),
        )
        conexion.commit()
        return "consultado", "Onboarding completado.", {"perfil": None}, {}
    finally:
        cursor.close()
        conexion.close()
