"""Estados de progreso separados para juego personal y actividades docentes."""

from db import obtener_conexion


PROMOCION_GRADO_CONFIG = {
    "min_ejercicios": 12,
    "min_precision": 85,
    "min_correctas_ultimas_seis": 5,
    "temas_representativos_catalogo": 3,
}


# Define el catálogo personal: visible completo, con grado curricular mínimo interno.
CATALOGO_PERSONAL_TEMAS = (
    ("Suma", "Suma", "Aritmética", "4P"),
    ("Resta", "Resta", "Aritmética", "4P"),
    ("Multiplicacion", "Multiplicación", "Aritmética", "4P"),
    ("Division", "División", "Aritmética", "4P"),
    ("Potencias", "Potencias", "Potencias", "4P"),
    ("Raiz cuadrada", "Raíz cuadrada", "Potencias", "4P"),
    ("Operaciones combinadas", "Operaciones combinadas", "Operaciones", "4P"),
    ("Suma de fracciones", "Suma de fracciones", "Fracciones", "4P"),
    ("Resta de fracciones", "Resta de fracciones", "Fracciones", "4P"),
    ("Multiplicacion de fracciones", "Multiplicación de fracciones", "Fracciones", "4P"),
    ("Division de fracciones", "División de fracciones", "Fracciones", "4P"),
    ("Operaciones combinadas de fracciones", "Operaciones combinadas de fracciones", "Fracciones", "5P"),
    ("Conversiones de fracciones", "Conversiones de fracciones", "Fracciones", "5P"),
    ("Suma de decimales", "Suma de decimales", "Decimales", "4P"),
    ("Resta de decimales", "Resta de decimales", "Decimales", "4P"),
    ("Multiplicacion de decimales", "Multiplicación de decimales", "Decimales", "4P"),
    ("Division de decimales", "División de decimales", "Decimales", "4P"),
    ("Porcentajes", "Porcentajes", "Proporcionalidad", "4P"),
    ("Regla de tres directa", "Regla de tres directa", "Proporcionalidad", "5P"),
    ("Regla de tres inversa", "Regla de tres inversa", "Proporcionalidad", "5P"),
    ("Geometria", "Geometría", "Geometría", "6P"),
)
DEFINICIONES_TEMA_PERSONAL = {
    nombre: {"nombre_visible": nombre_visible, "categoria": categoria, "grado_minimo": grado_minimo, "orden": indice}
    for indice, (nombre, nombre_visible, categoria, grado_minimo) in enumerate(CATALOGO_PERSONAL_TEMAS)
}


def _porcentaje(aciertos, intentos):
    # Calcula el porcentaje oficial sin dividir por cero.
    return round((aciertos / intentos) * 100, 2) if intentos else 0


def _serializar_fecha(valor):
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _nivel_inicial(cursor):
    cursor.execute("""
        SELECT id_nivel, codigo, nombre, orden_nivel
        FROM niveles_dificultad
        WHERE estado = 'activo'
        ORDER BY es_inicial DESC, orden_nivel ASC LIMIT 1
    """)
    return cursor.fetchone()


def _grado_por_codigo(codigo, cursor):
    cursor.execute("""
        SELECT id_grado, codigo_grado, nombre_grado, orden_visualizacion
        FROM grados WHERE codigo_grado = %s AND estado = 'activo' LIMIT 1
    """, (codigo,))
    return cursor.fetchone()


def _grado_por_id(id_grado, cursor):
    cursor.execute("""
        SELECT id_grado, codigo_grado, nombre_grado, orden_visualizacion
        FROM grados WHERE id_grado = %s
    """, (id_grado,))
    return cursor.fetchone()


def _grado_siguiente(id_grado, cursor):
    cursor.execute("""
        SELECT siguiente.id_grado, siguiente.codigo_grado, siguiente.nombre_grado, siguiente.orden_visualizacion
        FROM grados actual
        INNER JOIN grados siguiente ON siguiente.orden_visualizacion > actual.orden_visualizacion
        WHERE actual.id_grado = %s AND siguiente.codigo_grado IN ('4P', '5P', '6P')
          AND siguiente.estado = 'activo'
        ORDER BY siguiente.orden_visualizacion ASC LIMIT 1
    """, (id_grado,))
    return cursor.fetchone()


def _tema_por_id(id_tema, cursor):
    cursor.execute("""
        SELECT t.id_tema, t.nombre_tema, t.id_grado, g.codigo_grado, g.orden_visualizacion
        FROM temas t INNER JOIN grados g ON g.id_grado = t.id_grado
        WHERE t.id_tema = %s AND t.estado = 'activo' AND g.estado = 'activo' LIMIT 1
    """, (id_tema,))
    return cursor.fetchone()


def _tema_equivalente(nombre_tema, id_grado, cursor):
    cursor.execute("""
        SELECT id_tema, nombre_tema, id_grado
        FROM temas WHERE nombre_tema = %s AND id_grado = %s AND estado = 'activo' LIMIT 1
    """, (nombre_tema, id_grado))
    return cursor.fetchone()


def _catalogo_personal(id_usuario, cursor, bloquear=False):
    cursor.execute(f"""
        SELECT ppc.*, g.codigo_grado, g.orden_visualizacion
        FROM progreso_personal_catalogo ppc
        INNER JOIN grados g ON g.id_grado = ppc.id_grado_desbloqueado
        WHERE ppc.id_usuario = %s {'FOR UPDATE' if bloquear else ''}
    """, (id_usuario,))
    catalogo = cursor.fetchone()
    if catalogo:
        return catalogo
    cuarto = _grado_por_codigo("4P", cursor)
    if not cuarto:
        raise RuntimeError("No existe Cuarto primaria activo para el juego personal.")
    cursor.execute("INSERT INTO progreso_personal_catalogo (id_usuario, id_grado_desbloqueado) VALUES (%s, %s)", (id_usuario, cuarto["id_grado"]))
    return {"id_usuario": id_usuario, "id_grado_desbloqueado": cuarto["id_grado"], **cuarto}


def listar_temas_personales(id_usuario, cursor):
    # Expone todo el catálogo; el grado mínimo se usa al crear progreso, no para ocultar temas.
    nombres = tuple(DEFINICIONES_TEMA_PERSONAL)
    marcadores = ", ".join(["%s"] * len(nombres))
    cursor.execute("""
        SELECT t.id_tema, t.nombre_tema
        FROM temas t INNER JOIN grados g ON g.id_grado = t.id_grado
        WHERE t.estado = 'activo' AND g.estado = 'activo'
          AND g.codigo_grado IN ('4P', '5P', '6P')
          AND t.nombre_tema IN (""" + marcadores + """)
          AND NOT EXISTS (
              SELECT 1 FROM temas previo INNER JOIN grados gp ON gp.id_grado = previo.id_grado
              WHERE previo.nombre_tema = t.nombre_tema AND previo.estado = 'activo'
                AND gp.estado = 'activo' AND gp.codigo_grado IN ('4P', '5P', '6P')
                AND gp.orden_visualizacion < g.orden_visualizacion
          )
    """, nombres)
    return sorted(cursor.fetchall(), key=lambda tema: DEFINICIONES_TEMA_PERSONAL[tema["nombre_tema"]]["orden"])


def _tema_permitido_personal(id_usuario, id_tema, cursor):
    return any(int(tema["id_tema"]) == int(id_tema) for tema in listar_temas_personales(id_usuario, cursor))


def _estado_personal(id_usuario, tema_clave, cursor, bloquear=False):
    cursor.execute(f"""
        SELECT ppt.*, g.codigo_grado, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
        FROM progreso_personal_tema ppt
        INNER JOIN grados g ON g.id_grado = ppt.id_grado_curricular
        INNER JOIN niveles_dificultad n ON n.id_nivel = ppt.id_nivel_actual
        WHERE ppt.id_usuario = %s AND ppt.tema_clave = %s {'FOR UPDATE' if bloquear else ''}
    """, (id_usuario, tema_clave))
    return cursor.fetchone()


def obtener_o_crear_estado_personal(id_usuario, id_tema_solicitado, cursor, bloquear=False):
    """Resuelve la ruta personal sin aceptar grado ni dificultad desde el cliente."""
    if not _tema_permitido_personal(id_usuario, id_tema_solicitado, cursor):
        return None
    solicitado = _tema_por_id(id_tema_solicitado, cursor)
    if not solicitado:
        return None
    estado = _estado_personal(id_usuario, solicitado["nombre_tema"], cursor, bloquear)
    if estado:
        return estado
    nivel = _nivel_inicial(cursor)
    cuarto = _grado_por_codigo("4P", cursor)
    tema_cuarto = _tema_equivalente(solicitado["nombre_tema"], cuarto["id_grado"], cursor) if cuarto else None
    # Un tema exclusivo nace en el grado que abrió el catálogo; uno compartido, en Cuarto.
    inicial = tema_cuarto or solicitado
    cursor.execute("""
        INSERT INTO progreso_personal_tema
            (id_usuario, tema_clave, id_tema_actual, id_grado_curricular, id_nivel_actual)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_usuario, solicitado["nombre_tema"], inicial["id_tema"], inicial["id_grado"], nivel["id_nivel"]))
    return _estado_personal(id_usuario, solicitado["nombre_tema"], cursor, bloquear)


def _estado_asignacion(id_usuario, id_asignacion, id_tema, id_grado, cursor, id_nivel_inicial=None, bloquear=False):
    cursor.execute(f"""
        SELECT pat.*, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
        FROM progreso_asignacion_tema_estudiante pat
        INNER JOIN niveles_dificultad n ON n.id_nivel = pat.id_nivel_actual
        WHERE pat.id_estudiante = %s AND pat.id_asignacion = %s AND pat.id_tema = %s
        {'FOR UPDATE' if bloquear else ''}
    """, (id_usuario, id_asignacion, id_tema))
    estado = cursor.fetchone()
    if estado:
        return estado
    nivel_inicial = id_nivel_inicial or _nivel_inicial(cursor)["id_nivel"]
    cursor.execute("""
        INSERT INTO progreso_asignacion_tema_estudiante
            (id_asignacion, id_estudiante, id_tema, id_grado_asignacion, id_nivel_actual)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_asignacion, id_usuario, id_tema, id_grado, nivel_inicial))
    return _estado_asignacion(id_usuario, id_asignacion, id_tema, id_grado, cursor, id_nivel_inicial, bloquear)


def obtener_estado_asignacion(id_usuario, id_asignacion, id_tema, id_grado, cursor, id_nivel_inicial=None, bloquear=False):
    # El grado proviene de la asignación, nunca del perfil ni del progreso personal.
    return _estado_asignacion(id_usuario, id_asignacion, id_tema, id_grado, cursor, id_nivel_inicial, bloquear)


def evaluar_progresion_personal(estado, nivel_actual, codigo_grado, resultados_recientes=None):
    """Devuelve promover_grado solo con evidencia sostenida en dificultad difícil."""
    if codigo_grado not in ("4P", "5P") or nivel_actual.get("codigo") != "dificil":
        return "mantener"
    if int(estado.get("intentos_dificil", estado.get("total_intentos", 0)) or 0) < PROMOCION_GRADO_CONFIG["min_ejercicios"]:
        return "mantener"
    if float(estado.get("precision_dificil", estado.get("porcentaje_aciertos", 0)) or 0) < PROMOCION_GRADO_CONFIG["min_precision"]:
        return "mantener"
    recientes = list(resultados_recientes or [])[-6:]
    if len(recientes) < 6 or sum(1 for resultado in recientes if resultado) < PROMOCION_GRADO_CONFIG["min_correctas_ultimas_seis"]:
        return "mantener"
    return "promover_grado"


def _evidencia_dificil_personal(partida, cursor):
    """Resume solo intentos personales del tema, grado y nivel difícil actuales."""
    cursor.execute("""
        SELECT i.es_correcta
        FROM intentos_juego i
        INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
        WHERE p.id_usuario = %s AND p.tipo_contexto = 'personal'
          AND p.id_grado = %s AND p.id_tema = %s AND i.nivel_al_responder = %s
        ORDER BY i.id_intento DESC
    """, (partida["id_usuario"], partida["id_grado"], partida["id_tema"], partida["id_nivel_actual"]))
    resultados = [bool(fila["es_correcta"]) for fila in cursor.fetchall()]
    intentos = len(resultados)
    return {
        "intentos_dificil": intentos,
        "precision_dificil": _porcentaje(sum(resultados), intentos),
        "resultados_recientes": list(reversed(resultados[:6])),
    }


def _actualizar_catalogo_si_corresponde(id_usuario, id_grado_origen, id_grado_nuevo, cursor):
    # Impide que un único tema desbloquee prematuramente el catálogo siguiente.
    catalogo = _catalogo_personal(id_usuario, cursor, bloquear=True)
    cursor.execute("""
        SELECT COUNT(*) AS total FROM progreso_personal_tema
        WHERE id_usuario = %s AND id_grado_curricular = %s AND estado_dominio = 'dominado'
    """, (id_usuario, id_grado_nuevo))
    promovidos = int((cursor.fetchone() or {}).get("total") or 0)
    cursor.execute("SELECT COUNT(DISTINCT nombre_tema) AS total FROM temas WHERE id_grado = %s AND estado = 'activo'", (id_grado_origen,))
    requeridos = min(PROMOCION_GRADO_CONFIG["temas_representativos_catalogo"], max(int((cursor.fetchone() or {}).get("total") or 0), 1))
    nuevo_grado = _grado_por_id(id_grado_nuevo, cursor)
    if promovidos >= requeridos and nuevo_grado and catalogo["orden_visualizacion"] < nuevo_grado["orden_visualizacion"]:
        cursor.execute("UPDATE progreso_personal_catalogo SET id_grado_desbloqueado = %s WHERE id_usuario = %s", (id_grado_nuevo, id_usuario))
        return True
    return False


def _actualizar_estado_personal(partida, es_correcta, tiempo_ms, nivel_recomendado, cursor):
    tema_clave = partida.get("tema_clave")
    if not tema_clave:
        tema = _tema_por_id(partida["id_tema"], cursor)
        tema_clave = tema["nombre_tema"] if tema else None
    estado = _estado_personal(partida["id_usuario"], tema_clave, cursor, bloquear=True)
    if not estado:
        raise RuntimeError("No existe el estado personal de la partida.")
    intentos_previos = int(estado["total_intentos"])
    intentos = intentos_previos + 1
    aciertos = int(estado["total_aciertos"]) + (1 if es_correcta else 0)
    errores = int(estado["total_errores"]) + (0 if es_correcta else 1)
    racha_correctas = int(estado["racha_correctas"]) + 1 if es_correcta else 0
    racha_incorrectas = 0 if es_correcta else int(estado["racha_incorrectas"]) + 1
    promedio = round(((int(estado["tiempo_promedio_ms"]) * intentos_previos) + tiempo_ms) / intentos)
    cursor.execute("""
        SELECT COUNT(DISTINCT id_partida) AS total
        FROM partidas_juego
        WHERE id_usuario = %s AND tipo_contexto = 'personal' AND id_tema = %s
    """, (partida["id_usuario"], estado["id_tema_actual"]))
    partidas = int((cursor.fetchone() or {}).get("total") or 0)
    actualizado = {**estado, "total_intentos": intentos, "total_aciertos": aciertos, "total_errores": errores,
                  "porcentaje_aciertos": _porcentaje(aciertos, intentos), "racha_correctas": racha_correctas,
                  "racha_incorrectas": racha_incorrectas, "partidas_distintas": partidas}

    siguiente_grado, siguiente_tema, siguiente_nivel = estado["id_grado_curricular"], estado["id_tema_actual"], nivel_recomendado["id_nivel"]
    accion, codigo_regla, promocionado = "mantener", None, False
    nivel_actual = {"codigo": estado["codigo_nivel"]}
    evidencia = _evidencia_dificil_personal(partida, cursor) if nivel_actual["codigo"] == "dificil" else {}
    if evaluar_progresion_personal({**actualizado, **evidencia}, nivel_actual, estado["codigo_grado"], evidencia.get("resultados_recientes")) == "promover_grado":
        grado_nuevo = _grado_siguiente(estado["id_grado_curricular"], cursor)
        tema_nuevo = _tema_equivalente(partida["tema_clave"], grado_nuevo["id_grado"], cursor) if grado_nuevo else None
        facil = _nivel_inicial(cursor)
        if tema_nuevo and facil:
            siguiente_grado, siguiente_tema, siguiente_nivel = grado_nuevo["id_grado"], tema_nuevo["id_tema"], facil["id_nivel"]
            accion, codigo_regla, promocionado = "promover_grado", "dominio_curricular_sostenido", True
            # La dificultad se reinicia para el nuevo grado; los intentos siguen en el historial.
            intentos = aciertos = errores = racha_correctas = racha_incorrectas = promedio = partidas = 0

    porcentaje = _porcentaje(aciertos, intentos)
    dominio = "dominado" if promocionado else ("dominado" if intentos >= PROMOCION_GRADO_CONFIG["min_ejercicios"] and porcentaje >= PROMOCION_GRADO_CONFIG["min_precision"] else ("en_progreso" if intentos else "inicial"))
    cursor.execute("""
        UPDATE progreso_personal_tema
        SET id_tema_actual = %s, id_grado_curricular = %s, id_nivel_actual = %s,
            total_intentos = %s, total_aciertos = %s, total_errores = %s, porcentaje_aciertos = %s,
            racha_correctas = %s, racha_incorrectas = %s, partidas_distintas = %s, estado_dominio = %s,
            tiempo_promedio_ms = %s, cambios_dificultad = cambios_dificultad + %s,
            ultima_practica = CURRENT_TIMESTAMP
        WHERE id_progreso_personal_tema = %s
    """, (siguiente_tema, siguiente_grado, siguiente_nivel, intentos, aciertos, errores, porcentaje,
            racha_correctas, racha_incorrectas, partidas, dominio, promedio,
            1 if estado["id_nivel_actual"] != siguiente_nivel else 0, estado["id_progreso_personal_tema"]))
    if promocionado:
        _actualizar_catalogo_si_corresponde(partida["id_usuario"], estado["id_grado_curricular"], siguiente_grado, cursor)
    return {"id_grado": siguiente_grado, "id_tema": siguiente_tema, "id_nivel": siguiente_nivel,
            "accion": accion, "codigo_regla": codigo_regla, "promocionado": promocionado}


def _actualizar_estado_asignacion(partida, es_correcta, tiempo_ms, nivel_recomendado, cursor):
    estado = _estado_asignacion(partida["id_usuario"], partida["id_asignacion"], partida["id_tema"], partida["id_grado"], cursor, bloquear=True)
    previos = int(estado["total_intentos"])
    intentos, aciertos = previos + 1, int(estado["total_aciertos"]) + (1 if es_correcta else 0)
    errores = int(estado["total_errores"]) + (0 if es_correcta else 1)
    rc = int(estado["racha_correctas"]) + 1 if es_correcta else 0
    ri = 0 if es_correcta else int(estado["racha_incorrectas"]) + 1
    promedio = round(((int(estado["tiempo_promedio_ms"]) * previos) + tiempo_ms) / intentos)
    cursor.execute("""
        UPDATE progreso_asignacion_tema_estudiante
        SET id_nivel_actual = %s, total_intentos = %s, total_aciertos = %s, total_errores = %s,
            porcentaje_aciertos = %s, racha_correctas = %s, racha_incorrectas = %s,
            partidas_distintas = partidas_distintas + %s, tiempo_promedio_ms = %s,
            cambios_dificultad = cambios_dificultad + %s, ultima_practica = CURRENT_TIMESTAMP
        WHERE id_progreso_asignacion_tema = %s
    """, (nivel_recomendado["id_nivel"], intentos, aciertos, errores, _porcentaje(aciertos, intentos), rc, ri,
            1 if not previos else 0, promedio, 1 if estado["id_nivel_actual"] != nivel_recomendado["id_nivel"] else 0,
            estado["id_progreso_asignacion_tema"]))
    return {"id_grado": partida["id_grado"], "id_tema": partida["id_tema"], "id_nivel": nivel_recomendado["id_nivel"],
            "accion": "mantener", "codigo_regla": None, "promocionado": False}


def actualizar_progreso_contextual(partida, es_correcta, tiempo_ms, nivel_recomendado, cursor):
    # Actualiza exclusivamente el estado que originó la respuesta.
    if partida.get("tipo_contexto") == "asignacion":
        return _actualizar_estado_asignacion(partida, es_correcta, tiempo_ms, nivel_recomendado, cursor)
    return _actualizar_estado_personal(partida, es_correcta, tiempo_ms, nivel_recomendado, cursor)


def sincronizar_progreso_usuario(id_usuario, cursor):
    # El panel personal no mezcla actividades evaluables por el docente.
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id_partida) AS total_partidas, COUNT(i.id_intento) AS total_ejercicios,
               COALESCE(SUM(i.es_correcta = 1), 0) AS total_aciertos, COALESCE(SUM(i.es_correcta = 0), 0) AS total_errores,
               COALESCE(MAX(p.total_correctos), 0) AS mejor_puntuacion, COALESCE(SUM(i.tiempo_respuesta_ms), 0) AS tiempo_total_ms,
               MAX(COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio)) AS ultima_actividad
        FROM partidas_juego p LEFT JOIN intentos_juego i ON i.id_partida = p.id_partida
        WHERE p.id_usuario = %s AND p.tipo_contexto = 'personal'
    """, (id_usuario,))
    fila = cursor.fetchone() or {}
    intentos, aciertos = int(fila.get("total_ejercicios") or 0), int(fila.get("total_aciertos") or 0)
    cursor.execute("""
        INSERT INTO progreso_estudiante
            (id_usuario, total_partidas, total_ejercicios, total_aciertos, total_errores, porcentaje_aciertos,
             puntos, mejor_puntuacion, tiempo_total_ms, ultima_actividad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE total_partidas = VALUES(total_partidas), total_ejercicios = VALUES(total_ejercicios),
            total_aciertos = VALUES(total_aciertos), total_errores = VALUES(total_errores), porcentaje_aciertos = VALUES(porcentaje_aciertos),
            puntos = VALUES(puntos), mejor_puntuacion = VALUES(mejor_puntuacion), tiempo_total_ms = VALUES(tiempo_total_ms),
            ultima_actividad = VALUES(ultima_actividad)
    """, (id_usuario, int(fila.get("total_partidas") or 0), intentos, aciertos, int(fila.get("total_errores") or 0),
            _porcentaje(aciertos, intentos), aciertos, int(fila.get("mejor_puntuacion") or 0),
            int(fila.get("tiempo_total_ms") or 0), fila.get("ultima_actividad")))


def _serializar_progreso_tema(fila):
    return {"id_progreso_tema_estudiante": fila["id_progreso_personal_tema"], "id_usuario": fila["id_usuario"],
            "id_tema": fila["id_tema_actual"], "nombre_tema": fila["tema_clave"], "grado_curricular": fila["nombre_grado"],
            "id_grado_curricular_actual": fila["id_grado_curricular"], "id_nivel_actual": fila["id_nivel_actual"],
            "codigo_nivel": fila["codigo_nivel"], "nombre_nivel": fila["nombre_nivel"],
            "total_intentos": int(fila["total_intentos"]), "total_aciertos": int(fila["total_aciertos"]),
            "total_errores": int(fila["total_errores"]), "porcentaje_aciertos": float(fila["porcentaje_aciertos"]),
            "racha_correctas": int(fila["racha_correctas"]), "racha_incorrectas": int(fila["racha_incorrectas"]),
            "estado_dominio": fila["estado_dominio"], "tiempo_promedio_ms": int(fila["tiempo_promedio_ms"]),
            "cambios_dificultad": int(fila["cambios_dificultad"]), "ultima_practica": _serializar_fecha(fila.get("ultima_practica"))}


def obtener_progreso_estudiante(usuario):
    conexion = obtener_conexion(); cursor = conexion.cursor(dictionary=True)
    try:
        sincronizar_progreso_usuario(usuario["id_usuario"], cursor)
        cursor.execute("SELECT * FROM progreso_estudiante WHERE id_usuario = %s", (usuario["id_usuario"],))
        resumen = cursor.fetchone() or {}
        cursor.execute("""
            SELECT ppt.*, g.nombre_grado, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel
            FROM progreso_personal_tema ppt INNER JOIN grados g ON g.id_grado = ppt.id_grado_curricular
            INNER JOIN niveles_dificultad n ON n.id_nivel = ppt.id_nivel_actual
            WHERE ppt.id_usuario = %s ORDER BY ppt.ultima_practica DESC, ppt.tema_clave ASC
        """, (usuario["id_usuario"],))
        temas = [_serializar_progreso_tema(fila) for fila in cursor.fetchall()]
        conexion.commit()
        return "consultado", "Progreso consultado correctamente.", {"progreso": resumen, "temas": temas}, {}
    except Exception:
        conexion.rollback(); raise
    finally:
        cursor.close(); conexion.close()


def obtener_historial_estudiante(usuario, limite=20, offset=0):
    limite, offset = min(max(int(limite or 20), 1), 100), max(int(offset or 0), 0)
    conexion = obtener_conexion(); cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, a.nombre AS asignacion, g.nombre_grado, t.nombre_tema, ni.nombre AS nivel_inicial, nf.nombre AS nivel_final
            FROM partidas_juego p LEFT JOIN asignaciones a ON a.id_asignacion = p.id_asignacion
            LEFT JOIN grados g ON g.id_grado = p.id_grado LEFT JOIN temas t ON t.id_tema = p.id_tema
            LEFT JOIN niveles_dificultad ni ON ni.id_nivel = p.id_nivel_inicial LEFT JOIN niveles_dificultad nf ON nf.id_nivel = p.id_nivel_actual
            WHERE p.id_usuario = %s ORDER BY COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio) DESC, p.id_partida DESC LIMIT %s OFFSET %s
        """, (usuario["id_usuario"], limite, offset))
        historial = []
        for fila in cursor.fetchall():
            respuestas = int(fila.get("preguntas_respondidas") or 0); aciertos = int(fila.get("total_correctos") or 0)
            historial.append({"id_partida": fila["id_partida"], "id_asignacion": fila.get("id_asignacion"), "asignacion": fila.get("asignacion"),
                "fecha_inicio": _serializar_fecha(fila.get("fecha_inicio")), "fecha_fin": _serializar_fecha(fila.get("fecha_fin")),
                "ultima_actividad": _serializar_fecha(fila.get("fecha_ultima_actividad")), "grado": fila.get("nombre_grado"), "tema": fila.get("nombre_tema"),
                "nivel_inicial": fila.get("nivel_inicial"), "nivel_final": fila.get("nivel_final"), "aciertos": aciertos,
                "errores": int(fila.get("total_errores") or 0), "intentos": respuestas, "porcentaje_aciertos": _porcentaje(aciertos, respuestas),
                "puntuacion": aciertos, "estado": fila.get("estado"), "motivo_finalizacion": fila.get("motivo_finalizacion")})
        cursor.execute("SELECT COUNT(*) AS total FROM partidas_juego WHERE id_usuario = %s", (usuario["id_usuario"],))
        return "consultado", "Historial consultado correctamente.", {"historial": historial, "total": int((cursor.fetchone() or {}).get("total") or 0)}, {}
    finally:
        cursor.close(); conexion.close()


def obtener_panel_estudiante(usuario):
    estado, mensaje, datos, errores = obtener_progreso_estudiante(usuario)
    if estado != "consultado":
        return estado, mensaje, datos, errores
    _, _, historial, _ = obtener_historial_estudiante(usuario, limite=5, offset=0)
    return "consultado", "Panel estudiante consultado correctamente.", {**datos, "historial_reciente": historial["historial"]}, {}
