import re

from mysql.connector import IntegrityError

from db import obtener_conexion


GRADOS_BASE = (
    {"codigo_grado": "4P", "nombre_grado": "Cuarto", "descripcion": "Cuarto grado base", "orden_visualizacion": 1},
    {"codigo_grado": "5P", "nombre_grado": "Quinto", "descripcion": "Quinto grado base", "orden_visualizacion": 2},
    {"codigo_grado": "6P", "nombre_grado": "Sexto", "descripcion": "Sexto grado base", "orden_visualizacion": 3},
)
SECCIONES_CONFIGURABLES = ("A", "B", "C", "D")
SECCION_FALLBACK = "Única"


class SeccionAsignadaError(ValueError):
    # Indica que una seccion institucional activa pertenece a otro docente.
    def __init__(self, nombre_seccion):
        self.nombre_seccion = nombre_seccion
        super().__init__(f"La sección {nombre_seccion} ya está asignada a otro docente.")


def normalizar_nombre_institucion(nombre):
    # Normaliza texto para comparar instituciones sin duplicar por espacios o mayusculas.
    return re.sub(r"\s+", " ", (nombre or "").strip()).lower()


def _serializar_fecha(valor):
    # Convierte fechas MySQL a texto JSON estable.
    return valor.strftime("%Y-%m-%d %H:%M:%S") if valor else None


def _serializar_institucion(fila):
    # Entrega la institucion en el formato uniforme usado por frontend.
    if not fila:
        return None
    return {
        "id_institucion": fila["id_institucion"],
        "nombre": fila["nombre"],
        "descripcion": fila.get("descripcion"),
        "estado": fila.get("estado"),
        "fecha_creacion": _serializar_fecha(fila.get("fecha_creacion")),
        "fecha_modificacion": _serializar_fecha(fila.get("fecha_modificacion")),
    }


def garantizar_grados_base(cursor):
    # Asegura que el catalogo global tenga solo los tres nombres base principales.
    ids = {}
    for grado in GRADOS_BASE:
        cursor.execute(
            """
            SELECT id_grado
            FROM grados
            WHERE codigo_grado = %s OR nombre_grado = %s
            ORDER BY CASE WHEN codigo_grado = %s THEN 0 ELSE 1 END, id_grado ASC
            LIMIT 1
            """,
            (grado["codigo_grado"], grado["nombre_grado"], grado["codigo_grado"]),
        )
        fila = cursor.fetchone()
        if fila:
            id_grado = fila["id_grado"]
            cursor.execute(
                """
                UPDATE grados
                SET codigo_grado = %s,
                    nombre_grado = %s,
                    descripcion = %s,
                    orden_visualizacion = %s,
                    estado = 'activo'
                WHERE id_grado = %s
                """,
                (
                    grado["codigo_grado"],
                    grado["nombre_grado"],
                    grado["descripcion"],
                    grado["orden_visualizacion"],
                    id_grado,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO grados (codigo_grado, nombre_grado, descripcion, orden_visualizacion, estado)
                VALUES (%s, %s, %s, %s, 'activo')
                """,
                (
                    grado["codigo_grado"],
                    grado["nombre_grado"],
                    grado["descripcion"],
                    grado["orden_visualizacion"],
                ),
            )
            id_grado = cursor.lastrowid
        ids[grado["codigo_grado"]] = id_grado
    return ids


def garantizar_grados_institucion(id_institucion, cursor):
    # Crea los tres grados institucionales faltantes y reutiliza los existentes.
    ids_base = garantizar_grados_base(cursor)
    for id_grado_base in ids_base.values():
        cursor.execute(
            """
            INSERT INTO institucion_grados (id_institucion, id_grado_base, estado)
            SELECT %s, %s, 'activo'
            WHERE NOT EXISTS (
                SELECT 1
                FROM institucion_grados
                WHERE id_institucion = %s
                  AND id_grado_base = %s
            )
            """,
            (id_institucion, id_grado_base, id_institucion, id_grado_base),
        )
    cursor.execute(
        """
        SELECT ig.id_institucion_grado, ig.id_institucion, ig.id_grado_base,
               g.codigo_grado, g.nombre_grado, ig.estado
        FROM institucion_grados ig
        INNER JOIN grados g ON g.id_grado = ig.id_grado_base
        WHERE ig.id_institucion = %s
        ORDER BY g.orden_visualizacion ASC
        """,
        (id_institucion,),
    )
    return cursor.fetchall()


def obtener_o_crear_institucion(nombre, cursor, descripcion=None):
    # Reutiliza una institucion existente por nombre normalizado o crea una nueva con sus tres grados.
    nombre_limpio = re.sub(r"\s+", " ", (nombre or "").strip())
    nombre_normalizado = normalizar_nombre_institucion(nombre_limpio)
    if not nombre_limpio:
        return None

    cursor.execute(
        """
        SELECT *
        FROM instituciones
        WHERE nombre_normalizado = %s
        LIMIT 1
        """,
        (nombre_normalizado,),
    )
    existente = cursor.fetchone()
    if existente:
        cursor.execute(
            "UPDATE instituciones SET estado = 'activo' WHERE id_institucion = %s",
            (existente["id_institucion"],),
        )
        garantizar_grados_institucion(existente["id_institucion"], cursor)
        cursor.execute("SELECT * FROM instituciones WHERE id_institucion = %s", (existente["id_institucion"],))
        return cursor.fetchone()

    cursor.execute(
        """
        INSERT INTO instituciones (nombre, nombre_normalizado, descripcion, estado)
        VALUES (%s, %s, %s, 'activo')
        """,
        (nombre_limpio, nombre_normalizado, descripcion),
    )
    id_institucion = cursor.lastrowid
    garantizar_grados_institucion(id_institucion, cursor)
    cursor.execute("SELECT * FROM instituciones WHERE id_institucion = %s", (id_institucion,))
    return cursor.fetchone()


def buscar_instituciones(texto):
    # Busca instituciones activas por texto normalizado para el onboarding docente.
    normalizado = normalizar_nombre_institucion(texto)
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        patron = f"%{normalizado}%"
        cursor.execute(
            """
            SELECT *
            FROM instituciones
            WHERE estado = 'activo'
              AND (%s = '' OR nombre_normalizado LIKE %s)
            ORDER BY nombre ASC
            LIMIT 12
            """,
            (normalizado, patron),
        )
        return "consultado", "Instituciones consultadas correctamente.", [
            _serializar_institucion(fila) for fila in cursor.fetchall()
        ], {}
    finally:
        cursor.close()
        conexion.close()


def obtener_institucion_activa_por_id(id_institucion, cursor):
    # Valida que la institucion seleccionada exista y este activa.
    cursor.execute(
        """
        SELECT *
        FROM instituciones
        WHERE id_institucion = %s
          AND estado = 'activo'
        LIMIT 1
        """,
        (id_institucion,),
    )
    return cursor.fetchone()


def obtener_institucion_docente(id_docente, cursor):
    # Consulta la institucion activa vinculada al perfil docente.
    cursor.execute(
        """
        SELECT i.*
        FROM perfiles_docente pd
        INNER JOIN instituciones i ON i.id_institucion = pd.id_institucion
        WHERE pd.id_usuario = %s
        LIMIT 1
        """,
        (id_docente,),
    )
    return cursor.fetchone()


def obtener_id_institucion_grado(id_institucion, id_grado_base, cursor):
    # Obtiene el grado institucional que conecta institucion con grado base.
    garantizar_grados_institucion(id_institucion, cursor)
    cursor.execute(
        """
        SELECT id_institucion_grado
        FROM institucion_grados
        WHERE id_institucion = %s
          AND id_grado_base = %s
          AND estado = 'activo'
        LIMIT 1
        """,
        (id_institucion, id_grado_base),
    )
    fila = cursor.fetchone()
    return fila["id_institucion_grado"] if fila else None


def normalizar_secciones_configurables(nombres):
    # Acepta solo secciones A-D provenientes del frontend.
    secciones = []
    for nombre in nombres or []:
        valor = str(nombre or "").strip().upper()
        if valor not in SECCIONES_CONFIGURABLES:
            raise ValueError("Solo se permiten las secciones A, B, C y D.")
        if valor not in secciones:
            secciones.append(valor)
    return secciones


def obtener_o_crear_seccion_institucional(id_institucion_grado, nombre_seccion, cursor, estado="activo"):
    # Crea o reactiva una seccion institucional sin duplicar A-D o Única.
    cursor.execute(
        """
        SELECT ig.id_grado_base
        FROM institucion_grados ig
        WHERE ig.id_institucion_grado = %s
        LIMIT 1
        """,
        (id_institucion_grado,),
    )
    grado = cursor.fetchone()
    if not grado:
        return None

    cursor.execute(
        """
        SELECT id_seccion
        FROM secciones
        WHERE id_institucion_grado = %s
          AND nombre_seccion = %s
        LIMIT 1
        """,
        (id_institucion_grado, nombre_seccion),
    )
    seccion = cursor.fetchone()
    if seccion:
        cursor.execute(
            """
            UPDATE secciones
            SET id_grado = %s,
                estado = %s
            WHERE id_seccion = %s
            """,
            (grado["id_grado_base"], estado, seccion["id_seccion"]),
        )
        return seccion["id_seccion"]

    cursor.execute(
        """
        INSERT INTO secciones (id_grado, id_institucion_grado, nombre_seccion, descripcion, estado)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (grado["id_grado_base"], id_institucion_grado, nombre_seccion, None, estado),
    )
    return cursor.lastrowid


def _validar_seccion_disponible(id_docente, id_seccion, nombre_seccion, cursor):
    # Bloquea la fila activa para evitar carreras entre docentes que toman la misma seccion.
    cursor.execute(
        """
        SELECT id_docente
        FROM docente_secciones
        WHERE id_seccion = %s
          AND estado = 'activo'
        FOR UPDATE
        """,
        (id_seccion,),
    )
    propietarios = cursor.fetchall()
    for propietario in propietarios:
        if propietario["id_docente"] != id_docente:
            raise SeccionAsignadaError(nombre_seccion)


def configurar_secciones_docente(id_docente, id_institucion_grado, nombres_seccion, cursor):
    # Vincula al docente con A-D; si no selecciona ninguna, genera Única como fallback.
    secciones = normalizar_secciones_configurables(nombres_seccion)
    nombres_finales = secciones or [SECCION_FALLBACK]
    ids_seccion = []
    for nombre in nombres_finales:
        id_seccion = obtener_o_crear_seccion_institucional(id_institucion_grado, nombre, cursor)
        _validar_seccion_disponible(id_docente, id_seccion, nombre, cursor)
        ids_seccion.append(id_seccion)

    cursor.execute(
        """
        SELECT s.id_seccion
        FROM secciones s
        WHERE s.id_institucion_grado = %s
        """,
        (id_institucion_grado,),
    )
    ids_grado = [fila["id_seccion"] for fila in cursor.fetchall()]
    if ids_grado:
        formato = ",".join(["%s"] * len(ids_grado))
        cursor.execute(
            f"""
            UPDATE docente_secciones
            SET estado = 'inactivo',
                fecha_fin = CURRENT_TIMESTAMP
            WHERE id_docente = %s
              AND id_seccion IN ({formato})
            """,
            tuple([id_docente, *ids_grado]),
        )

    if secciones:
        cursor.execute(
            """
            UPDATE secciones
            SET estado = 'inactivo'
            WHERE id_institucion_grado = %s
              AND nombre_seccion = %s
            """,
            (id_institucion_grado, SECCION_FALLBACK),
        )

    for id_seccion in ids_seccion:
        try:
            cursor.execute(
                """
                INSERT INTO docente_secciones (id_docente, id_seccion, estado)
                VALUES (%s, %s, 'activo')
                ON DUPLICATE KEY UPDATE estado = 'activo', fecha_fin = NULL
                """,
                (id_docente, id_seccion),
            )
        except IntegrityError as error:
            if getattr(error, "errno", None) == 1062:
                cursor.execute("SELECT nombre_seccion FROM secciones WHERE id_seccion = %s", (id_seccion,))
                seccion = cursor.fetchone() or {}
                raise SeccionAsignadaError(seccion.get("nombre_seccion") or "seleccionada") from error
            raise
    return ids_seccion


def listar_disponibilidad_secciones(id_docente, id_institucion):
    # Devuelve A-D por grado indicando si cada seccion esta libre, ocupada por otro docente o propia.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        institucion = obtener_institucion_activa_por_id(id_institucion, cursor)
        if not institucion:
            return "no_encontrado", "La institucion seleccionada no existe.", None, {
                "id_institucion": "Institucion inexistente o inactiva."
            }
        grados = garantizar_grados_institucion(id_institucion, cursor)
        resultado = []
        for grado in grados:
            secciones = []
            for nombre in SECCIONES_CONFIGURABLES:
                cursor.execute(
                    """
                    SELECT s.id_seccion, ds.id_docente
                    FROM secciones s
                    LEFT JOIN docente_secciones ds
                        ON ds.id_seccion = s.id_seccion
                       AND ds.estado = 'activo'
                    WHERE s.id_institucion_grado = %s
                      AND s.nombre_seccion = %s
                      AND s.estado = 'activo'
                    LIMIT 1
                    """,
                    (grado["id_institucion_grado"], nombre),
                )
                asignacion = cursor.fetchone()
                propia = bool(asignacion and asignacion["id_docente"] == id_docente)
                disponible = not (asignacion and asignacion["id_docente"]) or propia
                secciones.append({
                    "id_seccion": asignacion.get("id_seccion") if asignacion else None,
                    "nombre_seccion": nombre,
                    "disponible": disponible,
                    "propia": propia,
                    "estado": "propia" if propia else ("ocupada" if asignacion and asignacion["id_docente"] else "disponible"),
                })
            resultado.append({
                "id_grado": grado["id_grado_base"],
                "id_institucion_grado": grado["id_institucion_grado"],
                "codigo_grado": grado["codigo_grado"],
                "nombre_grado": grado["nombre_grado"],
                "secciones": secciones,
            })
        conexion.commit()
        return "consultado", "Disponibilidad consultada correctamente.", resultado, {}
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()
