from db import obtener_conexion
from models.grado import Grado
from services.grupos_service import (
    sincronizar_codigos_grado_docente,
)
from services.instituciones_service import (
    SECCION_FALLBACK,
    SECCIONES_CONFIGURABLES,
    configurar_secciones_docente,
    obtener_id_institucion_grado,
    obtener_institucion_docente,
)


class Seccion:
    # Funcion: convertir_fila_a_diccionario
    # Descripcion:
    #   Transforma una fila combinada de secciones y grados en el formato JSON esperado por el frontend.
    #
    # Es llamada desde:
    #   Los metodos obtener_todas(), obtener_por_id(), crear(), actualizar() y cambiar_estado().
    #
    # Llama a:
    #   No llama a servicios externos; solo organiza los datos recibidos desde MySQL.
    #
    # Retorna:
    #   Un diccionario con datos de la seccion, grado relacionado y fechas en texto.
    #
    # Manejo de errores:
    #   Si recibe None, retorna None para evitar errores al serializar respuestas 404.
    @staticmethod
    def convertir_fila_a_diccionario(fila):
        if fila is None:
            return None

        return {
            "id_seccion": fila["id_seccion"],
            "id_grado": fila["id_grado"],
            "id_institucion": fila.get("id_institucion"),
            "id_institucion_grado": fila.get("id_institucion_grado"),
            "nombre_seccion": fila["nombre_seccion"],
            "descripcion": fila["descripcion"],
            "estado": fila["estado"],
            "grado": {
                "id_grado": fila["id_grado"],
                "codigo_grado": fila["codigo_grado"],
                "nombre_grado": fila["nombre_grado"],
            },
            "institucion": fila.get("institucion"),
            "fecha_creacion": fila["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S") if fila["fecha_creacion"] else None,
            "fecha_modificacion": fila["fecha_modificacion"].strftime("%Y-%m-%d %H:%M:%S") if fila["fecha_modificacion"] else None,
        }

    # Funcion: obtener_todas
    # Descripcion:
    #   Consulta todas las secciones registradas, incluyendo la informacion basica del grado relacionado.
    #
    # Es llamada desde:
    #   La ruta GET /api/secciones en backend/routes/secciones_routes.py.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta una consulta SELECT con INNER JOIN hacia grados.
    #
    # Retorna:
    #   Una lista de diccionarios ordenada por grado y nombre de seccion.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que la ruta retorne HTTP 500 uniforme.
    @staticmethod
    def obtener_todas(estado=None, usuario=None):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            parametros = []
            filtros = ["s.nombre_seccion <> %s"]
            parametros.append(SECCION_FALLBACK)
            if estado:
                filtros.append("s.estado = %s")
                parametros.append(estado)
            join_docente = ""
            if usuario and usuario["rol"] == "docente":
                join_docente = """
                INNER JOIN docente_secciones ds
                    ON ds.id_seccion = s.id_seccion
                   AND ds.id_docente = %s
                   AND ds.estado = 'activo'
                """
                parametros.insert(0, usuario["id_usuario"])
            where = "WHERE " + " AND ".join(filtros)

            cursor.execute(
                f"""
                SELECT
                    s.id_seccion,
                    s.id_grado,
                    s.id_institucion_grado,
                    i.id_institucion,
                    i.nombre AS institucion,
                    s.nombre_seccion,
                    s.descripcion,
                    s.estado,
                    s.fecha_creacion,
                    s.fecha_modificacion,
                    g.codigo_grado,
                    g.nombre_grado
                FROM secciones s
                {join_docente}
                LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = s.id_institucion_grado
                LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
                INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, s.id_grado)
                {where}
                ORDER BY i.nombre ASC, g.id_grado ASC, s.nombre_seccion ASC
                """,
                tuple(parametros),
            )
            return [Seccion.convertir_fila_a_diccionario(fila) for fila in cursor.fetchall()]
        finally:
            cursor.close()
            conexion.close()

    # Funcion: obtener_por_id
    # Descripcion:
    #   Consulta una seccion especifica por su identificador, incluyendo la informacion del grado.
    #
    # Es llamada desde:
    #   Las rutas GET, PUT, PATCH y DELETE de /api/secciones en backend/routes/secciones_routes.py.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta una consulta SELECT con INNER JOIN hacia grados.
    #
    # Retorna:
    #   Un diccionario si la seccion existe o None si no existe.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que la ruta retorne HTTP 500 uniforme.
    @staticmethod
    def obtener_por_id(id_seccion):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    s.id_seccion,
                    s.id_grado,
                    s.id_institucion_grado,
                    i.id_institucion,
                    i.nombre AS institucion,
                    s.nombre_seccion,
                    s.descripcion,
                    s.estado,
                    s.fecha_creacion,
                    s.fecha_modificacion,
                    g.codigo_grado,
                    g.nombre_grado
                FROM secciones s
                LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = s.id_institucion_grado
                LEFT JOIN instituciones i ON i.id_institucion = ig.id_institucion
                INNER JOIN grados g ON g.id_grado = COALESCE(ig.id_grado_base, s.id_grado)
                WHERE s.id_seccion = %s
                """,
                (id_seccion,),
            )
            return Seccion.convertir_fila_a_diccionario(cursor.fetchone())
        finally:
            cursor.close()
            conexion.close()

    # Funcion: existe_duplicado
    # Descripcion:
    #   Verifica si ya existe una seccion con el mismo nombre dentro del mismo grado.
    #
    # Es llamada desde:
    #   Los metodos crear() y actualizar() antes de guardar datos en MySQL.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta una consulta SELECT COUNT sobre secciones.
    #
    # Retorna:
    #   True si existe duplicado, False si el nombre esta disponible.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que la ruta Flask lo maneje.
    @staticmethod
    def existe_duplicado(id_grado, nombre_seccion, id_seccion_excluida=None, id_institucion_grado=None):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            parametros = [nombre_seccion]
            filtro_contexto = "id_grado = %s AND id_institucion_grado IS NULL"
            if id_institucion_grado:
                filtro_contexto = "id_institucion_grado = %s"
                parametros.append(id_institucion_grado)
            else:
                parametros.append(id_grado)
            filtro_exclusion = ""
            if id_seccion_excluida:
                filtro_exclusion = "AND id_seccion <> %s"
                parametros.append(id_seccion_excluida)

            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM secciones
                WHERE nombre_seccion = %s
                  AND {filtro_contexto}
                  {filtro_exclusion}
                """,
                tuple(parametros),
            )
            fila = cursor.fetchone()
            return fila["total"] > 0
        finally:
            cursor.close()
            conexion.close()

    # Funcion: crear
    # Descripcion:
    #   Inserta una nueva seccion en MySQL despues de validar grado, nombre, estado y duplicados.
    #
    # Es llamada desde:
    #   La ruta POST /api/secciones en backend/routes/secciones_routes.py.
    #
    # Llama a:
    #   Grado.existe(), Seccion.existe_duplicado(), obtener_conexion() y Seccion.obtener_por_id().
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje y datos de la seccion creada.
    #
    # Manejo de errores:
    #   Si falla la insercion, ejecuta rollback y relanza el error para que Flask responda HTTP 500.
    @staticmethod
    def crear(datos, usuario=None):
        id_grado = datos.get("id_grado")
        nombre_seccion = (datos.get("nombre_seccion") or "").strip()
        descripcion = (datos.get("descripcion") or "").strip() or None
        estado = datos.get("estado", "activo")

        if not id_grado:
            return "datos_invalidos", "El grado es obligatorio.", None
        nombre_seccion = nombre_seccion.upper()
        if nombre_seccion not in SECCIONES_CONFIGURABLES:
            return "datos_invalidos", "Seleccione una seccion valida: A, B, C o D.", None
        if estado not in ("activo", "inactivo"):
            return "datos_invalidos", "El estado debe ser activo o inactivo.", None
        if not Grado.existe(id_grado):
            return "grado_no_existe", "El grado seleccionado no existe.", None
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            if usuario and usuario["rol"] == "docente":
                institucion = obtener_institucion_docente(usuario["id_usuario"], cursor)
                if not institucion:
                    return "datos_invalidos", "El docente debe seleccionar una institucion antes de crear secciones.", None
                id_institucion_grado = obtener_id_institucion_grado(institucion["id_institucion"], int(id_grado), cursor)
                ids_seccion = configurar_secciones_docente(
                    usuario["id_usuario"],
                    id_institucion_grado,
                    [nombre_seccion],
                    cursor,
                )
                id_seccion = ids_seccion[0]
                cursor.execute(
                    """
                    UPDATE secciones
                    SET descripcion = %s,
                        estado = %s
                    WHERE id_seccion = %s
                    """,
                    (descripcion, estado, id_seccion),
                )
                sincronizar_codigos_grado_docente(usuario["id_usuario"], int(id_grado), cursor, id_institucion_grado)
            else:
                if Seccion.existe_duplicado(id_grado, nombre_seccion):
                    return "duplicado", "Ya existe una seccion con ese nombre para el grado seleccionado.", None
                cursor.execute(
                    """
                    INSERT INTO secciones (id_grado, nombre_seccion, descripcion, estado)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_grado, nombre_seccion, descripcion, estado),
                )
                id_seccion = cursor.lastrowid
            conexion.commit()
            nueva_seccion = Seccion.obtener_por_id(id_seccion)
            return "creado", "Seccion creada correctamente.", nueva_seccion
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: actualizar
    # Descripcion:
    #   Actualiza los datos de una seccion existente sin afectar otras secciones.
    #
    # Es llamada desde:
    #   La ruta PUT /api/secciones/<id_seccion> en backend/routes/secciones_routes.py.
    #
    # Llama a:
    #   Seccion.obtener_por_id(), Grado.existe(), Seccion.existe_duplicado() y obtener_conexion().
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje y datos actualizados de la seccion.
    #
    # Manejo de errores:
    #   Si falla la actualizacion, ejecuta rollback y relanza el error para que Flask responda HTTP 500.
    @staticmethod
    def actualizar(id_seccion, datos):
        seccion_actual = Seccion.obtener_por_id(id_seccion)
        if not seccion_actual:
            return "no_existe", "La seccion solicitada no existe.", None

        id_grado = datos.get("id_grado")
        nombre_seccion = (datos.get("nombre_seccion") or "").strip()
        descripcion = (datos.get("descripcion") or "").strip() or None
        estado = datos.get("estado", "activo")

        if not id_grado:
            return "datos_invalidos", "El grado es obligatorio.", None
        nombre_seccion = nombre_seccion.upper()
        if nombre_seccion not in SECCIONES_CONFIGURABLES:
            return "datos_invalidos", "Seleccione una seccion valida: A, B, C o D.", None
        if estado not in ("activo", "inactivo"):
            return "datos_invalidos", "El estado debe ser activo o inactivo.", None
        if not Grado.existe(id_grado):
            return "grado_no_existe", "El grado seleccionado no existe.", None
        if Seccion.existe_duplicado(
            id_grado,
            nombre_seccion,
            id_seccion,
            seccion_actual.get("id_institucion_grado"),
        ):
            return "duplicado", "Ya existe una seccion con ese nombre para el grado seleccionado.", None

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE secciones
                SET id_grado = %s,
                    nombre_seccion = %s,
                    descripcion = %s,
                    estado = %s
                WHERE id_seccion = %s
                """,
                (id_grado, nombre_seccion, descripcion, estado, id_seccion),
            )
            conexion.commit()
            return "actualizado", "Seccion actualizada correctamente.", Seccion.obtener_por_id(id_seccion)
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: cambiar_estado
    # Descripcion:
    #   Cambia una seccion a estado activo o inactivo sin eliminar el registro.
    #
    # Es llamada desde:
    #   La ruta PATCH /api/secciones/<id_seccion>/estado en backend/routes/secciones_routes.py.
    #
    # Llama a:
    #   Seccion.obtener_por_id() y obtener_conexion() para validar y actualizar el registro.
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje y datos actualizados.
    #
    # Manejo de errores:
    #   Si falla la actualizacion, ejecuta rollback y relanza el error para que Flask responda HTTP 500.
    @staticmethod
    def cambiar_estado(id_seccion, estado):
        if estado not in ("activo", "inactivo"):
            return "datos_invalidos", "El estado debe ser activo o inactivo.", None
        if not Seccion.obtener_por_id(id_seccion):
            return "no_existe", "La seccion solicitada no existe.", None

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "UPDATE secciones SET estado = %s WHERE id_seccion = %s",
                (estado, id_seccion),
            )
            conexion.commit()
            return "actualizado", "Estado de la seccion actualizado correctamente.", Seccion.obtener_por_id(id_seccion)
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: tiene_relaciones
    # Descripcion:
    #   Revisa tablas frecuentes que podrian usar id_seccion antes de permitir una eliminacion fisica.
    #
    # Es llamada desde:
    #   El metodo eliminar() antes de ejecutar DELETE sobre secciones.
    #
    # Llama a:
    #   obtener_conexion() y consulta information_schema para detectar tablas relacionadas existentes.
    #
    # Retorna:
    #   True si encuentra registros relacionados, False si no encuentra relaciones.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que la ruta Flask lo maneje.
    @staticmethod
    def tiene_relaciones(id_seccion):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT TABLE_NAME AS tabla
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND COLUMN_NAME = 'id_seccion'
                  AND TABLE_NAME <> 'secciones'
                """
            )
            tablas = [fila["tabla"] for fila in cursor.fetchall()]
            for tabla in tablas:
                cursor.execute(f"SELECT COUNT(*) AS total FROM `{tabla}` WHERE id_seccion = %s", (id_seccion,))
                if cursor.fetchone()["total"] > 0:
                    return True
            return False
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(id_seccion):
        # Conserva compatibilidad interna: eliminar ahora solo desactiva y no borra fisicamente.
        seccion = Seccion.obtener_por_id(id_seccion)
        if not seccion:
            return "no_existe", "La seccion solicitada no existe.", None
        return Seccion.cambiar_estado(id_seccion, "inactivo")
