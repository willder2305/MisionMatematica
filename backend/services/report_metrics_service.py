"""Metricas reutilizables para los reportes de administrador y docente."""

from collections import defaultdict


TAMANO_VENTANA_MEJORA = 10
INTENTOS_MINIMOS_MEJORA = TAMANO_VENTANA_MEJORA * 2
SIN_DATOS_SUFFICIENTES = "Sin datos suficientes"
SIN_PROGRESO_REGISTRADO = "Sin progreso registrado"


def calcular_porcentaje(aciertos, intentos):
    """Calcula precisión porcentual redondeada, sin dividir entre cero."""
    return round((int(aciertos or 0) / int(intentos or 0)) * 100, 2) if intentos else 0


def calcular_mejora(intentos):
    """Compara los 10 intentos más recientes con los 10 inmediatamente anteriores.

    La mejora se expresa en puntos porcentuales y solo existe cuando ambas
    ventanas están completas; con menos de 20 intentos no se infiere tendencia.
    """
    if len(intentos) < INTENTOS_MINIMOS_MEJORA:
        return None, "sin_datos_suficientes"

    anteriores = intentos[-INTENTOS_MINIMOS_MEJORA:-TAMANO_VENTANA_MEJORA]
    recientes = intentos[-TAMANO_VENTANA_MEJORA:]
    precision_anterior = calcular_porcentaje(sum(bool(item) for item in anteriores), TAMANO_VENTANA_MEJORA)
    precision_reciente = calcular_porcentaje(sum(bool(item) for item in recientes), TAMANO_VENTANA_MEJORA)
    return round(precision_reciente - precision_anterior, 2), "suficiente"


def _pares_unicos(filas, campo_estudiante, campo_tema):
    # Evita repetir pares antes de construir la consulta por lote.
    return sorted({
        (int(fila[campo_estudiante]), int(fila[campo_tema]))
        for fila in filas
        if fila.get(campo_estudiante) is not None and fila.get(campo_tema) is not None
    })


def _condicion_pares(pares, alias_partida="p"):
    # MySQL no acepta una lista de tuplas parametrizada directamente en todos los conectores.
    condiciones = []
    parametros = []
    for id_estudiante, id_tema in pares:
        condiciones.append(f"({alias_partida}.id_usuario = %s AND {alias_partida}.id_tema = %s)")
        parametros.extend([id_estudiante, id_tema])
    return " OR ".join(condiciones), parametros


def obtener_metricas_por_estudiante_tema(
    cursor,
    filas,
    filtros,
    campo_estudiante="id_estudiante",
    campo_tema="id_tema",
    condicion_partidas=None,
    parametros_partidas=None,
):
    """Obtiene precisión, mejora y nivel actual para varias filas en dos consultas.

    Las fechas, cuando existen, se aplican sobre cada intento. Así precisión y
    mejora usan exactamente el mismo periodo visible en el reporte.
    """
    pares = _pares_unicos(filas, campo_estudiante, campo_tema)
    if not pares:
        return {}

    condicion_pares, parametros = _condicion_pares(pares)
    condiciones_fecha = []
    parametros_fecha = []
    if filtros.get("fecha_inicio"):
        condiciones_fecha.append("i.fecha_respuesta >= %s")
        parametros_fecha.append(filtros["fecha_inicio"])
    if filtros.get("fecha_fin"):
        condiciones_fecha.append("i.fecha_respuesta <= %s")
        parametros_fecha.append(filtros["fecha_fin"])
    where_fecha = f" AND {' AND '.join(condiciones_fecha)}" if condiciones_fecha else ""
    where_partidas = f" AND ({condicion_partidas})" if condicion_partidas else ""
    parametros_partidas = list(parametros_partidas or [])

    cursor.execute(
        f"""
        SELECT p.id_usuario AS id_estudiante, p.id_tema, i.es_correcta
        FROM intentos_juego i
        INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
        WHERE ({condicion_pares}){where_partidas}{where_fecha}
        ORDER BY p.id_usuario ASC, p.id_tema ASC, i.fecha_respuesta ASC, i.id_intento ASC
        """,
        tuple(parametros + parametros_partidas + parametros_fecha),
    )
    intentos_por_par = defaultdict(list)
    for fila in cursor.fetchall():
        intentos_por_par[(fila["id_estudiante"], fila["id_tema"])].append(bool(fila["es_correcta"]))

    cursor.execute(
        f"""
        SELECT pte.id_usuario AS id_estudiante, pte.id_tema,
               COALESCE(g_progreso.nombre_grado, g_tema.nombre_grado) AS grado,
               nivel.nombre AS dificultad
        FROM progreso_tema_estudiante pte
        INNER JOIN temas t ON t.id_tema = pte.id_tema
        LEFT JOIN grados g_progreso ON g_progreso.id_grado = pte.id_grado_curricular_actual
        LEFT JOIN grados g_tema ON g_tema.id_grado = t.id_grado
        LEFT JOIN niveles_dificultad nivel ON nivel.id_nivel = pte.id_nivel_actual
        WHERE ({condicion_pares})
        """,
        tuple(parametros),
    )
    niveles = {
        (fila["id_estudiante"], fila["id_tema"]): " - ".join(
            parte for parte in (fila.get("grado"), fila.get("dificultad")) if parte
        ) or SIN_PROGRESO_REGISTRADO
        for fila in cursor.fetchall()
    }

    resultado = {}
    for par in pares:
        intentos = intentos_por_par[par]
        aciertos = sum(intentos)
        mejora, estado = calcular_mejora(intentos)
        errores_consecutivos = 0
        for correcto in reversed(intentos):
            if correcto:
                break
            errores_consecutivos += 1
        resultado[par] = {
            "intentos": len(intentos),
            "aciertos": aciertos,
            "errores": len(intentos) - aciertos,
            "precision": calcular_porcentaje(aciertos, len(intentos)),
            "improvement_percentage": mejora,
            "improvement_status": estado,
            "mejora": f"{mejora:+.2f} pp" if mejora is not None else SIN_DATOS_SUFFICIENTES,
            "nivel_actual": niveles.get(par, SIN_PROGRESO_REGISTRADO),
            "errores_consecutivos": errores_consecutivos,
        }
    return resultado


def aplicar_metricas_reporte(
    cursor,
    filas,
    filtros,
    campo_estudiante="id_estudiante",
    campo_tema="id_tema",
    condicion_partidas=None,
    parametros_partidas=None,
):
    """Enriquece filas de reporte con los mismos datos calculados por lote."""
    metricas = obtener_metricas_por_estudiante_tema(
        cursor,
        filas,
        filtros,
        campo_estudiante,
        campo_tema,
        condicion_partidas,
        parametros_partidas,
    )
    for fila in filas:
        par = (fila.get(campo_estudiante), fila.get(campo_tema))
        metrica = metricas.get(par)
        if not metrica:
            continue
        fila.update(metrica)
        fila["correctos"] = metrica["aciertos"]
        fila["porcentaje_aciertos"] = metrica["precision"]
    return filas
