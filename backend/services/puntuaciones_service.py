"""Puntuaciones acumuladas por tema y clasificación de estudiantes.

La puntuación es académica y se mantiene independiente del monedero, las
compras y las recompensas de una partida.
"""

from db import obtener_conexion


PUNTOS_POR_ACIERTO = 2
LIMITE_POR_DEFECTO = 25
LIMITE_MAXIMO = 100


def puntos_por_aciertos(total_aciertos):
    """Convierte aciertos válidos en puntuación académica sin valores negativos."""
    return max(int(total_aciertos or 0), 0) * PUNTOS_POR_ACIERTO


def acreditar_puntuacion_tema(id_usuario, id_tema, es_correcta, cursor):
    """Acredita dos puntos al tema real de un intento correcto ya persistido.

    Debe ejecutarse en la misma transacción que el intento. La idempotencia se
    garantiza por el `request_id` único del intento, que se verifica antes de
    llegar a esta función.
    """
    if not es_correcta:
        return 0

    cursor.execute(
        """
        INSERT INTO progreso_tema_estudiante
            (id_usuario, id_tema, puntos_acumulados, aciertos_puntuados)
        VALUES (%s, %s, %s, 1)
        ON DUPLICATE KEY UPDATE
            puntos_acumulados = puntos_acumulados + VALUES(puntos_acumulados),
            aciertos_puntuados = aciertos_puntuados + 1
        """,
        (id_usuario, id_tema, PUNTOS_POR_ACIERTO),
    )
    return PUNTOS_POR_ACIERTO


def _entero_acotado(valor, defecto, minimo, maximo):
    """Normaliza paginación sin aceptar valores fuera de los límites públicos."""
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return defecto
    return min(max(numero, minimo), maximo)


def _tema_activo(id_tema, cursor):
    """Obtiene solo un tema curricular que continúa activo para la clasificación."""
    cursor.execute(
        """
        SELECT t.id_tema, t.nombre_tema
        FROM temas t
        INNER JOIN grados g ON g.id_grado = t.id_grado
        WHERE t.id_tema = %s
          AND t.estado = 'activo'
          AND g.estado = 'activo'
        LIMIT 1
        """,
        (id_tema,),
    )
    return cursor.fetchone()


def _grupo_canonico_estudiante(id_usuario, cursor):
    """Resuelve la matrícula institucional activa sin depender de parámetros web."""
    cursor.execute(
        """
        SELECT pe.id_institucion, pe.id_institucion_grado, pe.id_seccion
        FROM perfiles_estudiante pe
        INNER JOIN instituciones i
            ON i.id_institucion = pe.id_institucion
           AND i.estado = 'activo'
        INNER JOIN institucion_grados ig
            ON ig.id_institucion_grado = pe.id_institucion_grado
           AND ig.id_institucion = pe.id_institucion
           AND ig.estado = 'activo'
        INNER JOIN secciones s
            ON s.id_seccion = pe.id_seccion
           AND s.id_institucion_grado = pe.id_institucion_grado
           AND s.estado = 'activo'
        WHERE pe.id_usuario = %s
          AND pe.modalidad = 'grupo_educativo'
        LIMIT 1
        """,
        (id_usuario,),
    )
    return cursor.fetchone()


def _puntuacion_usuario(id_usuario, id_tema, cursor):
    """Consulta la puntuación del usuario actual aun cuando todavía sea cero."""
    cursor.execute(
        """
        SELECT COALESCE(pte.puntos_acumulados, 0) AS puntos
        FROM usuarios u
        LEFT JOIN progreso_tema_estudiante pte
            ON pte.id_usuario = u.id_usuario
           AND pte.id_tema = %s
        WHERE u.id_usuario = %s
        LIMIT 1
        """,
        (id_tema, id_usuario),
    )
    fila = cursor.fetchone() or {}
    return int(fila.get("puntos") or 0)


def _consulta_clasificacion(id_tema, grupo, limite, offset, cursor):
    """Lista participantes activos con puntuación positiva sin exponer datos privados."""
    filtros_grupo = ""
    parametros = []
    if grupo:
        filtros_grupo = """
            INNER JOIN perfiles_estudiante pe ON pe.id_usuario = u.id_usuario
            INNER JOIN institucion_grados ig
                ON ig.id_institucion_grado = pe.id_institucion_grado
               AND ig.id_institucion = pe.id_institucion
               AND ig.estado = 'activo'
            INNER JOIN secciones s
                ON s.id_seccion = pe.id_seccion
               AND s.id_institucion_grado = pe.id_institucion_grado
               AND s.estado = 'activo'
        """
        filtros_grupo += """
            AND pe.modalidad = 'grupo_educativo'
            AND pe.id_institucion = %s
            AND pe.id_institucion_grado = %s
            AND pe.id_seccion = %s
        """
        parametros.extend([grupo["id_institucion"], grupo["id_institucion_grado"], grupo["id_seccion"]])

    cursor.execute(
        f"""
        SELECT CONCAT_WS(' ', u.nombres, u.apellidos) AS nombre,
               COALESCE(pref.personaje_key, 'masculino') AS personaje_key,
               t.nombre_tema AS tema,
               pte.puntos_acumulados AS puntos
        FROM progreso_tema_estudiante pte
        INNER JOIN usuarios u
            ON u.id_usuario = pte.id_usuario
           AND u.estado = 'activo'
        INNER JOIN roles r
            ON r.id_rol = u.id_rol
           AND r.nombre = 'estudiante'
           AND r.estado = 'activo'
        INNER JOIN temas t
            ON t.id_tema = pte.id_tema
           AND t.estado = 'activo'
        LEFT JOIN preferencias_estudiante pref ON pref.id_usuario = u.id_usuario
        {filtros_grupo}
        WHERE pte.id_tema = %s
          AND pte.puntos_acumulados > 0
        ORDER BY pte.puntos_acumulados DESC, nombre ASC, u.id_usuario ASC
        LIMIT %s OFFSET %s
        """,
        tuple([*parametros, id_tema, limite, offset]),
    )
    filas = cursor.fetchall()
    return [
        {
            "nombre": fila["nombre"],
            "personaje_key": fila["personaje_key"],
            "tema": fila["tema"],
            "puntos": int(fila["puntos"] or 0),
        }
        for fila in filas
    ]


def _total_clasificacion(id_tema, grupo, cursor):
    """Cuenta la misma población filtrada que muestra la tabla paginada."""
    filtros_grupo = ""
    parametros = []
    if grupo:
        filtros_grupo = """
            INNER JOIN perfiles_estudiante pe ON pe.id_usuario = u.id_usuario
            INNER JOIN institucion_grados ig
                ON ig.id_institucion_grado = pe.id_institucion_grado
               AND ig.id_institucion = pe.id_institucion
               AND ig.estado = 'activo'
            INNER JOIN secciones s
                ON s.id_seccion = pe.id_seccion
               AND s.id_institucion_grado = pe.id_institucion_grado
               AND s.estado = 'activo'
        """
        filtros_grupo += """
            AND pe.modalidad = 'grupo_educativo'
            AND pe.id_institucion = %s
            AND pe.id_institucion_grado = %s
            AND pe.id_seccion = %s
        """
        parametros.extend([grupo["id_institucion"], grupo["id_institucion_grado"], grupo["id_seccion"]])
    cursor.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM progreso_tema_estudiante pte
        INNER JOIN usuarios u
            ON u.id_usuario = pte.id_usuario
           AND u.estado = 'activo'
        INNER JOIN roles r
            ON r.id_rol = u.id_rol
           AND r.nombre = 'estudiante'
           AND r.estado = 'activo'
        INNER JOIN temas t
            ON t.id_tema = pte.id_tema
           AND t.estado = 'activo'
        {filtros_grupo}
        WHERE pte.id_tema = %s
          AND pte.puntos_acumulados > 0
        """,
        tuple([*parametros, id_tema]),
    )
    return int((cursor.fetchone() or {}).get("total") or 0)


def obtener_clasificacion_estudiante(usuario, id_tema, scope="general", page=1, limit=LIMITE_POR_DEFECTO):
    """Devuelve la tabla general o el grupo real del estudiante autenticado."""
    try:
        id_tema = int(id_tema)
    except (TypeError, ValueError):
        return "datos_invalidos", "Seleccione un tema válido.", None, {"tema_id": "Tema requerido."}
    scope = (scope or "general").strip().lower()
    if scope not in {"general", "grupo"}:
        return "datos_invalidos", "El alcance de clasificación no es válido.", None, {"scope": "Use general o grupo."}

    pagina = _entero_acotado(page, 1, 1, 1000000)
    limite = _entero_acotado(limit, LIMITE_POR_DEFECTO, 1, LIMITE_MAXIMO)
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        tema = _tema_activo(id_tema, cursor)
        if not tema:
            return "datos_invalidos", "El tema seleccionado no está disponible.", None, {"tema_id": "Tema inactivo o inexistente."}
        grupo = _grupo_canonico_estudiante(usuario["id_usuario"], cursor)
        if scope == "grupo" and not grupo:
            return "no_autorizado", "No pertenece a un grupo institucional activo.", None, {"scope": "Grupo no disponible."}

        grupo_aplicable = grupo if scope == "grupo" else None
        total = _total_clasificacion(id_tema, grupo_aplicable, cursor)
        datos = _consulta_clasificacion(id_tema, grupo_aplicable, limite, (pagina - 1) * limite, cursor)
        return "consultado", "Clasificación consultada correctamente.", {
            "tema": tema,
            "scope": scope,
            "puede_ver_grupo": bool(grupo),
            "mi_puntuacion": _puntuacion_usuario(usuario["id_usuario"], id_tema, cursor),
            "participantes": datos,
            "paginacion": {"page": pagina, "limit": limite, "total": total},
        }, {}
    finally:
        cursor.close()
        conexion.close()
