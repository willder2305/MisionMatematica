"""Orquesta partidas adaptativas, respuestas y progreso académico del juego.

El servicio conserva dos contextos aislados: el juego personal progresa por
tema desde Cuarto Fácil hasta Sexto Difícil, mientras que una actividad usa el
grado fijo de su asignación. Cada respuesta se procesa dentro de una
transacción para proteger vidas, progreso, decisiones del agente y monedas.
"""

import json
import random
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from mysql.connector import IntegrityError

from agent.motor_reglas import MotorReglasAdaptativo
from db import obtener_conexion
from services.asignaciones_service import (
    registrar_cierre_partida_asignada,
    registrar_inicio_asignacion_estudiante,
    validar_asignacion_estudiante,
)
from services.ejercicios_service import (
    obtener_ejercicio_publicado,
    obtener_explicacion_pasos_ejercicio,
    preparar_pregunta,
)
from services.plantillas_service import generar_y_guardar_ejercicio, obtener_ejercicio_generado, serializar_pregunta_generada
from services.progreso_service import (
    DEFINICIONES_TEMA_PERSONAL,
    actualizar_progreso_contextual,
    obtener_estado_asignacion,
    obtener_o_crear_estado_personal,
    listar_temas_personales,
    sincronizar_progreso_usuario,
)
from services.personalizacion_service import (
    COSTO_CONTINUACION,
    acreditar_recompensa_partida,
    bloquear_monedero_estudiante,
    obtener_saldo_en_cursor,
    registrar_movimiento_monedas,
    resolver_personalizacion_partida,
)


CASILLA_FINAL = 10
VIDAS_INICIALES = 5
# Compatibilidad para pruebas y partidas historicas; las partidas nuevas usan inventario persistente.
MAPAS_PERMITIDOS = ("bosque", "mapa_2", "mapa_3")

# Columnas que usa la serialización y la lógica de una partida. Evita SELECT *
# en la ruta consultada al iniciar, responder, continuar o recuperar una partida.
COLUMNAS_PARTIDA = """
    id_partida, id_usuario, id_asignacion, tipo_contexto, id_grado, id_tema,
    request_id, id_nivel_inicial, id_nivel_actual, id_ejercicio_actual,
    id_ejercicio_generado_actual, personaje, mapa, casilla_actual,
    total_correctos, total_errores, vidas_iniciales, vidas_restantes,
    vidas_perdidas_total, continuaciones_compradas, recompensa_otorgada,
    preguntas_respondidas, estado, motivo_finalizacion, fecha_inicio,
    fecha_fin, fecha_ultima_actividad
"""


# Convierte parametros JSON de MySQL a diccionarios Python.
def _parse_json(valor):
    if isinstance(valor, dict):
        return valor
    if not valor:
        return {}
    return json.loads(valor)


# Formatea fechas para responder JSON sin objetos datetime.
def _serializar_fecha(valor):
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


# Convierte una fila de partidas_juego al formato que usa React.
def serializar_partida(fila):
    if not fila:
        return None
    return {
        "id_partida": fila["id_partida"],
        "id_usuario": fila.get("id_usuario"),
        "id_asignacion": fila.get("id_asignacion"),
        "tipo_contexto": fila.get("tipo_contexto") or ("asignacion" if fila.get("id_asignacion") else "personal"),
        "id_grado": fila.get("id_grado"),
        "id_tema": fila.get("id_tema"),
        "id_nivel_inicial": fila.get("id_nivel_inicial"),
        "id_nivel_actual": fila.get("id_nivel_actual"),
        "id_ejercicio_actual": fila.get("id_ejercicio_actual"),
        "id_ejercicio_generado_actual": fila.get("id_ejercicio_generado_actual"),
        "personaje": fila["personaje"],
        "mapa": fila["mapa"],
        "casilla_actual": fila["casilla_actual"],
        "total_correctos": fila["total_correctos"],
        "total_errores": fila["total_errores"],
        "vidas_iniciales": fila.get("vidas_iniciales", VIDAS_INICIALES),
        "vidas_restantes": fila.get("vidas_restantes", VIDAS_INICIALES),
        "vidas_perdidas_total": fila.get("vidas_perdidas_total", 0),
        "continuaciones_compradas": fila.get("continuaciones_compradas", 0),
        "recompensa_otorgada": bool(fila.get("recompensa_otorgada", 0)),
        "preguntas_respondidas": fila.get("preguntas_respondidas", 0),
        "estado": fila["estado"],
        "motivo_finalizacion": fila.get("motivo_finalizacion"),
        "fecha_inicio": _serializar_fecha(fila.get("fecha_inicio")),
        "fecha_fin": _serializar_fecha(fila.get("fecha_fin")),
        "fecha_ultima_actividad": _serializar_fecha(fila.get("fecha_ultima_actividad")),
    }


def _obtener_partida(id_partida, cursor, bloquear=False):
    """Obtiene una partida con sus columnas necesarias y bloqueo opcional.

    El bloqueo se usa en mutaciones para impedir que dos respuestas, compras
    de continuación o recompensas actualicen el mismo estado simultáneamente.
    """
    cursor.execute(
        f"""
        SELECT {COLUMNAS_PARTIDA}
        FROM partidas_juego
        WHERE id_partida = %s
        {'FOR UPDATE' if bloquear else ''}
        """,
        (id_partida,),
    )
    return cursor.fetchone()


# Verifica que el grado y tema elegidos existan y esten activos.
def _obtener_grado_tema_activos(id_grado, id_tema, cursor):
    cursor.execute(
        """
        SELECT g.id_grado, t.id_tema
        FROM grados g
        INNER JOIN temas t ON t.id_grado = g.id_grado
        WHERE g.id_grado = %s
          AND t.id_tema = %s
          AND g.estado = 'activo'
          AND t.estado = 'activo'
        """,
        (id_grado, id_tema),
    )
    return cursor.fetchone()


# Obtiene el perfil del estudiante para validar el contexto academico del juego.
def _obtener_perfil_estudiante(id_usuario, cursor):
    cursor.execute(
        """
        SELECT id_usuario, id_grado, modalidad, personaje, id_institucion_grado, id_seccion
        FROM perfiles_estudiante
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )
    return cursor.fetchone()


def _validar_grado_estudiante(id_usuario, id_grado, cursor):
    # Compatibilidad interna: valida grado de perfil sin autorizar grado manual de inicio.
    perfil = _obtener_perfil_estudiante(id_usuario, cursor)
    if not perfil:
        return False, "Complete el onboarding antes de iniciar el juego.", {"onboarding": "Perfil de estudiante requerido."}

    if perfil["modalidad"] == "cuenta_propia":
        if perfil.get("id_grado") is not None and int(perfil["id_grado"]) == id_grado:
            return True, "", {}
        return False, "El grado no corresponde al perfil del estudiante.", {"id_grado": "Grado fuera del perfil."}

    if perfil["modalidad"] == "grupo_educativo":
        cursor.execute(
            """
            SELECT pe.id_perfil_estudiante
            FROM perfiles_estudiante pe
            INNER JOIN institucion_grados ig
                ON ig.id_institucion_grado = pe.id_institucion_grado
            INNER JOIN secciones s
                ON s.id_seccion = pe.id_seccion
               AND s.id_institucion_grado = pe.id_institucion_grado
            WHERE pe.id_usuario = %s
              AND pe.modalidad = 'grupo_educativo'
              AND ig.estado = 'activo'
              AND s.estado = 'activo'
              AND ig.id_grado_base = %s
            LIMIT 1
            """,
            (id_usuario, id_grado),
        )
        if cursor.fetchone():
            return True, "", {}
        return False, "El grado no pertenece al perfil institucional activo.", {"id_grado": "Grado fuera del perfil institucional."}

    return False, "La modalidad del estudiante no permite iniciar el juego.", {"modalidad": "Modalidad invalida."}


# Obtiene el nivel inicial configurado para comenzar una partida.
def _obtener_nivel_inicial(cursor):
    cursor.execute(
        """
        SELECT id_nivel, codigo, nombre, orden_nivel
        FROM niveles_dificultad
        WHERE estado = 'activo'
        ORDER BY es_inicial DESC, orden_nivel ASC
        LIMIT 1
        """
    )
    return cursor.fetchone()


def _obtener_grado_cuarto(cursor):
    # Resuelve Cuarto como grado curricular inicial para cuenta propia.
    cursor.execute(
        """
        SELECT id_grado
        FROM grados
        WHERE codigo_grado = '4P'
          AND estado = 'activo'
        LIMIT 1
        """
    )
    fila = cursor.fetchone()
    return fila["id_grado"] if fila else None


def _obtener_tema_por_id(id_tema, cursor):
    # Consulta tema activo con grado para usar el nombre como llave curricular.
    cursor.execute(
        """
        SELECT t.id_tema, t.id_grado, t.nombre_tema, g.nombre_grado, g.orden_visualizacion
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


def _obtener_tema_por_nombre_grado(nombre_tema, id_grado, cursor):
    # Busca el tema equivalente dentro del grado curricular resuelto.
    cursor.execute(
        """
        SELECT t.id_tema, t.id_grado, t.nombre_tema, g.nombre_grado, g.orden_visualizacion
        FROM temas t
        INNER JOIN grados g ON g.id_grado = t.id_grado
        WHERE t.nombre_tema = %s
          AND t.id_grado = %s
          AND t.estado = 'activo'
          AND g.estado = 'activo'
        LIMIT 1
        """,
        (nombre_tema, id_grado),
    )
    return cursor.fetchone()


def _obtener_nivel_desde_progreso(id_usuario, id_tema, cursor):
    # Usa dificultad por tema si ya existe; si no, arranca en el nivel inicial activo.
    cursor.execute(
        """
        SELECT pte.id_nivel_actual
        FROM progreso_tema_estudiante pte
        INNER JOIN niveles_dificultad n ON n.id_nivel = pte.id_nivel_actual
        WHERE pte.id_usuario = %s
          AND pte.id_tema = %s
          AND n.estado = 'activo'
        LIMIT 1
        """,
        (id_usuario, id_tema),
    )
    fila = cursor.fetchone()
    if fila and fila.get("id_nivel_actual"):
        return _obtener_nivel_por_id(fila["id_nivel_actual"], cursor)
    return _obtener_nivel_inicial(cursor)


def _obtener_nivel_asignacion_o_progreso(id_usuario, id_tema, asignacion, cursor):
    # Para actividades usa progreso del estudiante y recurre al nivel inicial de la asignacion.
    nivel = _obtener_nivel_desde_progreso(id_usuario, id_tema, cursor)
    if nivel:
        return nivel
    if asignacion and asignacion.get("id_nivel_inicial"):
        return _obtener_nivel_por_id(asignacion["id_nivel_inicial"], cursor)
    return _obtener_nivel_inicial(cursor)


def _primer_tema_asignacion(id_asignacion, cursor):
    # Permite iniciar una actividad sin que el estudiante seleccione tema manualmente.
    cursor.execute(
        """
        SELECT t.id_tema
        FROM asignacion_temas at
        INNER JOIN asignaciones a ON a.id_asignacion = at.id_asignacion
        INNER JOIN institucion_grados ig ON ig.id_institucion_grado = a.id_institucion_grado
        INNER JOIN temas t ON t.id_tema = at.id_tema
        WHERE at.id_asignacion = %s
          AND at.estado = 'activo'
          AND t.estado = 'activo'
          AND t.id_grado = ig.id_grado_base
        ORDER BY t.nombre_tema ASC, t.id_tema ASC
        LIMIT 1
        """,
        (id_asignacion,),
    )
    fila = cursor.fetchone()
    return fila["id_tema"] if fila else None


def _grado_curricular_independiente(id_usuario, nombre_tema, perfil, cursor):
    # Determina el grado curricular interno del tema sin aceptar grado desde el cliente.
    cursor.execute(
        """
        SELECT pct.id_grado_nuevo AS id_grado
        FROM promociones_curriculares_tema pct
        INNER JOIN temas tn ON tn.id_tema = pct.id_tema_nuevo
        WHERE pct.id_usuario = %s
          AND tn.nombre_tema = %s
        ORDER BY pct.fecha_promocion DESC, pct.id_promocion DESC
        LIMIT 1
        """,
        (id_usuario, nombre_tema),
    )
    fila = cursor.fetchone()
    if fila and fila.get("id_grado"):
        return fila["id_grado"]
    cursor.execute(
        """
        SELECT COALESCE(pte.id_grado_curricular_actual, t.id_grado) AS id_grado
        FROM progreso_tema_estudiante pte
        INNER JOIN temas t ON t.id_tema = pte.id_tema
        INNER JOIN grados g ON g.id_grado = COALESCE(pte.id_grado_curricular_actual, t.id_grado)
        WHERE pte.id_usuario = %s
          AND t.nombre_tema = %s
        ORDER BY g.orden_visualizacion DESC, pte.fecha_modificacion DESC, pte.id_progreso_tema_estudiante DESC
        LIMIT 1
        """,
        (id_usuario, nombre_tema),
    )
    fila = cursor.fetchone()
    if fila and fila.get("id_grado"):
        return fila["id_grado"]
    return perfil.get("id_grado") or _obtener_grado_cuarto(cursor)


def _tema_visible_registrado(id_usuario, id_tema, nombre_tema, perfil, cursor):
    # Resuelve el tema visible desde el grado registrado, nunca desde el nivel adaptativo.
    id_grado_base = perfil.get("id_grado") or _obtener_grado_cuarto(cursor)
    if id_tema:
        cursor.execute(
            """
            SELECT t.id_tema, t.id_grado, t.nombre_tema
            FROM temas t
            WHERE t.id_tema = %s
              AND t.id_grado = %s
              AND t.estado = 'activo'
            LIMIT 1
            """,
            (id_tema, id_grado_base),
        )
        tema = cursor.fetchone()
        if tema:
            return tema
        return None
    if nombre_tema:
        return _obtener_tema_por_nombre_grado(nombre_tema, id_grado_base, cursor)
    return None


def _resolver_contexto_juego(datos_limpios, cursor):
    # Centraliza el contexto para que React no pueda imponer grado ni dificultad.
    perfil = _obtener_perfil_estudiante(datos_limpios["id_usuario"], cursor)
    if not perfil:
        return None, "no_autorizado", "Complete el onboarding antes de iniciar el juego.", {
            "onboarding": "Perfil de estudiante requerido."
        }

    if datos_limpios["id_asignacion"]:
        id_tema = datos_limpios["id_tema"] or _primer_tema_asignacion(datos_limpios["id_asignacion"], cursor)
        if not id_tema:
            return None, "datos_invalidos", "La asignación no tiene temas activos.", {"id_tema": "Tema requerido."}
        asignacion_ok, mensaje, asignacion, errores = validar_asignacion_estudiante(
            datos_limpios["id_usuario"],
            datos_limpios["id_asignacion"],
            id_tema,
            cursor,
        )
        if not asignacion_ok:
            return None, "no_autorizado", mensaje, errores
        estado_asignacion = obtener_estado_asignacion(
            datos_limpios["id_usuario"], datos_limpios["id_asignacion"], id_tema, asignacion["id_grado"], cursor
        )
        return {
            "id_grado": asignacion["id_grado"],
            "id_tema": id_tema,
            "nivel": _obtener_nivel_por_id(estado_asignacion["id_nivel_actual"], cursor),
            "perfil": perfil,
            "asignacion": asignacion,
            "tipo_contexto": "asignacion",
        }, None, None, None

    if not datos_limpios["id_tema"]:
        return None, "datos_invalidos", "Seleccione un tema disponible.", {"id_tema": "Tema requerido."}
    estado_personal = obtener_o_crear_estado_personal(datos_limpios["id_usuario"], datos_limpios["id_tema"], cursor)
    if not estado_personal:
        return None, "no_autorizado", "El tema todavía no está disponible en tu aventura.", {"id_tema": "Tema bloqueado."}
    return {
        "id_grado": estado_personal["id_grado_curricular"],
        "id_tema": estado_personal["id_tema_actual"],
        "nivel": _obtener_nivel_por_id(estado_personal["id_nivel_actual"], cursor),
        "perfil": perfil,
        "asignacion": None,
        "tipo_contexto": "personal",
    }, None, None, None


def _serializar_tema_contexto(fila):
    # Entrega temas sin exponer dificultad ni controles de grado.
    definicion = DEFINICIONES_TEMA_PERSONAL.get(fila["nombre_tema"], {})
    return {
        "id_tema": fila["id_tema"],
        "nombre_tema": definicion.get("nombre_visible", fila["nombre_tema"]),
        "tema_nombre": definicion.get("nombre_visible", fila["nombre_tema"]),
        "categoria": definicion.get("categoria"),
    }


def _listar_temas_grado(id_grado, cursor):
    cursor.execute(
        """
        SELECT id_tema, nombre_tema
        FROM temas
        WHERE id_grado = %s
          AND estado = 'activo'
        ORDER BY nombre_tema ASC
        """,
        (id_grado,),
    )
    return [_serializar_tema_contexto(fila) for fila in cursor.fetchall()]


def obtener_contexto_juego_estudiante(usuario):
    # Devuelve modalidad y temas permitidos; grado y dificultad quedan internos al backend.
    if usuario["rol"] != "estudiante":
        return "no_autorizado", "Solo estudiantes pueden consultar contexto de juego.", None, {}
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        perfil = _obtener_perfil_estudiante(usuario["id_usuario"], cursor)
        if not perfil:
            return "no_autorizado", "Complete el onboarding antes de iniciar el juego.", None, {}
        temas = [_serializar_tema_contexto(fila) for fila in listar_temas_personales(usuario["id_usuario"], cursor)]
        conexion.commit()
        return "consultado", "Contexto de juego consultado correctamente.", {
            "modalidad": perfil["modalidad"],
            "requiere_tema": True,
            "temas": temas,
        }, {}
    finally:
        cursor.close()
        conexion.close()


# Busca el nivel actual por id para entregarlo al motor de reglas.
def _obtener_nivel_por_id(id_nivel, cursor):
    cursor.execute(
        """
        SELECT id_nivel, codigo, nombre, orden_nivel
        FROM niveles_dificultad
        WHERE id_nivel = %s
          AND estado = 'activo'
        """,
        (id_nivel,),
    )
    return cursor.fetchone()


# Carga todos los niveles activos ordenados para subir o bajar dificultad.
def _obtener_niveles(cursor):
    cursor.execute(
        """
        SELECT id_nivel, codigo, nombre, orden_nivel
        FROM niveles_dificultad
        WHERE estado = 'activo'
        ORDER BY orden_nivel ASC
        """
    )
    return cursor.fetchall()


# Carga las reglas activas desde la base y parsea sus parametros JSON.
def _obtener_reglas(cursor):
    cursor.execute(
        """
        SELECT codigo_regla, prioridad, parametros_json, accion
        FROM reglas_adaptativas
        WHERE estado = 'activo'
        ORDER BY prioridad ASC
        """
    )
    reglas = []
    for regla in cursor.fetchall():
        reglas.append({**regla, "parametros_json": _parse_json(regla.get("parametros_json"))})
    return reglas


# Valida el contexto academico de inicio; personaje y mapa vienen de preferencias seguras.
def _validar_inicio(datos):
    errores = {}
    id_usuario = datos.get("id_usuario_autenticado")

    try:
        id_tema = int(datos.get("id_tema")) if datos.get("id_tema") not in (None, "") else None
    except (TypeError, ValueError):
        id_tema = None
        errores["id_tema"] = "Seleccione un tema valido."

    try:
        id_asignacion = int(datos.get("id_asignacion")) if datos.get("id_asignacion") else None
    except (TypeError, ValueError):
        id_asignacion = None
        errores["id_asignacion"] = "Asignacion invalida."

    request_id = (datos.get("request_id") or "").strip()
    if request_id and len(request_id) > 80:
        errores["request_id"] = "Identificador de solicitud demasiado largo."

    return {
        "id_tema": id_tema,
        "tema_nombre": (datos.get("tema_nombre") or "").strip(),
        "id_usuario": id_usuario,
        "id_asignacion": id_asignacion,
        "request_id": request_id or None,
    }, errores


def _obtener_pregunta_actual_partida(partida, cursor):
    # Reconstruye la pregunta visible de una partida ya creada sin exponer la respuesta.
    if not partida:
        return None
    if partida.get("id_ejercicio_generado_actual"):
        return serializar_pregunta_generada(
            obtener_ejercicio_generado(partida["id_ejercicio_generado_actual"], cursor)
        )
    if partida.get("id_ejercicio_actual"):
        return preparar_pregunta(partida["id_ejercicio_actual"], cursor)
    return None


def _obtener_partida_por_request_id(id_usuario, request_id, cursor):
    """Busca el inicio idempotente de una partida sin leer columnas ajenas al flujo."""
    if not request_id:
        return None
    cursor.execute(
        f"""
        SELECT {COLUMNAS_PARTIDA}
        FROM partidas_juego
        WHERE id_usuario = %s
          AND request_id = %s
        LIMIT 1
        """,
        (id_usuario, request_id),
    )
    return cursor.fetchone()


def seleccionar_mapa_nueva_partida(id_usuario, id_asignacion, cursor, mapas_disponibles=MAPAS_PERMITIDOS):
    """Compatibilidad de rotacion para el catalogo base; el flujo nuevo usa preferencias seguras."""
    cursor.execute(
        "SELECT mapa FROM partidas_juego WHERE id_usuario = %s AND id_asignacion = %s ORDER BY id_partida DESC LIMIT 1",
        (id_usuario, id_asignacion),
    )
    ultimo = cursor.fetchone() or {}
    mapas = tuple(mapas_disponibles)
    candidatos = [mapa for mapa in mapas if mapa != ultimo.get("mapa")] if len(mapas) > 1 else list(mapas)
    return random.choice(candidatos or list(mapas))


def iniciar_partida_adaptativa(datos):
    """Crea o recupera una partida idempotente y genera su primera pregunta.

    El contexto personal se resuelve en el backend con progreso por tema. Si
    existe una asignación, conserva su grado y nunca consume progreso personal.
    La personalización también se obtiene del inventario persistente, no del
    cliente, antes de crear el registro de partida.
    """
    datos_limpios, errores = _validar_inicio(datos)
    if errores:
        return "datos_invalidos", "Revise los datos para iniciar la partida.", None, errores
    if not datos_limpios["id_usuario"]:
        return "no_autorizado", "Autenticación requerida para iniciar una partida.", None, {}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        partida_existente = _obtener_partida_por_request_id(
            datos_limpios["id_usuario"],
            datos_limpios["request_id"],
            cursor,
        )
        if partida_existente:
            return "consultado", "Partida ya iniciada para esta solicitud.", {
                "partida": serializar_partida(partida_existente),
                "pregunta_actual": _obtener_pregunta_actual_partida(partida_existente, cursor),
            }, {}

        contexto, codigo_contexto, mensaje_contexto, errores_contexto = _resolver_contexto_juego(datos_limpios, cursor)
        if not contexto:
            return codigo_contexto, mensaje_contexto, None, errores_contexto
        if not _obtener_grado_tema_activos(contexto["id_grado"], contexto["id_tema"], cursor):
            return "datos_invalidos", "El tema no está disponible para el contexto académico actual.", None, {"id_tema": "Tema no disponible."}

        nivel_inicial = contexto["nivel"]
        if not nivel_inicial:
            return "datos_invalidos", "No existen niveles de dificultad activos.", None, {}

        personaje_partida, mapa_partida = resolver_personalizacion_partida(datos_limpios["id_usuario"], cursor)

        cursor.execute(
            """
            INSERT INTO partidas_juego
                (id_usuario, id_asignacion, tipo_contexto, id_grado, id_tema, request_id, id_nivel_inicial, id_nivel_actual, id_ejercicio_actual,
                 id_ejercicio_generado_actual, personaje, mapa, casilla_actual, total_correctos, total_errores, vidas_iniciales,
                 vidas_restantes, preguntas_respondidas, estado, fecha_ultima_actividad)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, %s, %s, 0, 0, 0, %s, %s, 0, 'en_curso', CURRENT_TIMESTAMP)
            """,
            (
                datos_limpios["id_usuario"],
                datos_limpios["id_asignacion"],
                contexto["tipo_contexto"],
                contexto["id_grado"],
                contexto["id_tema"],
                datos_limpios["request_id"],
                nivel_inicial["id_nivel"],
                nivel_inicial["id_nivel"],
                personaje_partida,
                mapa_partida,
                VIDAS_INICIALES,
                VIDAS_INICIALES,
            ),
        )
        id_partida = cursor.lastrowid
        registrar_inicio_asignacion_estudiante(
            datos_limpios["id_asignacion"],
            datos_limpios["id_usuario"],
            id_partida,
            cursor,
        )
        pregunta = generar_y_guardar_ejercicio(
            id_partida,
            contexto["id_grado"],
            contexto["id_tema"],
            nivel_inicial["id_nivel"],
            cursor,
        )
        if not pregunta:
            conexion.rollback()
            return "configuracion_incompleta", "No existe una plantilla procedimental válida para el objetivo académico resuelto.", None, {}

        cursor.execute(
            """
            UPDATE partidas_juego
            SET id_ejercicio_actual = %s,
                id_ejercicio_generado_actual = %s
            WHERE id_partida = %s
            """,
            (
                None,
                pregunta.get("id_ejercicio_generado"),
                id_partida,
            ),
        )
        conexion.commit()

        partida = obtener_partida_adaptativa(id_partida)
        return "creado", "Partida iniciada correctamente.", {"partida": partida, "pregunta_actual": pregunta}, {}
    except IntegrityError as error:
        conexion.rollback()
        if getattr(error, "errno", None) == 1062 and datos_limpios.get("request_id"):
            partida_existente = _obtener_partida_por_request_id(
                datos_limpios["id_usuario"],
                datos_limpios["request_id"],
                cursor,
            )
            if partida_existente:
                return "consultado", "Partida ya iniciada para esta solicitud.", {
                    "partida": serializar_partida(partida_existente),
                    "pregunta_actual": _obtener_pregunta_actual_partida(partida_existente, cursor),
                }, {}
            return "estado_incompatible", "La solicitud de inicio ya fue utilizada.", None, {"request_id": "Identificador duplicado."}
        raise
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def obtener_partida_adaptativa(id_partida):
    """Devuelve el estado serializado de una partida para el propietario autorizado."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        return serializar_partida(_obtener_partida(id_partida, cursor))
    finally:
        cursor.close()
        conexion.close()


# Normaliza texto/numeros para comparar respuestas sin depender de mayusculas.
def _normalizar_respuesta(valor):
    return str(valor).strip().lower()


def _parse_fraccion_o_decimal(valor):
    # Interpreta formatos numericos comunes del estudiante sin evaluar codigo.
    texto = _normalizar_respuesta(valor).replace(",", ".")
    if " " in texto and "/" in texto:
        entero, fraccion = texto.split(" ", 1)
        signo = -1 if entero.startswith("-") else 1
        return Fraction(int(entero), 1) + signo * Fraction(fraccion)
    if "/" in texto:
        return Fraction(texto)
    return Decimal(texto)


def _requiere_forma_simplificada(ejercicio):
    # Lee metadata del ejercicio generado para exigir forma exacta cuando aplique.
    parametros = _parse_json(ejercicio.get("parametros_json")) if ejercicio.get("parametros_json") else {}
    return bool(parametros.get("forma_simplificada_requerida"))


# Compara la respuesta del estudiante contra la respuesta guardada en BD.
def _evaluar_respuesta(ejercicio, respuesta):
    enviada = _normalizar_respuesta(respuesta)
    correcta = _normalizar_respuesta(ejercicio["respuesta_correcta"])
    if _requiere_forma_simplificada(ejercicio) and "/" in correcta:
        return enviada.replace(" ", "") == correcta.replace(" ", "")
    if enviada == correcta:
        return True
    try:
        return _parse_fraccion_o_decimal(enviada) == _parse_fraccion_o_decimal(correcta)
    except (ValueError, InvalidOperation, ZeroDivisionError):
        return False


# Calcula metricas historicas que el agente usa para decidir dificultad.
def _obtener_metricas(partida, cursor):
    """Obtiene una ventana por estudiante, tema, contexto, grado y dificultad.

    Las actividades mantienen su propio historial y el juego personal no mezcla
    resultados de otros temas ni grados curriculares.
    """
    cursor.execute(
        """
        SELECT i.id_intento, i.es_correcta, i.tiempo_respuesta_ms
        FROM intentos_juego i
        INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
        WHERE p.id_usuario = %s
          AND p.tipo_contexto = %s
          AND p.id_grado = %s
          AND p.id_tema = %s
          AND i.nivel_al_responder = %s
        ORDER BY i.id_intento DESC
        LIMIT 8
        """,
        (
            partida["id_usuario"], partida.get("tipo_contexto") or "personal", partida["id_grado"],
            partida["id_tema"], partida["id_nivel_actual"],
        ),
    )
    intentos = cursor.fetchall()
    intentos.reverse()
    total = len(intentos)
    aciertos = sum(1 for intento in intentos if intento["es_correcta"])
    errores = total - aciertos
    porcentaje = round((aciertos / total) * 100, 2) if total else 0
    promedio = round(sum(intento["tiempo_respuesta_ms"] for intento in intentos) / total) if total else 0

    correctas_consecutivas = 0
    incorrectas_consecutivas = 0
    for intento in reversed(intentos):
        if intento["es_correcta"] and incorrectas_consecutivas == 0:
            correctas_consecutivas += 1
        elif not intento["es_correcta"] and correctas_consecutivas == 0:
            incorrectas_consecutivas += 1
        else:
            break

    ultimos_cinco = intentos[-5:]
    errores_ultimas_cinco = sum(1 for intento in ultimos_cinco if not intento["es_correcta"])
    cursor.execute(
        """
        SELECT MAX(d.id_intento) AS ultimo_cambio
        FROM decisiones_agente d
        INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
        WHERE p.id_usuario = %s AND p.tipo_contexto = %s AND p.id_grado = %s
          AND d.id_tema = %s AND d.accion IN ('aumentar', 'reducir')
        """,
        (partida["id_usuario"], partida.get("tipo_contexto") or "personal", partida["id_grado"], partida["id_tema"]),
    )
    ultimo_cambio = (cursor.fetchone() or {}).get("ultimo_cambio")
    preguntas_desde_ultimo_cambio = total if not ultimo_cambio else sum(
        1 for intento in intentos if int(intento["id_intento"]) > int(ultimo_cambio)
    )

    return {
        "total_intentos": total,
        "total_aciertos": aciertos,
        "total_errores": errores,
        "porcentaje_aciertos": porcentaje,
        "correctas_consecutivas": correctas_consecutivas,
        "incorrectas_consecutivas": incorrectas_consecutivas,
        "errores_ultimas_cinco": errores_ultimas_cinco,
        "preguntas_desde_ultimo_cambio": preguntas_desde_ultimo_cambio,
        "tiempo_promedio_ms": promedio,
        "decisiones_recientes": [],
    }


# Valida payload de respuesta enviado desde React.
def _validar_respuesta(datos):
    errores = {}
    request_id = (datos.get("request_id") or "").strip()
    respuesta = datos.get("respuesta")

    try:
        id_ejercicio = int(datos.get("id_ejercicio")) if datos.get("id_ejercicio") is not None else None
    except (TypeError, ValueError):
        id_ejercicio = None

    try:
        id_ejercicio_generado = int(datos.get("id_ejercicio_generado")) if datos.get("id_ejercicio_generado") is not None else None
    except (TypeError, ValueError):
        id_ejercicio_generado = None

    if not id_ejercicio and not id_ejercicio_generado:
        errores["id_ejercicio"] = "Ejercicio invalido."

    try:
        tiempo = max(0, int(datos.get("tiempo_respuesta_ms", 0)))
    except (TypeError, ValueError):
        tiempo = 0

    if respuesta is None or str(respuesta).strip() == "":
        errores["respuesta"] = "Ingrese una respuesta."
    if not request_id:
        errores["request_id"] = "request_id es obligatorio."

    return {
        "id_ejercicio": id_ejercicio,
        "id_ejercicio_generado": id_ejercicio_generado,
        "respuesta": respuesta,
        "request_id": request_id,
        "tiempo": tiempo,
    }, errores


# Devuelve una respuesta segura si llega dos veces el mismo request_id.
def _respuesta_idempotente(id_partida, request_id, cursor):
    cursor.execute(
        """
        SELECT i.*, COALESCE(e.enunciado, eg.enunciado) AS enunciado,
               COALESCE(e.explicacion, eg.explicacion) AS explicacion,
               COALESCE(e.explicacion_pasos, eg.explicacion_pasos) AS explicacion_pasos,
               COALESCE(e.respuesta_correcta, eg.respuesta_correcta) AS respuesta_correcta
        FROM intentos_juego i
        LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
        LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
        WHERE i.request_id = %s
        """,
        (request_id,),
    )
    intento = cursor.fetchone()
    if not intento:
        return None
    if intento["id_partida"] != id_partida:
        return {
            "codigo": "datos_invalidos",
            "mensaje": "request_id ya fue utilizado en otra partida.",
            "data": None,
            "errors": {"request_id": "Identificador duplicado."},
        }

    partida_actual = serializar_partida(_obtener_partida(id_partida, cursor))
    siguiente_pregunta = None
    if partida_actual and partida_actual["estado"] == "en_curso" and partida_actual.get("id_ejercicio_generado_actual"):
        siguiente_pregunta = serializar_pregunta_generada(
            obtener_ejercicio_generado(partida_actual["id_ejercicio_generado_actual"], cursor)
        )
    elif partida_actual and partida_actual["estado"] == "en_curso" and partida_actual.get("id_ejercicio_actual"):
        siguiente_pregunta = preparar_pregunta(partida_actual["id_ejercicio_actual"], cursor)

    cursor.execute(
        """
        SELECT d.*, na.codigo AS codigo_anterior, na.nombre AS nombre_anterior, na.orden_nivel AS orden_anterior,
               nn.codigo AS codigo_nuevo, nn.nombre AS nombre_nuevo, nn.orden_nivel AS orden_nuevo
        FROM decisiones_agente d
        INNER JOIN niveles_dificultad na ON na.id_nivel = d.nivel_anterior
        INNER JOIN niveles_dificultad nn ON nn.id_nivel = d.nivel_nuevo
        WHERE d.id_intento = %s
        ORDER BY d.id_decision DESC
        LIMIT 1
        """,
        (intento["id_intento"],),
    )
    decision = cursor.fetchone()
    agente = None
    if decision:
        agente = {
            "accion": decision["accion"],
            "regla_aplicada": decision["regla_aplicada"],
            "mensaje": "Respuesta ya registrada.",
            "motivo": decision["motivo"],
            "recomendar_refuerzo": decision["accion"] == "reforzar",
            "nivel_anterior": {
                "id_nivel": decision["nivel_anterior"],
                "codigo": decision["codigo_anterior"],
                "nombre": decision["nombre_anterior"],
                "orden_nivel": decision["orden_anterior"],
            },
            "nivel_nuevo": {
                "id_nivel": decision["nivel_nuevo"],
                "codigo": decision["codigo_nuevo"],
                "nombre": decision["nombre_nuevo"],
                "orden_nivel": decision["orden_nuevo"],
            },
            "metricas": {},
        }

    return {
        "codigo": "consultado",
        "mensaje": "La respuesta ya habia sido registrada.",
        "data": {
            "resultado": {
                "correcta": bool(intento["es_correcta"]),
                "respuesta_correcta": None if intento["es_correcta"] else intento.get("respuesta_correcta"),
                "explicacion_pasos": obtener_explicacion_pasos_ejercicio(intento) if not intento["es_correcta"] else None,
            },
            "partida": partida_actual,
            "agente": agente,
            "siguiente_pregunta": siguiente_pregunta,
            "animacion": "avance" if intento["es_correcta"] else "error",
        },
        "errors": {},
    }


def _generar_siguiente_pregunta_partida(partida, id_nivel, cursor):
    """Crea una pregunta procedimental para el objetivo académico ya resuelto."""
    return generar_y_guardar_ejercicio(
        partida["id_partida"],
        partida["id_grado"],
        partida["id_tema"],
        id_nivel,
        cursor,
    )


def continuar_partida_adaptativa(id_partida, datos, id_usuario_autenticado):
    """Resta una moneda una sola vez y reactiva la misma partida desde su casilla actual."""
    request_id = str((datos or {}).get("request_id") or "").strip()
    if not request_id or len(request_id) > 80:
        return "datos_invalidos", "La solicitud de continuación no es válida.", None, {"request_id": "Identificador requerido."}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        partida = _obtener_partida(id_partida, cursor, bloquear=True)
        if not partida:
            return "no_existe", "La partida solicitada no existe.", None, {}
        if partida.get("id_usuario") != id_usuario_autenticado:
            return "no_autorizado", "No puede continuar una partida de otro estudiante.", None, {}

        cursor.execute(
            """
            SELECT id_movimiento FROM movimientos_monedas
            WHERE request_id = %s AND tipo = 'continuar_partida'
            LIMIT 1
            """,
            (request_id,),
        )
        if cursor.fetchone():
            saldo = obtener_saldo_en_cursor(id_usuario_autenticado, cursor)
            conexion.commit()
            return "consultado", "La continuación ya había sido registrada.", {
                "partida": serializar_partida(partida),
                "pregunta_actual": _obtener_pregunta_actual_partida(partida, cursor),
                "saldo_monedas": saldo,
            }, {}

        if partida["estado"] != "sin_vidas" or int(partida.get("vidas_restantes") or 0) != 0:
            return "estado_incompatible", "Esta partida no necesita una continuación.", None, {}

        monedero = bloquear_monedero_estudiante(id_usuario_autenticado, cursor)
        saldo_anterior = int(monedero["saldo_monedas"])
        if saldo_anterior < COSTO_CONTINUACION:
            conexion.rollback()
            return "saldo_insuficiente", "No tienes monedas suficientes para continuar.", None, {"saldo": "Necesitas 1 moneda."}

        saldo_nuevo = saldo_anterior - COSTO_CONTINUACION
        cursor.execute(
            "UPDATE monederos SET saldo_monedas = %s WHERE id_usuario = %s",
            (saldo_nuevo, id_usuario_autenticado),
        )
        registrar_movimiento_monedas(
            cursor,
            id_usuario=id_usuario_autenticado,
            id_partida=id_partida,
            tipo="continuar_partida",
            cantidad=-COSTO_CONTINUACION,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            referencia=f"continuar:partida:{id_partida}:{request_id}",
            descripcion="Continuacion de partida despues de quedarse sin vidas.",
            request_id=request_id,
        )

        pregunta = _generar_siguiente_pregunta_partida(partida, partida["id_nivel_actual"], cursor)
        if not pregunta:
            conexion.rollback()
            return "configuracion_incompleta", "No existe una pregunta disponible para continuar.", None, {}

        cursor.execute(
            """
            UPDATE partidas_juego
            SET vidas_restantes = %s,
                continuaciones_compradas = continuaciones_compradas + 1,
                id_ejercicio_actual = %s,
                id_ejercicio_generado_actual = %s,
                estado = 'en_curso',
                motivo_finalizacion = NULL,
                fecha_fin = NULL,
                fecha_ultima_actividad = CURRENT_TIMESTAMP
            WHERE id_partida = %s
            """,
            (
                VIDAS_INICIALES,
                pregunta.get("id_ejercicio"),
                pregunta.get("id_ejercicio_generado"),
                id_partida,
            ),
        )
        conexion.commit()
        partida_actualizada = obtener_partida_adaptativa(id_partida)
        return "actualizado", "Puedes continuar tu aventura.", {
            "partida": partida_actualizada,
            "pregunta_actual": pregunta,
            "saldo_monedas": saldo_nuevo,
        }, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def responder_partida_adaptativa(id_partida, datos, id_usuario_autenticado):
    """Procesa una única respuesta y devuelve el siguiente estado de juego.

    Valida propiedad, pregunta e idempotencia; después registra el intento,
    resta una vida o avanza una casilla, consulta al agente y genera el próximo
    ejercicio. La recompensa normal es +1 moneda y la perfecta es +2 total;
    ambas se acreditan una sola vez dentro de esta misma transacción.
    """
    datos_limpios, errores = _validar_respuesta(datos)
    if errores:
        return "datos_invalidos", "Revise la respuesta enviada.", None, errores
    if not id_usuario_autenticado:
        return "no_autorizado", "Autenticación requerida para responder una partida.", None, {}

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        partida = _obtener_partida(id_partida, cursor, bloquear=True)
        if not partida:
            return "no_existe", "La partida solicitada no existe.", None, {}
        if partida.get("id_usuario") != id_usuario_autenticado:
            return "no_autorizado", "No puede responder una partida de otro usuario.", None, {}

        respuesta_previa = _respuesta_idempotente(id_partida, datos_limpios["request_id"], cursor)
        if respuesta_previa:
            conexion.commit()
            return (
                respuesta_previa["codigo"],
                respuesta_previa["mensaje"],
                respuesta_previa["data"],
                respuesta_previa["errors"],
            )

        if partida["estado"] != "en_curso":
            return "estado_incompatible", "La partida ya ha finalizado.", {"partida": serializar_partida(partida)}, {}

        ejercicio = None
        id_ejercicio_intento = None
        id_ejercicio_generado_intento = None
        if partida.get("id_ejercicio_generado_actual"):
            if partida["id_ejercicio_generado_actual"] != datos_limpios["id_ejercicio_generado"]:
                return "datos_invalidos", "La pregunta enviada no corresponde a la partida actual.", None, {"id_ejercicio_generado": "Pregunta desincronizada."}
            ejercicio = obtener_ejercicio_generado(datos_limpios["id_ejercicio_generado"], cursor)
            if not ejercicio or ejercicio["id_partida"] != id_partida:
                return "datos_invalidos", "El ejercicio generado no pertenece a esta partida.", None, {}
            id_ejercicio_generado_intento = ejercicio["id_ejercicio_generado"]
        elif partida["id_ejercicio_actual"] != datos_limpios["id_ejercicio"]:
            return "datos_invalidos", "La pregunta enviada no corresponde a la partida actual.", None, {"id_ejercicio": "Pregunta desincronizada."}
        else:
            ejercicio = obtener_ejercicio_publicado(datos_limpios["id_ejercicio"], cursor)
            if not ejercicio:
                return "datos_invalidos", "El ejercicio actual no está publicado.", None, {}
            id_ejercicio_intento = ejercicio["id_ejercicio"]

        es_correcta = _evaluar_respuesta(ejercicio, datos_limpios["respuesta"])
        casilla_antes = partida["casilla_actual"]
        vidas_antes = partida["vidas_restantes"]
        total_correctos_despues = int(partida["total_correctos"] or 0) + (1 if es_correcta else 0)
        casilla_despues = min(total_correctos_despues, CASILLA_FINAL) if es_correcta else casilla_antes
        vidas_despues = vidas_antes if es_correcta else max(vidas_antes - 1, 0)
        estado = "en_curso"
        motivo = None
        if total_correctos_despues >= CASILLA_FINAL and casilla_despues >= CASILLA_FINAL:
            estado = "completada"
            motivo = "recorrido_completado"
        elif vidas_despues <= 0:
            estado = "sin_vidas"
            motivo = "sin_vidas"

        cursor.execute(
            """
            INSERT INTO intentos_juego
                (id_partida, id_ejercicio, id_ejercicio_generado, respuesta_estudiante, es_correcta, nivel_al_responder,
                 tiempo_respuesta_ms, casilla_antes, casilla_despues, vidas_antes, vidas_despues,
                 request_id, respuesta_api_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, JSON_OBJECT('registrado', true))
            """,
            (
                id_partida,
                id_ejercicio_intento,
                id_ejercicio_generado_intento,
                str(datos_limpios["respuesta"]).strip(),
                1 if es_correcta else 0,
                partida["id_nivel_actual"],
                datos_limpios["tiempo"],
                casilla_antes,
                casilla_despues,
                vidas_antes,
                vidas_despues,
                datos_limpios["request_id"],
            ),
        )
        id_intento = cursor.lastrowid

        metricas = _obtener_metricas(partida, cursor)
        niveles = _obtener_niveles(cursor)
        nivel_actual = _obtener_nivel_por_id(partida["id_nivel_actual"], cursor)
        decision = MotorReglasAdaptativo(niveles, _obtener_reglas(cursor)).decidir(metricas, nivel_actual)
        estado_contextual = actualizar_progreso_contextual(
            partida, es_correcta, datos_limpios["tiempo"], decision["nivel_recomendado"], cursor
        )
        id_nivel_nuevo = estado_contextual["id_nivel"]
        nivel_nuevo = _obtener_nivel_por_id(id_nivel_nuevo, cursor)
        partida_contextual = {
            **partida,
            "id_grado": estado_contextual["id_grado"],
            "id_tema": estado_contextual["id_tema"],
            "id_nivel_actual": id_nivel_nuevo,
        }
        siguiente_pregunta = _generar_siguiente_pregunta_partida(partida_contextual, id_nivel_nuevo, cursor) if estado == "en_curso" else None
        if estado == "en_curso" and not siguiente_pregunta:
            conexion.rollback()
            return "configuracion_incompleta", "No existe una plantilla procedimental válida para continuar la partida.", None, {}
        siguiente_id_ejercicio = siguiente_pregunta.get("id_ejercicio") if siguiente_pregunta else None
        siguiente_id_generado = siguiente_pregunta.get("id_ejercicio_generado") if siguiente_pregunta else None

        cursor.execute(
            """
            UPDATE partidas_juego
            SET id_grado = %s,
                id_tema = %s,
                casilla_actual = %s,
                total_correctos = total_correctos + %s,
                total_errores = total_errores + %s,
                vidas_restantes = %s,
                vidas_perdidas_total = vidas_perdidas_total + %s,
                preguntas_respondidas = preguntas_respondidas + 1,
                id_nivel_actual = %s,
                id_ejercicio_actual = %s,
                id_ejercicio_generado_actual = %s,
                estado = %s,
                motivo_finalizacion = %s,
                fecha_fin = CASE WHEN %s <> 'en_curso' THEN CURRENT_TIMESTAMP ELSE fecha_fin END,
                fecha_ultima_actividad = CURRENT_TIMESTAMP
            WHERE id_partida = %s
            """,
            (
                estado_contextual["id_grado"],
                estado_contextual["id_tema"],
                casilla_despues,
                1 if es_correcta else 0,
                0 if es_correcta else 1,
                vidas_despues,
                0 if es_correcta else 1,
                id_nivel_nuevo,
                siguiente_id_ejercicio,
                siguiente_id_generado,
                estado,
                motivo,
                estado,
                id_partida,
            ),
        )

        cursor.execute(
            """
            INSERT INTO decisiones_agente
                (id_partida, id_intento, id_tema, tipo_contexto, nivel_anterior, nivel_nuevo, accion,
                 regla_aplicada, motivo, datos_entrada_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_partida,
                id_intento,
                estado_contextual["id_tema"],
                partida.get("tipo_contexto") or ("asignacion" if partida.get("id_asignacion") else "personal"),
                partida["id_nivel_actual"],
                id_nivel_nuevo,
                estado_contextual["accion"] if estado_contextual["promocionado"] else decision["accion"],
                estado_contextual["codigo_regla"] or decision["codigo_regla"],
                "Promoción curricular por dominio sostenido." if estado_contextual["promocionado"] else decision["explicacion"],
                json.dumps(metricas),
            ),
        )

        registrar_cierre_partida_asignada(
            partida.get("id_asignacion"),
            partida["id_usuario"],
            id_partida,
            estado,
            total_correctos_despues,
            casilla_despues,
            cursor,
        )
        partida_para_recompensa = {
            **partida,
            "estado": estado,
            "casilla_actual": casilla_despues,
            "total_correctos": total_correctos_despues,
            "total_errores": int(partida.get("total_errores") or 0) + (0 if es_correcta else 1),
            "vidas_perdidas_total": int(partida.get("vidas_perdidas_total") or 0) + (0 if es_correcta else 1),
        }
        recompensa = acreditar_recompensa_partida(partida_para_recompensa, cursor)
        saldo_monedas = recompensa["saldo_actual"] if recompensa else obtener_saldo_en_cursor(partida["id_usuario"], cursor)
        sincronizar_progreso_usuario(partida["id_usuario"], cursor)
        conexion.commit()
        partida_actualizada = obtener_partida_adaptativa(id_partida)
        data = {
            "resultado": {
                "correcta": es_correcta,
                "respuesta_correcta": None if es_correcta else ejercicio.get("respuesta_correcta"),
                "explicacion_pasos": obtener_explicacion_pasos_ejercicio(ejercicio) if not es_correcta else None,
            },
            "partida": partida_actualizada,
            "agente": {
                "accion": estado_contextual["accion"] if estado_contextual["promocionado"] else decision["accion"],
                "regla_aplicada": estado_contextual["codigo_regla"] or decision["codigo_regla"],
                "mensaje": decision["mensaje"],
                "motivo": "Promoción curricular por dominio sostenido." if estado_contextual["promocionado"] else decision["explicacion"],
                "recomendar_refuerzo": decision["recomendar_refuerzo"],
                "nivel_anterior": nivel_actual,
                "nivel_nuevo": nivel_nuevo,
                "metricas": {k: v for k, v in metricas.items() if k != "decisiones_recientes"},
            },
            "siguiente_pregunta": siguiente_pregunta,
            "animacion": "avance" if es_correcta else "error",
            "recompensa": recompensa,
            "saldo_monedas": saldo_monedas,
        }
        return "actualizado", "Respuesta registrada correctamente.", data, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()
