from datetime import datetime

from db import obtener_conexion


TIPOS_ASIGNACION = ("generacion_automatica", "ejercicios_especificos")
ESTADOS_ASIGNACION = ("borrador", "activa", "pausada", "finalizada", "cancelada")
ESTADOS_ESTUDIANTE_ASIGNACION = ("pendiente", "en_progreso", "completada")


def _serializar_fecha(valor):
    # Convierte fechas MySQL a texto estable para JSON.
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _parse_fecha(valor, campo, errores, requerida=False):
    # Acepta fechas de input datetime-local o ISO simple desde React.
    if not valor:
        if requerida:
            errores[campo] = "Ingrese una fecha valida."
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "").replace("T", " "))
    except ValueError:
        errores[campo] = "Ingrese una fecha valida."
        return None


def _normalizar_ids(valores):
    # Convierte listas de IDs desde JSON o texto separado por comas.
    if isinstance(valores, str):
        valores = [valor.strip() for valor in valores.split(",") if valor.strip()]
    return sorted({int(valor) for valor in (valores or [])})


def _normalizar_entero(valor, campo, errores, requerido=False):
    # Convierte IDs obligatorios u opcionales de forma uniforme.
    if valor in (None, ""):
        if requerido:
            errores[campo] = "Seleccione una opcion valida."
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        errores[campo] = "Seleccione una opcion valida."
        return None


def _serializar_tema(fila):
    # Normaliza tema asociado a asignacion.
    return {
        "id_tema": fila["id_tema"],
        "nombre_tema": fila.get("nombre_tema"),
        "nombre_grado": fila.get("nombre_grado"),
    }


def _serializar_ejercicio(fila):
    # Normaliza ejercicio especifico sin exponer respuesta correcta al estudiante.
    return {
        "id_ejercicio": fila["id_ejercicio"],
        "id_tema": fila.get("id_tema"),
        "enunciado": fila.get("enunciado"),
        "tipo_respuesta": fila.get("tipo_respuesta"),
        "nombre_tema": fila.get("nombre_tema"),
        "nombre_nivel": fila.get("nombre_nivel"),
    }


def _serializar_asignacion(fila, temas=None, ejercicios=None):
    # Convierte una asignacion completa al formato usado por frontend.
    if not fila:
        return None
    return {
        "id_asignacion": fila["id_asignacion"],
        "id_docente": fila["id_docente"],
        "id_institucion_grado": fila.get("id_institucion_grado"),
        "id_seccion": fila.get("id_seccion"),
        "id_grado": fila.get("id_grado"),
        "id_grado_base": fila.get("id_grado"),
        "id_institucion": fila.get("id_institucion"),
        "nombre": fila["nombre"],
        "instrucciones": fila.get("instrucciones") or "",
        "tipo": fila["tipo"],
        "id_nivel_inicial": fila["id_nivel_inicial"],
        "nivel_inicial": fila.get("nivel_inicial"),
        "cantidad_preguntas": fila["cantidad_preguntas"],
        "fecha_inicio": _serializar_fecha(fila.get("fecha_inicio")),
        "fecha_limite": _serializar_fecha(fila.get("fecha_limite")),
        "obligatoria": bool(fila.get("obligatoria")),
        "estado": fila["estado"],
        "institucion": fila.get("institucion"),
        "seccion": fila.get("seccion"),
        "grado": fila.get("grado"),
        "docente": fila.get("docente"),
        "total_partidas": int(fila.get("total_partidas") or 0),
        "total_estudiantes": int(fila.get("total_estudiantes") or 0),
        "estado_estudiante": fila.get("estado_estudiante") or "pendiente",
        "fecha_completada_estudiante": _serializar_fecha(fila.get("fecha_completada")),
        "cantidad_intentos_estudiante": int(fila.get("cantidad_intentos") or 0),
        "ultima_partida_estudiante": fila.get("ultima_partida"),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
        "temas": temas or [],
        "ejercicios": ejercicios or [],
    }


def asegurar_estudiante_asignacion(id_asignacion, id_estudiante, cursor):
    # Crea la fila pendiente por estudiante sin cambiar completados existentes.
    cursor.execute(
        """
        INSERT INTO estudiante_asignaciones
            (id_asignacion, id_estudiante, estado, fecha_asignacion)
        VALUES (%s, %s, 'pendiente', CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE id_estudiante_asignacion = id_estudiante_asignacion
        """,
        (id_asignacion, id_estudiante),
    )


def registrar_inicio_asignacion_estudiante(id_asignacion, id_estudiante, id_partida, cursor):
    # Marca el intento de actividad como en progreso e incrementa cantidad_intentos.
    if not id_asignacion:
        return
    asegurar_estudiante_asignacion(id_asignacion, id_estudiante, cursor)
    cursor.execute(
        """
        UPDATE estudiante_asignaciones
        SET estado = CASE WHEN estado = 'completada' THEN estado ELSE 'en_progreso' END,
            fecha_inicio = COALESCE(fecha_inicio, CURRENT_TIMESTAMP),
            cantidad_intentos = cantidad_intentos + CASE WHEN estado = 'completada' THEN 0 ELSE 1 END,
            ultima_partida = %s,
            fecha_ultima_actividad = CURRENT_TIMESTAMP
        WHERE id_asignacion = %s
          AND id_estudiante = %s
        """,
        (id_partida, id_asignacion, id_estudiante),
    )


def registrar_cierre_partida_asignada(id_asignacion, id_estudiante, id_partida, estado_partida, total_correctos, casilla_actual, cursor):
    # Completa solo si la partida termino el recorrido; perder o salir conserva en progreso.
    if not id_asignacion:
        return
    asegurar_estudiante_asignacion(id_asignacion, id_estudiante, cursor)
    if estado_partida == "completada" and total_correctos >= 10 and casilla_actual >= 10:
        cursor.execute(
            """
            UPDATE estudiante_asignaciones
            SET estado = 'completada',
                fecha_completada = CURRENT_TIMESTAMP,
                ultima_partida = %s,
                fecha_ultima_actividad = CURRENT_TIMESTAMP
            WHERE id_asignacion = %s
              AND id_estudiante = %s
            """,
            (id_partida, id_asignacion, id_estudiante),
        )
        return

    cursor.execute(
        """
        UPDATE estudiante_asignaciones
        SET estado = CASE WHEN estado = 'completada' THEN estado ELSE 'en_progreso' END,
            ultima_partida = %s,
            fecha_ultima_actividad = CURRENT_TIMESTAMP
        WHERE id_asignacion = %s
          AND id_estudiante = %s
        """,
        (id_partida, id_asignacion, id_estudiante),
    )


def _asignacion_por_id(id_asignacion, cursor):
    # Consulta asignacion con datos de institucion, grado, seccion, nivel y docente.
    cursor.execute(
        """
        SELECT a.*, ig.id_grado_base AS id_grado, ig.id_institucion,
               i.nombre AS institucion, g.nombre_grado AS grado,
               s.nombre_seccion AS seccion, n.nombre AS nivel_inicial,
               CONCAT(u.nombres, ' ', u.apellidos) AS docente,
               (
                   SELECT COUNT(*)
                   FROM partidas_juego p
                   WHERE p.id_asignacion = a.id_asignacion
               ) AS total_partidas,
               (
                   SELECT COUNT(DISTINCT pe.id_usuario)
                   FROM perfiles_estudiante pe
                   WHERE pe.modalidad = 'grupo_educativo'
                     AND pe.id_institucion_grado = a.id_institucion_grado
                     AND pe.id_seccion = a.id_seccion
               ) AS total_estudiantes
        FROM asignaciones a
        INNER JOIN institucion_grados ig ON ig.id_institucion_grado = a.id_institucion_grado
        INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
        INNER JOIN grados g ON g.id_grado = ig.id_grado_base
        INNER JOIN niveles_dificultad n ON n.id_nivel = a.id_nivel_inicial
        INNER JOIN usuarios u ON u.id_usuario = a.id_docente
        INNER JOIN secciones s ON s.id_seccion = a.id_seccion
        WHERE a.id_asignacion = %s
        """,
        (id_asignacion,),
    )
    return cursor.fetchone()


def _temas_asignacion(id_asignacion, cursor):
    # Lista temas activos vinculados a una asignacion.
    cursor.execute(
        """
        SELECT t.id_tema, t.nombre_tema, g.nombre_grado
        FROM asignacion_temas at
        INNER JOIN temas t ON t.id_tema = at.id_tema
        INNER JOIN grados g ON g.id_grado = t.id_grado
        WHERE at.id_asignacion = %s
          AND at.estado = 'activo'
        ORDER BY t.nombre_tema ASC
        """,
        (id_asignacion,),
    )
    return [_serializar_tema(fila) for fila in cursor.fetchall()]


def _ejercicios_asignacion(id_asignacion, cursor, incluir_respuestas=False):
    # Lista ejercicios especificos activos asociados a una asignacion.
    cursor.execute(
        """
        SELECT e.id_ejercicio, e.id_tema, e.enunciado, e.tipo_respuesta,
               e.respuesta_correcta, t.nombre_tema, n.nombre AS nombre_nivel
        FROM asignacion_ejercicios ae
        INNER JOIN ejercicios e ON e.id_ejercicio = ae.id_ejercicio
        INNER JOIN temas t ON t.id_tema = e.id_tema
        INNER JOIN niveles_dificultad n ON n.id_nivel = e.id_nivel
        WHERE ae.id_asignacion = %s
          AND ae.estado = 'activo'
        ORDER BY e.id_ejercicio ASC
        """,
        (id_asignacion,),
    )
    ejercicios = []
    for fila in cursor.fetchall():
        ejercicio = _serializar_ejercicio(fila)
        if incluir_respuestas:
            ejercicio["respuesta_correcta"] = fila.get("respuesta_correcta")
        ejercicios.append(ejercicio)
    return ejercicios


def _puede_administrar(usuario, asignacion):
    # Permite administrar al docente propietario o administrador.
    return usuario["rol"] == "administrador" or (
        usuario["rol"] == "docente" and asignacion and asignacion["id_docente"] == usuario["id_usuario"]
    )


def _contexto_docente(id_docente, id_institucion_grado, id_seccion, cursor):
    # Valida que docente, grado institucional y seccion pertenezcan al mismo contexto.
    cursor.execute(
        """
        SELECT ig.id_institucion_grado, ig.id_institucion, ig.id_grado_base,
               g.nombre_grado, s.id_seccion, s.nombre_seccion
        FROM docente_grados dg
        INNER JOIN institucion_grados ig ON ig.id_institucion_grado = dg.id_institucion_grado
        INNER JOIN grados g ON g.id_grado = ig.id_grado_base
        INNER JOIN secciones s ON s.id_institucion_grado = ig.id_institucion_grado
        INNER JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion
        INNER JOIN perfiles_docente pd ON pd.id_usuario = dg.id_usuario_docente
        WHERE dg.id_usuario_docente = %s
          AND dg.id_institucion_grado = %s
          AND s.id_seccion = %s
          AND pd.id_institucion = ig.id_institucion
          AND dg.estado = 'activo'
          AND ds.id_docente = dg.id_usuario_docente
          AND ds.estado = 'activo'
          AND s.estado = 'activo'
          AND ig.estado = 'activo'
        LIMIT 1
        """,
        (id_docente, id_institucion_grado, id_seccion),
    )
    return cursor.fetchone()


def _validar_nivel(id_nivel, cursor):
    # Confirma que el nivel de dificultad este disponible.
    cursor.execute(
        "SELECT id_nivel FROM niveles_dificultad WHERE id_nivel = %s AND estado = 'activo'",
        (id_nivel,),
    )
    return cursor.fetchone() is not None


def _validar_temas(ids_tema, id_grado_base, cursor):
    # Comprueba que los temas seleccionados pertenezcan al grado base heredado.
    if not ids_tema:
        return False
    formato = ",".join(["%s"] * len(ids_tema))
    cursor.execute(
        f"""
        SELECT id_tema
        FROM temas
        WHERE estado = 'activo'
          AND id_grado = %s
          AND id_tema IN ({formato})
        """,
        tuple([id_grado_base, *ids_tema]),
    )
    encontrados = {fila["id_tema"] for fila in cursor.fetchall()}
    return encontrados == set(ids_tema)


def _validar_ejercicios(ids_ejercicio, ids_tema, cursor):
    # Valida que ejercicios especificos publicados pertenezcan a los temas elegidos.
    if not ids_ejercicio:
        return False
    formato = ",".join(["%s"] * len(ids_ejercicio))
    cursor.execute(
        f"""
        SELECT id_ejercicio, id_tema
        FROM ejercicios
        WHERE estado = 'publicado'
          AND id_ejercicio IN ({formato})
        """,
        tuple(ids_ejercicio),
    )
    encontrados = cursor.fetchall()
    return (
        {fila["id_ejercicio"] for fila in encontrados} == set(ids_ejercicio)
        and {fila["id_tema"] for fila in encontrados}.issubset(set(ids_tema))
    )


def _validar_payload(datos, contexto, cursor):
    # Valida campos base de asignacion y relaciones academicas institucionales.
    errores = {}
    nombre = (datos.get("nombre") or "").strip()
    instrucciones = (datos.get("instrucciones") or "").strip()
    tipo = (datos.get("tipo") or "generacion_automatica").strip()
    estado = (datos.get("estado") or "activa").strip()
    fecha_inicio = _parse_fecha(datos.get("fecha_inicio"), "fecha_inicio", errores, requerida=True)
    fecha_limite = _parse_fecha(datos.get("fecha_limite"), "fecha_limite", errores)

    id_nivel_inicial = _normalizar_entero(datos.get("id_nivel_inicial"), "id_nivel_inicial", errores, requerido=True)
    try:
        cantidad_preguntas = int(datos.get("cantidad_preguntas", 10))
    except (TypeError, ValueError):
        cantidad_preguntas = 0
        errores["cantidad_preguntas"] = "Ingrese una cantidad valida."

    try:
        ids_tema = _normalizar_ids(datos.get("temas"))
    except (TypeError, ValueError):
        ids_tema = []
        errores["temas"] = "Seleccione temas validos."

    try:
        ids_ejercicio = _normalizar_ids(datos.get("ejercicios"))
    except (TypeError, ValueError):
        ids_ejercicio = []
        errores["ejercicios"] = "Ingrese IDs de ejercicios validos."

    if "id_grupo" in datos and datos.get("id_grupo") not in (None, ""):
        errores["id_grupo"] = "id_grupo es legacy; use id_institucion_grado e id_seccion."
    if len(nombre) < 3:
        errores["nombre"] = "Ingrese un nombre de al menos 3 caracteres."
    if len(instrucciones) > 500:
        errores["instrucciones"] = "Las instrucciones no deben superar 500 caracteres."
    if tipo not in TIPOS_ASIGNACION:
        errores["tipo"] = "Tipo de asignacion invalido."
    if estado not in ESTADOS_ASIGNACION:
        errores["estado"] = "Estado invalido."
    if cantidad_preguntas < 1 or cantidad_preguntas > 100:
        errores["cantidad_preguntas"] = "La cantidad debe estar entre 1 y 100."
    if fecha_inicio and fecha_limite and fecha_inicio > fecha_limite:
        errores["fecha_limite"] = "La fecha limite debe ser posterior al inicio."
    if id_nivel_inicial and not _validar_nivel(id_nivel_inicial, cursor):
        errores["id_nivel_inicial"] = "Nivel inactivo o inexistente."
    if "temas" not in errores and not _validar_temas(ids_tema, contexto["id_grado_base"], cursor):
        errores["temas"] = "Los temas deben estar activos y pertenecer al grado seleccionado."
    if tipo == "ejercicios_especificos" and "ejercicios" not in errores:
        if not _validar_ejercicios(ids_ejercicio, ids_tema, cursor):
            errores["ejercicios"] = "Los ejercicios deben estar publicados y pertenecer a los temas seleccionados."

    return {
        "nombre": nombre,
        "instrucciones": instrucciones,
        "tipo": tipo,
        "id_nivel_inicial": id_nivel_inicial,
        "cantidad_preguntas": cantidad_preguntas,
        "fecha_inicio": fecha_inicio,
        "fecha_limite": fecha_limite,
        "obligatoria": 1 if datos.get("obligatoria", True) else 0,
        "estado": estado,
        "temas": ids_tema,
        "ejercicios": ids_ejercicio,
    }, errores


def _sincronizar_relacion_asignacion(tabla, columna_id, id_asignacion, ids_nuevos, cursor):
    # Activa relaciones vigentes e inactiva las retiradas sin borrar historico.
    cursor.execute(
        f"UPDATE {tabla} SET estado = 'inactivo', fecha_fin = CURRENT_TIMESTAMP WHERE id_asignacion = %s",
        (id_asignacion,),
    )
    for id_relacion in ids_nuevos:
        cursor.execute(
            f"""
            INSERT INTO {tabla} (id_asignacion, {columna_id}, estado, fecha_fin)
            VALUES (%s, %s, 'activo', NULL)
            ON DUPLICATE KEY UPDATE estado = 'activo', fecha_fin = NULL
            """,
            (id_asignacion, id_relacion),
        )


def _guardar_relaciones(id_asignacion, datos, cursor):
    # Guarda temas y ejercicios por estado para preservar relaciones historicas.
    _sincronizar_relacion_asignacion("asignacion_temas", "id_tema", id_asignacion, datos["temas"], cursor)
    ejercicios = datos["ejercicios"] if datos["tipo"] == "ejercicios_especificos" else []
    _sincronizar_relacion_asignacion("asignacion_ejercicios", "id_ejercicio", id_asignacion, ejercicios, cursor)


def _asignacion_completa(id_asignacion, cursor, incluir_respuestas=False):
    # Ensambla asignacion con temas y ejercicios activos.
    asignacion = _asignacion_por_id(id_asignacion, cursor)
    return _serializar_asignacion(
        asignacion,
        _temas_asignacion(id_asignacion, cursor),
        _ejercicios_asignacion(id_asignacion, cursor, incluir_respuestas=incluir_respuestas),
    )


def listar_contexto_asignaciones(usuario):
    # Lista grados institucionales y secciones disponibles para asignaciones.
    if usuario["rol"] not in ("docente", "administrador"):
        return "no_autorizado", "Permisos insuficientes para consultar este contexto.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if usuario["rol"] == "administrador":
            cursor.execute(
                """
                SELECT ig.id_institucion_grado, ig.id_grado_base, g.nombre_grado,
                       i.id_institucion, i.nombre AS institucion
                FROM institucion_grados ig
                INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
                INNER JOIN grados g ON g.id_grado = ig.id_grado_base
                WHERE ig.estado = 'activo'
                  AND i.estado = 'activo'
                ORDER BY i.nombre ASC, g.orden_visualizacion ASC
                """
            )
        else:
            cursor.execute(
                """
                SELECT dg.id_institucion_grado, ig.id_grado_base, g.nombre_grado,
                       i.id_institucion, i.nombre AS institucion
                FROM docente_grados dg
                INNER JOIN institucion_grados ig ON ig.id_institucion_grado = dg.id_institucion_grado
                INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
                INNER JOIN grados g ON g.id_grado = ig.id_grado_base
                INNER JOIN perfiles_docente pd ON pd.id_usuario = dg.id_usuario_docente
                WHERE dg.id_usuario_docente = %s
                  AND dg.estado = 'activo'
                  AND ig.estado = 'activo'
                  AND i.estado = 'activo'
                  AND pd.id_institucion = ig.id_institucion
                ORDER BY g.orden_visualizacion ASC
                """,
                (usuario["id_usuario"],),
            )
        grados = []
        for fila in cursor.fetchall():
            if usuario["rol"] == "administrador":
                cursor.execute(
                    """
                    SELECT s.id_seccion, s.nombre_seccion
                    FROM secciones s
                    WHERE s.estado = 'activo'
                      AND s.id_institucion_grado = %s
                    ORDER BY FIELD(s.nombre_seccion, 'A', 'B', 'C', 'D', 'Única'), s.nombre_seccion
                    """,
                    (fila["id_institucion_grado"],),
                )
            else:
                cursor.execute(
                    """
                    SELECT s.id_seccion, s.nombre_seccion
                    FROM docente_secciones ds
                    INNER JOIN secciones s ON s.id_seccion = ds.id_seccion
                    WHERE ds.id_docente = %s
                      AND ds.estado = 'activo'
                      AND s.estado = 'activo'
                      AND s.id_institucion_grado = %s
                    ORDER BY FIELD(s.nombre_seccion, 'A', 'B', 'C', 'D', 'Única'), s.nombre_seccion
                    """,
                    (usuario["id_usuario"], fila["id_institucion_grado"]),
                )
            grados.append({
                "id_institucion_grado": fila["id_institucion_grado"],
                "id_grado_base": fila["id_grado_base"],
                "nombre_grado": fila["nombre_grado"],
                "id_institucion": fila["id_institucion"],
                "institucion": fila["institucion"],
                "secciones": cursor.fetchall(),
            })
        return "consultado", "Contexto de asignaciones consultado correctamente.", grados, {}
    finally:
        cursor.close()
        conexion.close()


def listar_asignaciones(usuario):
    # Lista asignaciones propias para docente o todas para administrador.
    if usuario["rol"] not in ("docente", "administrador"):
        return "no_autorizado", "Permisos insuficientes.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        filtro = ""
        parametros = []
        if usuario["rol"] == "docente":
            filtro = "WHERE a.id_docente = %s"
            parametros.append(usuario["id_usuario"])
        cursor.execute(
            f"""
            SELECT a.id_asignacion
            FROM asignaciones a
            INNER JOIN institucion_grados ig ON ig.id_institucion_grado = a.id_institucion_grado
            {filtro}
            ORDER BY a.fecha_creacion DESC
            """,
            tuple(parametros),
        )
        asignaciones = [_asignacion_completa(fila["id_asignacion"], cursor, incluir_respuestas=True) for fila in cursor.fetchall()]
        return "consultado", "Asignaciones consultadas correctamente.", asignaciones, {}
    finally:
        cursor.close()
        conexion.close()


def crear_asignacion(usuario, datos):
    # Crea una asignacion institucional por grado institucional y seccion.
    if usuario["rol"] != "docente":
        return "no_autorizado", "Solo docentes pueden crear asignaciones.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        errores = {}
        id_institucion_grado = _normalizar_entero(datos.get("id_institucion_grado"), "id_institucion_grado", errores, requerido=True)
        id_seccion = _normalizar_entero(datos.get("id_seccion"), "id_seccion", errores, requerido=True)
        if "id_grupo" in datos and datos.get("id_grupo") not in (None, ""):
            errores["id_grupo"] = "id_grupo es legacy; use id_institucion_grado e id_seccion."
        contexto = None if errores else _contexto_docente(usuario["id_usuario"], id_institucion_grado, id_seccion, cursor)
        if not errores and not contexto:
            errores["id_seccion"] = "La seccion no pertenece a un grado impartido por el docente."
        if errores:
            return "datos_invalidos", "Revise los datos de la asignación.", None, errores

        datos_limpios, errores = _validar_payload(datos, contexto, cursor)
        if errores:
            return "datos_invalidos", "Revise los datos de la asignación.", None, errores

        cursor.execute(
            """
            INSERT INTO asignaciones
                (id_docente, id_institucion_grado, id_seccion, id_grupo, nombre, instrucciones, tipo,
                 id_nivel_inicial, cantidad_preguntas, fecha_inicio, fecha_limite, obligatoria, estado)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usuario["id_usuario"],
                id_institucion_grado,
                id_seccion,
                datos_limpios["nombre"],
                datos_limpios["instrucciones"],
                datos_limpios["tipo"],
                datos_limpios["id_nivel_inicial"],
                datos_limpios["cantidad_preguntas"],
                datos_limpios["fecha_inicio"],
                datos_limpios["fecha_limite"],
                datos_limpios["obligatoria"],
                datos_limpios["estado"],
            ),
        )
        id_asignacion = cursor.lastrowid
        _guardar_relaciones(id_asignacion, datos_limpios, cursor)
        conexion.commit()
        return "creado", "Asignación creada correctamente.", _asignacion_completa(id_asignacion, cursor, incluir_respuestas=True), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_asignacion(usuario, id_asignacion, datos):
    # Actualiza una asignacion preservando relaciones historicas.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        asignacion = _asignacion_por_id(id_asignacion, cursor)
        if not asignacion:
            return "no_existe", "La asignación solicitada no existe.", None, {}
        if not _puede_administrar(usuario, asignacion):
            return "no_autorizado", "No puede modificar esta asignación.", None, {}

        errores = {}
        if "id_grupo" in datos and datos.get("id_grupo") not in (None, ""):
            errores["id_grupo"] = "id_grupo es legacy; use id_institucion_grado e id_seccion."
        id_institucion_grado = _normalizar_entero(
            datos.get("id_institucion_grado", asignacion["id_institucion_grado"]),
            "id_institucion_grado",
            errores,
            requerido=True,
        )
        id_seccion = _normalizar_entero(
            datos.get("id_seccion", asignacion["id_seccion"]),
            "id_seccion",
            errores,
            requerido=True,
        )
        id_docente_contexto = asignacion["id_docente"] if usuario["rol"] == "administrador" else usuario["id_usuario"]
        contexto = None if errores else _contexto_docente(id_docente_contexto, id_institucion_grado, id_seccion, cursor)
        if not errores and not contexto:
            errores["id_seccion"] = "La seccion no pertenece a un grado impartido por el docente."
        if errores:
            return "datos_invalidos", "Revise los datos de la asignación.", None, errores

        datos_limpios, errores = _validar_payload(datos, contexto, cursor)
        if errores:
            return "datos_invalidos", "Revise los datos de la asignación.", None, errores

        cursor.execute(
            """
            UPDATE asignaciones
            SET id_institucion_grado = %s,
                id_seccion = %s,
                id_grupo = NULL,
                nombre = %s,
                instrucciones = %s,
                tipo = %s,
                id_nivel_inicial = %s,
                cantidad_preguntas = %s,
                fecha_inicio = %s,
                fecha_limite = %s,
                obligatoria = %s,
                estado = %s
            WHERE id_asignacion = %s
            """,
            (
                id_institucion_grado,
                id_seccion,
                datos_limpios["nombre"],
                datos_limpios["instrucciones"],
                datos_limpios["tipo"],
                datos_limpios["id_nivel_inicial"],
                datos_limpios["cantidad_preguntas"],
                datos_limpios["fecha_inicio"],
                datos_limpios["fecha_limite"],
                datos_limpios["obligatoria"],
                datos_limpios["estado"],
                id_asignacion,
            ),
        )
        _guardar_relaciones(id_asignacion, datos_limpios, cursor)
        conexion.commit()
        return "actualizado", "Asignación actualizada correctamente.", _asignacion_completa(id_asignacion, cursor, incluir_respuestas=True), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_asignacion(usuario, id_asignacion, estado):
    # Cambia estado de una asignacion sin modificar relaciones historicas.
    if estado not in ESTADOS_ASIGNACION:
        return "datos_invalidos", "Estado inválido.", None, {"estado": "Valor no permitido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        asignacion = _asignacion_por_id(id_asignacion, cursor)
        if not asignacion:
            return "no_existe", "La asignación solicitada no existe.", None, {}
        if not _puede_administrar(usuario, asignacion):
            return "no_autorizado", "No puede modificar esta asignación.", None, {}
        cursor.execute("UPDATE asignaciones SET estado = %s WHERE id_asignacion = %s", (estado, id_asignacion))
        conexion.commit()
        return "actualizado", "Estado de asignación actualizado.", _asignacion_completa(id_asignacion, cursor, incluir_respuestas=True), {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def listar_asignaciones_estudiante(usuario):
    # Lista actividades institucionales visibles desde el perfil academico del estudiante.
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden consultar actividades.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT modalidad
            FROM perfiles_estudiante
            WHERE id_usuario = %s
            LIMIT 1
            """,
            (usuario["id_usuario"],),
        )
        perfil = cursor.fetchone()
        if not perfil or perfil["modalidad"] != "grupo_educativo":
            return "no_autorizado", "Las actividades solo están disponibles para estudiantes de grupo educativo.", None, {}
        cursor.execute(
            """
            SELECT DISTINCT a.id_asignacion
            FROM perfiles_estudiante pe
            INNER JOIN asignaciones a
                ON a.id_institucion_grado = pe.id_institucion_grado
               AND a.id_seccion = pe.id_seccion
            LEFT JOIN estudiante_asignaciones ea
                ON ea.id_asignacion = a.id_asignacion
               AND ea.id_estudiante = pe.id_usuario
            WHERE pe.id_usuario = %s
              AND pe.modalidad = 'grupo_educativo'
              AND a.estado = 'activa'
              AND a.fecha_inicio <= CURRENT_TIMESTAMP
              AND (a.fecha_limite IS NULL OR a.fecha_limite >= CURRENT_TIMESTAMP)
              AND COALESCE(ea.estado, 'pendiente') <> 'completada'
            ORDER BY a.fecha_inicio DESC, a.id_asignacion DESC
            """,
            (usuario["id_usuario"],),
        )
        asignaciones = []
        for fila in cursor.fetchall():
            asegurar_estudiante_asignacion(fila["id_asignacion"], usuario["id_usuario"], cursor)
            asignacion = _asignacion_completa(fila["id_asignacion"], cursor, incluir_respuestas=False)
            cursor.execute(
                """
                SELECT estado AS estado_estudiante, fecha_completada,
                       cantidad_intentos, ultima_partida
                FROM estudiante_asignaciones
                WHERE id_asignacion = %s
                  AND id_estudiante = %s
                """,
                (fila["id_asignacion"], usuario["id_usuario"]),
            )
            progreso = cursor.fetchone() or {}
            cursor.execute(
                """
                SELECT COUNT(*) AS total,
                       MAX(estado) AS ultimo_estado
                FROM partidas_juego
                WHERE id_usuario = %s
                  AND id_asignacion = %s
                """,
                (usuario["id_usuario"], fila["id_asignacion"]),
            )
            avance = cursor.fetchone() or {}
            asignacion["partidas_realizadas"] = int(avance.get("total") or 0)
            asignacion["ultimo_estado_partida"] = avance.get("ultimo_estado")
            asignacion["estado_estudiante"] = progreso.get("estado_estudiante") or "pendiente"
            asignacion["fecha_completada_estudiante"] = _serializar_fecha(progreso.get("fecha_completada"))
            asignacion["cantidad_intentos_estudiante"] = int(progreso.get("cantidad_intentos") or 0)
            asignacion["ultima_partida_estudiante"] = progreso.get("ultima_partida")
            asignaciones.append(asignacion)
        conexion.commit()
        return "consultado", "Actividades consultadas correctamente.", asignaciones, {}
    finally:
        cursor.close()
        conexion.close()


def validar_asignacion_estudiante(id_usuario, id_asignacion, id_tema, cursor):
    # Valida que una partida pueda iniciarse desde una asignacion institucional visible.
    if not id_asignacion:
        return True, None, None, {}
    cursor.execute(
        """
        SELECT a.*, ig.id_grado_base AS id_grado,
               COALESCE(ea.estado, 'pendiente') AS estado_estudiante
        FROM asignaciones a
        INNER JOIN institucion_grados ig ON ig.id_institucion_grado = a.id_institucion_grado
        INNER JOIN perfiles_estudiante pe
            ON pe.id_institucion_grado = a.id_institucion_grado
           AND pe.id_seccion = a.id_seccion
        LEFT JOIN estudiante_asignaciones ea
            ON ea.id_asignacion = a.id_asignacion
           AND ea.id_estudiante = pe.id_usuario
        WHERE a.id_asignacion = %s
          AND pe.id_usuario = %s
          AND pe.modalidad = 'grupo_educativo'
          AND a.estado = 'activa'
          AND a.fecha_inicio <= CURRENT_TIMESTAMP
          AND (a.fecha_limite IS NULL OR a.fecha_limite >= CURRENT_TIMESTAMP)
        LIMIT 1
        """,
        (id_asignacion, id_usuario),
    )
    asignacion = cursor.fetchone()
    if not asignacion:
        return False, "La asignación no está disponible para este estudiante.", None, {"id_asignacion": "Asignación no disponible."}
    if asignacion.get("estado_estudiante") == "completada":
        return False, "La actividad ya fue completada por este estudiante.", None, {"id_asignacion": "Actividad completada."}
    cursor.execute(
        """
        SELECT 1
        FROM asignacion_temas at
        INNER JOIN temas t ON t.id_tema = at.id_tema
        WHERE at.id_asignacion = %s
          AND at.id_tema = %s
          AND at.estado = 'activo'
          AND t.estado = 'activo'
          AND t.id_grado = %s
        """,
        (id_asignacion, id_tema, asignacion["id_grado"]),
    )
    if not cursor.fetchone():
        return False, "El tema no pertenece a la asignación seleccionada.", None, {"id_tema": "Tema fuera de asignación."}
    return True, "", asignacion, {}
