import json

from db import obtener_conexion
from generators.generador_ejercicios import construir_ejercicio_desde_plantilla


def _parse_json(valor):
    # Convierte JSON de MySQL a dict Python de forma tolerante.
    if isinstance(valor, dict):
        return valor
    if not valor:
        return {}
    return json.loads(valor)


def _serializar_plantilla(fila):
    # Prepara una plantilla para API y generador.
    if not fila:
        return None
    tipo_canonico = fila.get("tipo_respuesta_canonico") or fila["tipo_respuesta"]
    return {
        **fila,
        "tipo_respuesta": tipo_canonico,
        "configuracion_json": _parse_json(fila.get("configuracion_json")),
        "fecha_creacion": fila["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_creacion") else None,
        "fecha_modificacion": fila["fecha_modificacion"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_modificacion") else None,
    }


def serializar_pregunta_generada(ejercicio):
    # Devuelve la pregunta generada sin exponer respuesta, formula ni parametros.
    if not ejercicio:
        return None
    return {
        "id_ejercicio_generado": ejercicio["id_ejercicio_generado"],
        "id_plantilla": ejercicio["id_plantilla"],
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
        "opciones": [
            {"id_opcion": opcion.get("id"), "texto_opcion": opcion.get("texto"), "orden_visualizacion": indice + 1}
            for indice, opcion in enumerate(_parse_json(ejercicio.get("opciones_json")))
        ],
        "origen": "generado",
    }


def listar_plantillas(filtros=None):
    # Lista plantillas con filtros opcionales para la pantalla administrativa.
    filtros = filtros or {}
    condiciones = []
    parametros = []
    if filtros.get("id_grado"):
        condiciones.append("p.id_grado = %s")
        parametros.append(filtros["id_grado"])
    if filtros.get("id_tema"):
        condiciones.append("p.id_tema = %s")
        parametros.append(filtros["id_tema"])
    if filtros.get("estado"):
        condiciones.append("p.estado = %s")
        parametros.append(filtros["estado"])

    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT p.*, g.nombre_grado, t.nombre_tema, n.nombre AS nombre_nivel, n.codigo AS codigo_nivel
            FROM plantillas_ejercicios p
            INNER JOIN grados g ON g.id_grado = p.id_grado
            INNER JOIN temas t ON t.id_tema = p.id_tema
            INNER JOIN niveles_dificultad n ON n.id_nivel = p.id_nivel
            {where}
            ORDER BY g.orden_visualizacion ASC, t.nombre_tema ASC, n.orden_nivel ASC, p.nombre ASC
            """,
            tuple(parametros),
        )
        return [_serializar_plantilla(fila) for fila in cursor.fetchall()]
    finally:
        cursor.close()
        conexion.close()


def listar_niveles():
    # Devuelve niveles activos para formularios de plantillas.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id_nivel, codigo, nombre, orden_nivel
            FROM niveles_dificultad
            WHERE estado = 'activo'
            ORDER BY orden_nivel ASC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def _validar_datos_plantilla(datos):
    # Valida campos requeridos y que el JSON pueda generar un ejercicio valido.
    errores = {}
    try:
        id_grado = int(datos.get("id_grado"))
    except (TypeError, ValueError):
        id_grado = None
        errores["id_grado"] = "Seleccione un grado valido."
    try:
        id_tema = int(datos.get("id_tema"))
    except (TypeError, ValueError):
        id_tema = None
        errores["id_tema"] = "Seleccione un tema valido."
    try:
        id_nivel = int(datos.get("id_nivel"))
    except (TypeError, ValueError):
        id_nivel = None
        errores["id_nivel"] = "Seleccione un nivel valido."

    nombre = (datos.get("nombre") or "").strip()
    tipo_respuesta = (datos.get("tipo_respuesta") or "").strip()
    plantilla_enunciado = (datos.get("plantilla_enunciado") or "").strip()
    plantilla_explicacion = (datos.get("plantilla_explicacion") or "").strip()
    plantilla_pista = (datos.get("plantilla_pista") or "").strip()
    estado = (datos.get("estado") or "borrador").strip()
    configuracion = datos.get("configuracion_json")

    if isinstance(configuracion, str):
        try:
            configuracion = json.loads(configuracion)
        except json.JSONDecodeError:
            errores["configuracion_json"] = "JSON invalido."

    if not nombre:
        errores["nombre"] = "Ingrese un nombre."
    if tipo_respuesta not in ("seleccion_multiple", "numerica"):
        errores["tipo_respuesta"] = "Tipo de respuesta invalido."
    if estado not in ("borrador", "publicada", "desactivada"):
        errores["estado"] = "Estado invalido."
    if not plantilla_enunciado:
        errores["plantilla_enunciado"] = "Ingrese un enunciado."
    if not isinstance(configuracion, dict):
        errores["configuracion_json"] = "La configuracion debe ser JSON."

    datos_limpios = {
        "id_grado": id_grado,
        "id_tema": id_tema,
        "id_nivel": id_nivel,
        "nombre": nombre,
        "descripcion": (datos.get("descripcion") or "").strip(),
        "tipo_respuesta": tipo_respuesta,
        "plantilla_enunciado": plantilla_enunciado,
        "configuracion_json": configuracion,
        "plantilla_explicacion": plantilla_explicacion,
        "plantilla_pista": plantilla_pista,
        "estado": estado,
    }

    if not errores:
        try:
            construir_ejercicio_desde_plantilla({
                "id_plantilla": 0,
                "id_tema": id_tema,
                "id_nivel": id_nivel,
                **datos_limpios,
            })
        except ValueError as error:
            errores["configuracion_json"] = str(error)

    return datos_limpios, errores


def crear_plantilla(datos):
    # Crea una plantilla validando que pueda generar ejercicios correctos.
    datos_limpios, errores = _validar_datos_plantilla(datos)
    if errores:
        return "datos_invalidos", "Revise los datos de la plantilla.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO plantillas_ejercicios
                (id_grado, id_tema, id_nivel, nombre, descripcion, tipo_respuesta, plantilla_enunciado,
                 configuracion_json, plantilla_explicacion, plantilla_pista, estado, es_demo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                datos_limpios["id_grado"],
                datos_limpios["id_tema"],
                datos_limpios["id_nivel"],
                datos_limpios["nombre"],
                datos_limpios["descripcion"],
                datos_limpios["tipo_respuesta"],
                datos_limpios["plantilla_enunciado"],
                json.dumps(datos_limpios["configuracion_json"]),
                datos_limpios["plantilla_explicacion"],
                datos_limpios["plantilla_pista"],
                datos_limpios["estado"],
            ),
        )
        conexion.commit()
        return "creado", "Plantilla creada correctamente.", {"id_plantilla": cursor.lastrowid}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def actualizar_plantilla(id_plantilla, datos):
    # Actualiza una plantilla sin recalcular ejercicios historicos generados.
    datos_limpios, errores = _validar_datos_plantilla(datos)
    if errores:
        return "datos_invalidos", "Revise los datos de la plantilla.", None, errores

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE plantillas_ejercicios
            SET id_grado = %s,
                id_tema = %s,
                id_nivel = %s,
                nombre = %s,
                descripcion = %s,
                tipo_respuesta = %s,
                plantilla_enunciado = %s,
                configuracion_json = %s,
                plantilla_explicacion = %s,
                plantilla_pista = %s,
                estado = %s
            WHERE id_plantilla = %s
            """,
            (
                datos_limpios["id_grado"],
                datos_limpios["id_tema"],
                datos_limpios["id_nivel"],
                datos_limpios["nombre"],
                datos_limpios["descripcion"],
                datos_limpios["tipo_respuesta"],
                datos_limpios["plantilla_enunciado"],
                json.dumps(datos_limpios["configuracion_json"]),
                datos_limpios["plantilla_explicacion"],
                datos_limpios["plantilla_pista"],
                datos_limpios["estado"],
                id_plantilla,
            ),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "La plantilla solicitada no existe.", None, {}
        conexion.commit()
        return "actualizado", "Plantilla actualizada correctamente.", {"id_plantilla": id_plantilla}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def cambiar_estado_plantilla(id_plantilla, estado):
    # Activa, desactiva o deja en borrador una plantilla.
    if estado not in ("borrador", "publicada", "desactivada"):
        return "datos_invalidos", "Estado invalido.", None, {"estado": "Estado invalido."}
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE plantillas_ejercicios
            SET estado = %s
            WHERE id_plantilla = %s
            """,
            (estado, id_plantilla),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return "no_existe", "La plantilla solicitada no existe.", None, {}
        conexion.commit()
        return "actualizado", "Estado actualizado correctamente.", {"id_plantilla": id_plantilla, "estado": estado}, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_plantillas_publicadas(id_grado, id_tema, id_nivel, cursor):
    # Lista plantillas publicadas compatibles para intentar fallback entre moldes.
    cursor.execute(
        """
        SELECT p.*, t.tipo_respuesta AS tipo_respuesta_canonico
        FROM plantillas_ejercicios p
        INNER JOIN temas t ON t.id_tema = p.id_tema
        WHERE p.id_grado = %s
          AND p.id_tema = %s
          AND p.id_nivel = %s
          AND p.estado = 'publicada'
        ORDER BY p.es_demo ASC, p.id_plantilla DESC
        """,
        (id_grado, id_tema, id_nivel),
    )
    return [_serializar_plantilla(fila) for fila in cursor.fetchall()]


def obtener_plantilla_publicada(id_grado, id_tema, id_nivel, cursor):
    # Conserva compatibilidad devolviendo la primera plantilla publicada.
    plantillas = obtener_plantillas_publicadas(id_grado, id_tema, id_nivel, cursor)
    return plantillas[0] if plantillas else None


def _historial_parametros(id_partida, id_plantilla, cursor):
    # Carga parametros recientes para no repetir exactamente la combinacion.
    cursor.execute(
        """
        SELECT parametros_json
        FROM ejercicios_generados
        WHERE id_partida = %s
          AND id_plantilla = %s
        ORDER BY id_ejercicio_generado DESC
        LIMIT 8
        """,
        (id_partida, id_plantilla),
    )
    return [_parse_json(fila["parametros_json"]) for fila in cursor.fetchall()]


def obtener_ejercicio_generado(id_ejercicio_generado, cursor):
    # Obtiene un ejercicio generado con datos internos para validar respuesta.
    cursor.execute(
        """
        SELECT eg.*, n.codigo AS codigo_nivel, n.nombre AS nombre_nivel, n.orden_nivel
        FROM ejercicios_generados eg
        INNER JOIN niveles_dificultad n ON n.id_nivel = eg.id_nivel
        WHERE eg.id_ejercicio_generado = %s
          AND eg.estado_validacion = 'valido'
        """,
        (id_ejercicio_generado,),
    )
    return cursor.fetchone()


def generar_y_guardar_ejercicio(id_partida, id_grado, id_tema, id_nivel, cursor):
    # Genera solo desde plantillas del objetivo resuelto por el agente.
    plantillas = obtener_plantillas_publicadas(id_grado, id_tema, id_nivel, cursor)
    if not plantillas:
        return None

    generado = None
    for plantilla in plantillas:
        if (
            int(plantilla["id_grado"]) != int(id_grado)
            or int(plantilla["id_tema"]) != int(id_tema)
            or int(plantilla["id_nivel"]) != int(id_nivel)
        ):
            continue
        try:
            candidato = construir_ejercicio_desde_plantilla(
                plantilla,
                historial_parametros=_historial_parametros(id_partida, plantilla["id_plantilla"], cursor),
            )
            if int(candidato["id_tema"]) != int(id_tema) or int(candidato["id_nivel"]) != int(id_nivel):
                continue
            generado = candidato
            break
        except ValueError:
            continue
    if not generado:
        return None

    cursor.execute(
        """
        INSERT INTO ejercicios_generados
            (id_plantilla, id_partida, id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta,
             explicacion, explicacion_pasos, pista, opciones_json, parametros_json, semilla_generacion, estado_validacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'valido')
        """,
        (
            generado["id_plantilla"],
            id_partida,
            generado["id_tema"],
            generado["id_nivel"],
            generado["enunciado"],
            generado["tipo_respuesta"],
            generado["respuesta_correcta"],
            generado["explicacion"],
            json.dumps(generado["explicacion_pasos"]),
            generado["pista"],
            json.dumps(generado["opciones"]),
            json.dumps(generado["parametros"]),
            generado["semilla_generacion"],
        ),
    )
    return serializar_pregunta_generada(obtener_ejercicio_generado(cursor.lastrowid, cursor))


def probar_generacion(id_plantilla, cantidad=3):
    # Genera ejemplos temporales para admin sin guardarlos en la partida.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT p.*
            FROM plantillas_ejercicios p
            WHERE p.id_plantilla = %s
            """,
            (id_plantilla,),
        )
        plantilla = _serializar_plantilla(cursor.fetchone())
        if not plantilla:
            return "no_existe", "La plantilla solicitada no existe.", None, {}

        ejemplos = []
        historial = []
        for _ in range(max(1, min(int(cantidad), 10))):
            generado = construir_ejercicio_desde_plantilla(plantilla, historial)
            historial.append(generado["parametros"])
            ejemplos.append({
                "enunciado": generado["enunciado"],
                "respuesta_correcta": generado["respuesta_correcta"],
                "opciones": generado["opciones"],
                "parametros": generado["parametros"],
            })
        return "consultado", "Ejemplos generados correctamente.", ejemplos, {}
    finally:
        cursor.close()
        conexion.close()
