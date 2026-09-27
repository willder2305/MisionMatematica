from datetime import datetime

from db import obtener_conexion
from services.progreso_service import sincronizar_progreso_usuario


def _serializar_fecha(valor):
    # Convierte fechas MySQL a texto JSON estable.
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _porcentaje(aciertos, intentos):
    # Calcula porcentaje de aciertos sin dividir entre cero.
    return round((aciertos / intentos) * 100, 2) if intentos else 0


def _parse_fecha(valor, campo, errores):
    # Normaliza filtros de fecha recibidos desde inputs datetime-local.
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "").replace("T", " "))
    except ValueError:
        errores[campo] = "Ingrese una fecha valida."
        return None


def _normalizar_entero(valor, campo, errores):
    # Convierte IDs opcionales de filtros; vacio equivale a sin filtro.
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        errores[campo] = "Filtro invalido."
        return None


def _validar_filtros(filtros):
    # Valida filtros compartidos por reportes y cronologia.
    errores = {}
    datos = {
        "id_institucion_grado": _normalizar_entero(filtros.get("id_institucion_grado"), "id_institucion_grado", errores),
        "id_seccion": _normalizar_entero(filtros.get("id_seccion"), "id_seccion", errores),
        "id_estudiante": _normalizar_entero(filtros.get("id_estudiante"), "id_estudiante", errores),
        "id_tema": _normalizar_entero(filtros.get("id_tema"), "id_tema", errores),
        "id_asignacion": _normalizar_entero(filtros.get("id_asignacion"), "id_asignacion", errores),
        "fecha_inicio": _parse_fecha(filtros.get("fecha_inicio"), "fecha_inicio", errores),
        "fecha_fin": _parse_fecha(filtros.get("fecha_fin"), "fecha_fin", errores),
    }
    if datos["fecha_inicio"] and datos["fecha_fin"] and datos["fecha_inicio"] > datos["fecha_fin"]:
        errores["fecha_fin"] = "La fecha final debe ser posterior a la inicial."
    return datos, errores


def _condiciones_partidas(usuario, filtros, alias="p"):
    # Construye filtros SQL parametrizados sin exponer datos de otros docentes.
    condiciones = [f"{alias}.id_usuario IS NOT NULL"]
    parametros = []

    if usuario["rol"] == "docente":
        # El docente evalúa únicamente actividades asignadas; el juego personal no es una nota.
        condiciones.append(f"{alias}.tipo_contexto = 'asignacion'")
        condiciones.append(
            f"""
            EXISTS (
                SELECT 1
                FROM perfiles_estudiante pe_perm
                INNER JOIN docente_secciones ds_perm ON ds_perm.id_seccion = pe_perm.id_seccion
                WHERE pe_perm.id_usuario = {alias}.id_usuario
                  AND pe_perm.modalidad = 'grupo_educativo'
                  AND ds_perm.id_docente = %s
                  AND ds_perm.estado = 'activo'
            )
            """
        )
        parametros.append(usuario["id_usuario"])
    elif usuario["rol"] != "administrador":
        condiciones.append("1 = 0")

    if filtros.get("id_estudiante"):
        condiciones.append(f"{alias}.id_usuario = %s")
        parametros.append(filtros["id_estudiante"])
    if filtros.get("id_tema"):
        condiciones.append(f"{alias}.id_tema = %s")
        parametros.append(filtros["id_tema"])
    if filtros.get("id_asignacion"):
        condiciones.append(f"{alias}.id_asignacion = %s")
        parametros.append(filtros["id_asignacion"])
    if filtros.get("fecha_inicio"):
        condiciones.append(f"COALESCE({alias}.fecha_ultima_actividad, {alias}.fecha_fin, {alias}.fecha_inicio) >= %s")
        parametros.append(filtros["fecha_inicio"])
    if filtros.get("fecha_fin"):
        condiciones.append(f"COALESCE({alias}.fecha_ultima_actividad, {alias}.fecha_fin, {alias}.fecha_inicio) <= %s")
        parametros.append(filtros["fecha_fin"])
    if filtros.get("id_institucion_grado"):
        condiciones.append(
            f"""
            EXISTS (
                SELECT 1
                FROM perfiles_estudiante pe_grado
                WHERE pe_grado.id_usuario = {alias}.id_usuario
                  AND pe_grado.id_institucion_grado = %s
            )
            """
        )
        parametros.append(filtros["id_institucion_grado"])
    if filtros.get("id_seccion"):
        condiciones.append(
            f"""
            EXISTS (
                SELECT 1
                FROM perfiles_estudiante pe_seccion
                WHERE pe_seccion.id_usuario = {alias}.id_usuario
                  AND pe_seccion.id_seccion = %s
            )
            """
        )
        parametros.append(filtros["id_seccion"])

    return " AND ".join(condiciones), parametros


def _estudiantes_visibles(usuario, cursor):
    # Lista IDs de estudiantes visibles para sincronizar progreso antes de reportar.
    parametros = []
    filtro = ""
    if usuario["rol"] == "docente":
        filtro = "AND ds.id_docente = %s"
        parametros.append(usuario["id_usuario"])
    elif usuario["rol"] != "administrador":
        return []

    cursor.execute(
        f"""
        SELECT DISTINCT pe.id_usuario
        FROM perfiles_estudiante pe
        INNER JOIN docente_secciones ds ON ds.id_seccion = pe.id_seccion
        WHERE pe.modalidad = 'grupo_educativo'
          AND ds.estado = 'activo'
          {filtro}
        """,
        tuple(parametros),
    )
    return [fila["id_usuario"] for fila in cursor.fetchall()]


def _sincronizar_estudiantes_visibles(usuario, cursor):
    # Recalcula progreso para que el panel use datos consistentes.
    for id_usuario in _estudiantes_visibles(usuario, cursor):
        sincronizar_progreso_usuario(id_usuario, cursor)


def _errores_consecutivos(id_usuario, id_tema, cursor):
    # Cuenta errores consecutivos recientes por estudiante y tema.
    cursor.execute(
        """
        SELECT i.es_correcta
        FROM intentos_juego i
        INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
        WHERE p.id_usuario = %s
          AND p.id_tema = %s
          AND p.tipo_contexto = 'asignacion'
        ORDER BY i.fecha_respuesta DESC, i.id_intento DESC
        LIMIT 10
        """,
        (id_usuario, id_tema),
    )
    total = 0
    for fila in cursor.fetchall():
        if fila["es_correcta"]:
            break
        total += 1
    return total


def listar_estudiantes_docente(usuario):
    # Devuelve estudiantes visibles con metricas generales de progreso.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        _sincronizar_estudiantes_visibles(usuario, cursor)
        conexion.commit()

        filtro = ""
        parametros = []
        if usuario["rol"] == "docente":
            filtro = "AND ds.id_docente = %s"
            parametros.append(usuario["id_usuario"])
        elif usuario["rol"] != "administrador":
            return "no_autorizado", "Permisos insuficientes.", None, {}

        cursor.execute(
            f"""
            SELECT perfil.id_perfil_estudiante, perfil.id_usuario,
                   perfil.id_institucion_grado, perfil.id_seccion, perfil.modalidad, perfil.fecha_creacion AS fecha_ingreso,
                   u.nombres, u.apellidos, u.correo,
                   i.nombre AS institucion, g.nombre_grado AS grado, s.nombre_seccion AS seccion,
                   COALESCE(prog.total_partidas, 0) AS total_partidas,
                   COALESCE(prog.total_ejercicios, 0) AS total_ejercicios,
                   COALESCE(prog.total_aciertos, 0) AS total_aciertos,
                   COALESCE(prog.total_errores, 0) AS total_errores,
                   COALESCE(prog.porcentaje_aciertos, 0) AS porcentaje_aciertos,
                   prog.ultima_actividad,
                   (
                       SELECT COUNT(*)
                       FROM asignaciones a
                       WHERE a.id_institucion_grado = perfil.id_institucion_grado
                         AND a.id_seccion = perfil.id_seccion
                         AND a.estado = 'activa'
                         AND a.fecha_inicio <= CURRENT_TIMESTAMP
                         AND (a.fecha_limite IS NULL OR a.fecha_limite >= CURRENT_TIMESTAMP)
                         AND NOT EXISTS (
                             SELECT 1
                             FROM partidas_juego p
                             WHERE p.id_usuario = perfil.id_usuario
                               AND p.id_asignacion = a.id_asignacion
                         )
                   ) AS asignaciones_pendientes,
                   (
                       SELECT COUNT(DISTINCT p.id_asignacion)
                       FROM partidas_juego p
                       WHERE p.id_usuario = perfil.id_usuario
                         AND p.id_asignacion IS NOT NULL
                   ) AS asignaciones_iniciadas
            FROM perfiles_estudiante perfil
            INNER JOIN usuarios u ON u.id_usuario = perfil.id_usuario
            INNER JOIN docente_secciones ds ON ds.id_seccion = perfil.id_seccion
            INNER JOIN secciones s ON s.id_seccion = perfil.id_seccion
            INNER JOIN institucion_grados ig ON ig.id_institucion_grado = perfil.id_institucion_grado
            INNER JOIN instituciones i ON i.id_institucion = ig.id_institucion
            INNER JOIN grados g ON g.id_grado = ig.id_grado_base
            LEFT JOIN (
                SELECT p.id_usuario,
                       COUNT(DISTINCT p.id_partida) AS total_partidas,
                       COUNT(i.id_intento) AS total_ejercicios,
                       COALESCE(SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS total_aciertos,
                       COALESCE(SUM(CASE WHEN i.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS total_errores,
                       COALESCE(ROUND(100 * SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(i.id_intento), 0), 2), 0) AS porcentaje_aciertos,
                       MAX(COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio)) AS ultima_actividad
                FROM partidas_juego p
                LEFT JOIN intentos_juego i ON i.id_partida = p.id_partida
                WHERE p.tipo_contexto = 'asignacion'
                GROUP BY p.id_usuario
            ) prog ON prog.id_usuario = u.id_usuario
            WHERE perfil.modalidad = 'grupo_educativo'
              AND ds.estado = 'activo'
              {filtro}
            ORDER BY prog.ultima_actividad DESC, u.apellidos ASC, u.nombres ASC
            """,
            tuple(parametros),
        )
        estudiantes = []
        for fila in cursor.fetchall():
            estudiantes.append({
                "id_perfil_estudiante": fila["id_perfil_estudiante"],
                "id_usuario": fila["id_usuario"],
                "id_institucion_grado": fila["id_institucion_grado"],
                "id_seccion": fila.get("id_seccion"),
                "nombres": fila["nombres"],
                "apellidos": fila["apellidos"],
                "correo": fila["correo"],
                "institucion": fila["institucion"],
                "grado": fila["grado"],
                "seccion": fila.get("seccion"),
                "estado": "activo",
                "fecha_ingreso": _serializar_fecha(fila.get("fecha_ingreso")),
                "ultima_actividad": _serializar_fecha(fila.get("ultima_actividad")),
                "total_partidas": int(fila.get("total_partidas") or 0),
                "total_ejercicios": int(fila.get("total_ejercicios") or 0),
                "total_aciertos": int(fila.get("total_aciertos") or 0),
                "total_errores": int(fila.get("total_errores") or 0),
                "porcentaje_aciertos": float(fila.get("porcentaje_aciertos") or 0),
                "asignaciones_pendientes": int(fila.get("asignaciones_pendientes") or 0),
                "asignaciones_iniciadas": int(fila.get("asignaciones_iniciadas") or 0),
            })
        return "consultado", "Estudiantes consultados correctamente.", estudiantes, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_panel_docente(usuario):
    # Resume grados, estudiantes, asignaciones y actividad reciente del docente.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        _sincronizar_estudiantes_visibles(usuario, cursor)
        conexion.commit()

        condicion, parametros = _condiciones_partidas(usuario, {}, alias="p")
        filtro_docente = ""
        parametros_docente = []
        if usuario["rol"] == "docente":
            filtro_docente = "WHERE id_usuario_docente = %s"
            parametros_docente.append(usuario["id_usuario"])
        elif usuario["rol"] != "administrador":
            return "no_autorizado", "Permisos insuficientes.", None, {}

        cursor.execute(
            f"SELECT COUNT(*) AS total FROM docente_grados {filtro_docente} "
            + ("AND estado = 'activo'" if filtro_docente else "WHERE estado = 'activo'"),
            tuple(parametros_docente),
        )
        total_grados = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM asignaciones a
            {filtro_docente.replace('id_usuario_docente', 'a.id_docente')}
            """,
            tuple(parametros_docente),
        )
        total_asignaciones = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute(
            """
            SELECT COUNT(DISTINCT pe.id_usuario) AS total
            FROM perfiles_estudiante pe
            INNER JOIN docente_secciones ds ON ds.id_seccion = pe.id_seccion
            WHERE pe.modalidad = 'grupo_educativo'
              AND ds.estado = 'activo'
            """
            + (" AND ds.id_docente = %s" if usuario["rol"] == "docente" else ""),
            tuple(parametros_docente),
        )
        total_estudiantes = int((cursor.fetchone() or {}).get("total") or 0)
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT p.id_partida) AS partidas,
                   COUNT(i.id_intento) AS intentos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS aciertos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS errores,
                   COALESCE(ROUND(AVG(i.tiempo_respuesta_ms)), 0) AS tiempo_promedio_ms,
                   MAX(COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio)) AS ultima_actividad
            FROM partidas_juego p
            LEFT JOIN intentos_juego i ON i.id_partida = p.id_partida
            WHERE {condicion}
            """,
            tuple(parametros),
        )
        actividad = cursor.fetchone() or {}
        intentos = int(actividad.get("intentos") or 0)
        aciertos = int(actividad.get("aciertos") or 0)
        data = {
            "total_grados": total_grados,
            "total_estudiantes": total_estudiantes,
            "total_asignaciones": total_asignaciones,
            "total_partidas": int(actividad.get("partidas") or 0),
            "total_intentos": intentos,
            "total_aciertos": aciertos,
            "total_errores": int(actividad.get("errores") or 0),
            "porcentaje_aciertos": _porcentaje(aciertos, intentos),
            "tiempo_promedio_ms": int(actividad.get("tiempo_promedio_ms") or 0),
            "ultima_actividad": _serializar_fecha(actividad.get("ultima_actividad")),
        }
        return "consultado", "Panel docente consultado correctamente.", data, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_reporte_agente(usuario, filtros):
    # Construye reporte agregado de desempeno y decisiones adaptativas.
    datos, errores = _validar_filtros(filtros)
    if errores:
        return "datos_invalidos", "Revise los filtros del reporte.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        _sincronizar_estudiantes_visibles(usuario, cursor)
        conexion.commit()

        condicion, parametros = _condiciones_partidas(usuario, datos, alias="p")
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT p.id_usuario) AS estudiantes,
                   COUNT(DISTINCT p.id_partida) AS partidas,
                   COUNT(i.id_intento) AS intentos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS aciertos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS errores,
                   COALESCE(ROUND(AVG(i.tiempo_respuesta_ms)), 0) AS tiempo_promedio_ms
            FROM partidas_juego p
            LEFT JOIN intentos_juego i ON i.id_partida = p.id_partida
            WHERE {condicion}
            """,
            tuple(parametros),
        )
        resumen = cursor.fetchone() or {}
        total_intentos = int(resumen.get("intentos") or 0)
        total_aciertos = int(resumen.get("aciertos") or 0)

        cursor.execute(
            f"""
            SELECT d.accion, COUNT(*) AS total
            FROM decisiones_agente d
            INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
            WHERE {condicion}
            GROUP BY d.accion
            ORDER BY total DESC
            """,
            tuple(parametros),
        )
        decisiones_por_accion = [{"accion": fila["accion"], "total": int(fila["total"])} for fila in cursor.fetchall()]

        cursor.execute(
            f"""
            SELECT d.regla_aplicada, COUNT(*) AS total
            FROM decisiones_agente d
            INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
            WHERE {condicion}
            GROUP BY d.regla_aplicada
            ORDER BY total DESC
            LIMIT 10
            """,
            tuple(parametros),
        )
        reglas_aplicadas = [{"regla": fila["regla_aplicada"], "total": int(fila["total"])} for fila in cursor.fetchall()]

        cursor.execute(
            f"""
            SELECT p.id_usuario, u.nombres, u.apellidos, p.id_tema, t.nombre_tema, g.nombre_grado,
                   COUNT(i.id_intento) AS intentos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END), 0) AS aciertos,
                   COALESCE(SUM(CASE WHEN i.es_correcta = 0 THEN 1 ELSE 0 END), 0) AS errores,
                   COALESCE(SUM(CASE WHEN d.accion = 'reforzar' THEN 1 ELSE 0 END), 0) AS refuerzos,
                   COALESCE(SUM(CASE WHEN d.nivel_anterior <> d.nivel_nuevo THEN 1 ELSE 0 END), 0) AS cambios_nivel,
                   MAX(nn.nombre) AS nivel_actual,
                   MAX(i.fecha_respuesta) AS ultima_practica
            FROM partidas_juego p
            INNER JOIN usuarios u ON u.id_usuario = p.id_usuario
            INNER JOIN temas t ON t.id_tema = p.id_tema
            INNER JOIN grados g ON g.id_grado = t.id_grado
            LEFT JOIN intentos_juego i ON i.id_partida = p.id_partida
            LEFT JOIN decisiones_agente d ON d.id_intento = i.id_intento
            LEFT JOIN niveles_dificultad nn ON nn.id_nivel = p.id_nivel_actual
            WHERE {condicion}
            GROUP BY p.id_usuario, u.nombres, u.apellidos, p.id_tema, t.nombre_tema, g.nombre_grado
            HAVING intentos > 0
            ORDER BY (COALESCE(SUM(CASE WHEN i.es_correcta = 1 THEN 1 ELSE 0 END), 0) / COUNT(i.id_intento)) ASC,
                     errores DESC,
                     ultima_practica DESC
            LIMIT 20
            """,
            tuple(parametros),
        )
        temas_dificultad = []
        alertas = []
        for fila in cursor.fetchall():
            intentos = int(fila.get("intentos") or 0)
            aciertos = int(fila.get("aciertos") or 0)
            errores_total = int(fila.get("errores") or 0)
            porcentaje = _porcentaje(aciertos, intentos)
            consecutivos = _errores_consecutivos(fila["id_usuario"], fila["id_tema"], cursor)
            item = {
                "id_usuario": fila["id_usuario"],
                "estudiante": f"{fila['nombres']} {fila['apellidos']}",
                "id_tema": fila["id_tema"],
                "tema": fila["nombre_tema"],
                "grado": fila["nombre_grado"],
                "nivel_actual": fila.get("nivel_actual"),
                "intentos": intentos,
                "aciertos": aciertos,
                "errores": errores_total,
                "porcentaje_aciertos": porcentaje,
                "errores_consecutivos": consecutivos,
                "refuerzos": int(fila.get("refuerzos") or 0),
                "cambios_nivel": int(fila.get("cambios_nivel") or 0),
                "ultima_practica": _serializar_fecha(fila.get("ultima_practica")),
            }
            temas_dificultad.append(item)
            if intentos >= 3 and porcentaje < 60:
                alertas.append({"tipo": "bajo_rendimiento", "mensaje": "Porcentaje bajo de aciertos.", **item})
            elif consecutivos >= 2:
                alertas.append({"tipo": "errores_consecutivos", "mensaje": "Errores consecutivos recientes.", **item})
            elif item["refuerzos"] >= 2:
                alertas.append({"tipo": "refuerzo_recurrente", "mensaje": "El agente recomendo refuerzo varias veces.", **item})

        data = {
            "resumen": {
                "estudiantes": int(resumen.get("estudiantes") or 0),
                "partidas": int(resumen.get("partidas") or 0),
                "intentos": total_intentos,
                "aciertos": total_aciertos,
                "errores": int(resumen.get("errores") or 0),
                "porcentaje_aciertos": _porcentaje(total_aciertos, total_intentos),
                "tiempo_promedio_ms": int(resumen.get("tiempo_promedio_ms") or 0),
            },
            "decisiones_por_accion": decisiones_por_accion,
            "reglas_aplicadas": reglas_aplicadas,
            "temas_dificultad": temas_dificultad,
            "alertas": alertas[:12],
        }
        return "consultado", "Reporte del agente consultado correctamente.", data, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_decisiones_agente(usuario, filtros, limite=50, offset=0):
    # Devuelve cronologia de decisiones del agente con pregunta y niveles.
    datos, errores = _validar_filtros(filtros)
    if errores:
        return "datos_invalidos", "Revise los filtros del reporte.", None, errores
    limite = min(max(int(limite or 50), 1), 200)
    offset = max(int(offset or 0), 0)

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        condicion, parametros = _condiciones_partidas(usuario, datos, alias="p")
        cursor.execute(
            f"""
            SELECT d.id_decision, d.fecha_decision, d.accion, d.regla_aplicada, d.motivo,
                   p.id_partida, p.id_usuario, p.id_asignacion, p.tipo_contexto,
                   u.nombres, u.apellidos,
                   t.nombre_tema, g.nombre_grado,
                   i.es_correcta, i.respuesta_estudiante,
                   COALESCE(e.enunciado, eg.enunciado) AS pregunta,
                   na.nombre AS nivel_anterior, nn.nombre AS nivel_nuevo
            FROM decisiones_agente d
            INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
            INNER JOIN usuarios u ON u.id_usuario = p.id_usuario
            INNER JOIN temas t ON t.id_tema = d.id_tema
            INNER JOIN grados g ON g.id_grado = t.id_grado
            INNER JOIN intentos_juego i ON i.id_intento = d.id_intento
            INNER JOIN niveles_dificultad na ON na.id_nivel = d.nivel_anterior
            INNER JOIN niveles_dificultad nn ON nn.id_nivel = d.nivel_nuevo
            LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
            LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
            WHERE {condicion}
            ORDER BY d.fecha_decision DESC, d.id_decision DESC
            LIMIT %s OFFSET %s
            """,
            tuple(parametros + [limite, offset]),
        )
        decisiones = []
        for fila in cursor.fetchall():
            decisiones.append({
                "id_decision": fila["id_decision"],
                "fecha_decision": _serializar_fecha(fila.get("fecha_decision")),
                "id_partida": fila["id_partida"],
                "id_usuario": fila["id_usuario"],
                "id_asignacion": fila.get("id_asignacion"),
                "tipo_contexto": fila.get("tipo_contexto"),
                "estudiante": f"{fila['nombres']} {fila['apellidos']}",
                "grado": fila["nombre_grado"],
                "tema": fila["nombre_tema"],
                "pregunta": fila.get("pregunta"),
                "resultado": "correcta" if fila["es_correcta"] else "incorrecta",
                "respuesta_estudiante": fila.get("respuesta_estudiante"),
                "nivel_anterior": fila["nivel_anterior"],
                "accion": fila["accion"],
                "nivel_nuevo": fila["nivel_nuevo"],
                "regla_aplicada": fila["regla_aplicada"],
                "motivo": fila["motivo"],
            })

        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM decisiones_agente d
            INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
            WHERE {condicion}
            """,
            tuple(parametros),
        )
        total = int((cursor.fetchone() or {}).get("total") or 0)
        return "consultado", "Decisiones del agente consultadas correctamente.", {"decisiones": decisiones, "total": total}, {}
    finally:
        cursor.close()
        conexion.close()
