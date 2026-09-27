import json
import re

from db import obtener_conexion


def _pasos_guardados(valor):
    # Recupera pasos persistidos sin asumir que el conector entregue JSON como lista.
    if isinstance(valor, list):
        return [str(paso).strip() for paso in valor if str(paso).strip()]
    if isinstance(valor, str):
        try:
            pasos = json.loads(valor)
        except json.JSONDecodeError:
            return []
        return [str(paso).strip() for paso in pasos] if isinstance(pasos, list) else []
    return []


# Devuelve pasos breves para ejercicios importados o para historiales sin pasos persistidos.
def obtener_explicacion_pasos_ejercicio(ejercicio):
    pasos = _pasos_guardados(ejercicio.get("explicacion_pasos"))
    if pasos:
        return pasos[:4]

    explicacion = str(ejercicio.get("explicacion") or "").strip()
    enunciado = str(ejercicio.get("enunciado") or "")
    respuesta = str(ejercicio.get("respuesta_correcta") or "").strip()
    coincidencia = re.search(r"(-?\d+(?:[.,]\d+)?)\s*([+\-xX*/÷×])\s*(-?\d+(?:[.,]\d+)?)", enunciado)
    if not coincidencia:
        return [explicacion] if explicacion else ["Revisa los datos y la operación indicada."]

    izquierda, operador, derecha = coincidencia.groups()
    simbolo = {"x": "×", "X": "×", "*": "×", "÷": "÷", "/": "÷"}.get(operador, operador)
    return [f"{izquierda} {simbolo} {derecha} = {respuesta}."]


# Conserva el texto plano para integraciones antiguas que aún lo consumen.
def obtener_explicacion_ejercicio(ejercicio):
    return " ".join(obtener_explicacion_pasos_ejercicio(ejercicio))


# Arma la pregunta que se envia a React sin incluir la respuesta correcta.
def serializar_pregunta(ejercicio, opciones):
    if not ejercicio:
        return None
    return {
        "id_ejercicio": ejercicio["id_ejercicio"],
        "id_tema": ejercicio["id_tema"],
        "id_nivel": ejercicio["id_nivel"],
        "nivel": {
            "id_nivel": ejercicio["id_nivel"],
            "codigo": ejercicio["codigo_nivel"],
            "nombre": ejercicio["nombre_nivel"],
            "orden_nivel": ejercicio["orden_nivel"],
        },
        "enunciado": ejercicio["enunciado"],
        "tipo_respuesta": ejercicio["tipo_respuesta"],
        "pista": ejercicio.get("pista"),
        "opciones": opciones,
    }


# Busca un ejercicio publicado por id; se usa para validar la pregunta actual.
def obtener_ejercicio_publicado(id_ejercicio, cursor=None):
    cerrar = cursor is None
    conexion = None
    if cerrar:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT e.*, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
            FROM ejercicios e
            INNER JOIN niveles_dificultad n ON n.id_nivel = e.id_nivel
            WHERE e.id_ejercicio = %s
              AND e.estado = 'publicado'
            """,
            (id_ejercicio,),
        )
        return cursor.fetchone()
    finally:
        if cerrar:
            cursor.close()
            conexion.close()


# Carga las opciones visibles de un ejercicio de seleccion multiple.
def obtener_opciones_ejercicio(id_ejercicio, cursor=None):
    cerrar = cursor is None
    conexion = None
    if cerrar:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
    try:
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
    finally:
        if cerrar:
            cursor.close()
            conexion.close()


# Convierte un ejercicio guardado en la estructura segura que consume el frontend.
def preparar_pregunta(id_ejercicio, cursor=None):
    ejercicio = obtener_ejercicio_publicado(id_ejercicio, cursor)
    if not ejercicio:
        return None
    opciones = obtener_opciones_ejercicio(id_ejercicio, cursor) if ejercicio["tipo_respuesta"] == "seleccion_multiple" else []
    return serializar_pregunta(ejercicio, opciones)


# Selecciona la siguiente pregunta por grado, tema y nivel, evitando repetir si es posible.
def seleccionar_siguiente_ejercicio(id_grado, id_tema, id_nivel, id_partida=None, cursor=None):
    cerrar = cursor is None
    conexion = None
    if cerrar:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
    try:
        parametros = [id_grado, id_tema, id_nivel]
        filtro_repetidos = ""
        if id_partida:
            filtro_repetidos = """
              AND e.id_ejercicio NOT IN (
                  SELECT id_ejercicio
                  FROM intentos_juego
                  WHERE id_partida = %s
              )
            """
            parametros.append(id_partida)

        cursor.execute(
            f"""
            SELECT e.*, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
            FROM ejercicios e
            INNER JOIN temas t ON t.id_tema = e.id_tema
            INNER JOIN niveles_dificultad n ON n.id_nivel = e.id_nivel
            WHERE t.id_grado = %s
              AND e.id_tema = %s
              AND e.id_nivel = %s
              AND e.estado = 'publicado'
              {filtro_repetidos}
            ORDER BY e.id_ejercicio ASC
            LIMIT 1
            """,
            tuple(parametros),
        )
        ejercicio = cursor.fetchone()

        if not ejercicio:
            cursor.execute(
                """
                SELECT e.*, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
                FROM ejercicios e
                INNER JOIN temas t ON t.id_tema = e.id_tema
                INNER JOIN niveles_dificultad n ON n.id_nivel = e.id_nivel
                WHERE t.id_grado = %s
                  AND e.id_tema = %s
                  AND e.id_nivel = %s
                  AND e.estado = 'publicado'
                ORDER BY e.id_ejercicio ASC
                LIMIT 1
                """,
                (id_grado, id_tema, id_nivel),
            )
            ejercicio = cursor.fetchone()

        if not ejercicio:
            return None

        opciones = obtener_opciones_ejercicio(ejercicio["id_ejercicio"], cursor) if ejercicio["tipo_respuesta"] == "seleccion_multiple" else []
        return serializar_pregunta(ejercicio, opciones)
    finally:
        if cerrar:
            cursor.close()
            conexion.close()
