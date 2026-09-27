from db import obtener_conexion

from services.instituciones_service import GRADOS_BASE


GRADOS_BASE_POR_CODIGO = {grado["codigo_grado"]: grado for grado in GRADOS_BASE}
GRADOS_BASE_POR_NOMBRE = {grado["nombre_grado"].lower(): grado for grado in GRADOS_BASE}


class Grado:
    # Funcion: convertir_fila_a_diccionario
    # Descripcion:
    #   Convierte una fila de la consulta de grados en el formato JSON uniforme usado por React.
    #
    # Es llamada desde:
    #   obtener_todos(), obtener_por_id(), crear(), actualizar() y cambiar_estado() dentro de este modelo.
    #
    # Llama a:
    #   No llama a otros servicios; solo formatea datos recibidos desde MySQL.
    #
    # Parametros:
    #   fila: diccionario retornado por mysql-connector con datos del grado y total_secciones.
    #
    # Retorna:
    #   Un diccionario con datos completos del grado o None si no hay fila.
    #
    # Manejo de errores:
    #   Si la fila es None retorna None para que la ruta pueda responder 404 de forma controlada.
    @staticmethod
    def convertir_fila_a_diccionario(fila):
        if fila is None:
            return None

        return {
            "id_grado": fila["id_grado"],
            "codigo_grado": fila["codigo_grado"],
            "nombre_grado": fila["nombre_grado"],
            "descripcion": fila.get("descripcion"),
            "orden_visualizacion": fila.get("orden_visualizacion"),
            "estado": fila.get("estado"),
            "total_secciones": fila.get("total_secciones", 0),
            "fecha_creacion": fila["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_creacion") else None,
            "fecha_modificacion": fila["fecha_modificacion"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_modificacion") else None,
        }

    # Funcion: validar_datos
    # Descripcion:
    #   Valida y normaliza los datos enviados para crear o actualizar un grado.
    #
    # Es llamada desde:
    #   crear() y actualizar() antes de consultar duplicados o guardar en MySQL.
    #
    # Llama a:
    #   No llama servicios externos; solo valida reglas de negocio locales.
    #
    # Parametros:
    #   datos: diccionario recibido desde el JSON de la ruta Flask.
    #
    # Retorna:
    #   Una tupla con datos normalizados y diccionario de errores por campo.
    #
    # Manejo de errores:
    #   Acumula errores de validacion y evita que datos invalidos lleguen a MySQL.
    @staticmethod
    def validar_datos(datos):
        errores = {}
        codigo_grado = (datos.get("codigo_grado") or "").strip().upper()
        nombre_grado = (datos.get("nombre_grado") or "").strip()
        descripcion = (datos.get("descripcion") or "").strip() or None
        estado = datos.get("estado", "activo")

        try:
            orden_visualizacion = int(datos.get("orden_visualizacion", 1))
        except (TypeError, ValueError):
            orden_visualizacion = 0

        if not codigo_grado:
            errores["codigo_grado"] = "El codigo del grado es obligatorio."
        elif len(codigo_grado) > 20:
            errores["codigo_grado"] = "El codigo no debe superar 20 caracteres."

        if not nombre_grado:
            errores["nombre_grado"] = "El nombre del grado es obligatorio."
        elif len(nombre_grado) > 100:
            errores["nombre_grado"] = "El nombre no debe superar 100 caracteres."

        if descripcion and len(descripcion) > 255:
            errores["descripcion"] = "La descripcion no debe superar 255 caracteres."

        if orden_visualizacion <= 0:
            errores["orden_visualizacion"] = "El orden debe ser un entero mayor que cero."

        if estado not in ("activo", "inactivo"):
            errores["estado"] = "El estado debe ser activo o inactivo."

        grado_base = GRADOS_BASE_POR_CODIGO.get(codigo_grado) or GRADOS_BASE_POR_NOMBRE.get(nombre_grado.lower())
        if grado_base:
            codigo_grado = grado_base["codigo_grado"]
            nombre_grado = grado_base["nombre_grado"]
            orden_visualizacion = grado_base["orden_visualizacion"]
        else:
            errores["nombre_grado"] = "Solo se permiten los grados base Cuarto, Quinto y Sexto."

        datos_limpios = {
            "codigo_grado": codigo_grado,
            "nombre_grado": nombre_grado,
            "descripcion": descripcion,
            "orden_visualizacion": orden_visualizacion,
            "estado": estado,
        }
        return datos_limpios, errores

    # Funcion: obtener_todos
    # Descripcion:
    #   Consulta todos los grados registrados, con filtro opcional por estado e incluyendo total de secciones.
    #
    # Es llamada desde:
    #   La ruta GET /api/grados en backend/routes/grados_routes.py y el servicio obtenerGrados() de React.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta SELECT con LEFT JOIN hacia secciones.
    #
    # Parametros:
    #   estado: filtro opcional con valor activo o inactivo.
    #
    # Retorna:
    #   Una lista de diccionarios ordenada por orden_visualizacion y nombre_grado.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para que la ruta retorne HTTP 500 uniforme.
    @staticmethod
    def obtener_todos(estado=None):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            parametros = []
            filtro_estado = ""
            if estado:
                filtro_estado = "WHERE g.estado = %s"
                parametros.append(estado)

            cursor.execute(
                f"""
                SELECT
                    g.id_grado,
                    g.codigo_grado,
                    g.nombre_grado,
                    g.descripcion,
                    g.orden_visualizacion,
                    g.estado,
                    g.fecha_creacion,
                    g.fecha_modificacion,
                    SUM(CASE WHEN s.id_institucion_grado IS NULL THEN 1 ELSE 0 END) AS total_secciones
                FROM grados g
                LEFT JOIN secciones s ON s.id_grado = g.id_grado
                {filtro_estado}
                GROUP BY
                    g.id_grado,
                    g.codigo_grado,
                    g.nombre_grado,
                    g.descripcion,
                    g.orden_visualizacion,
                    g.estado,
                    g.fecha_creacion,
                    g.fecha_modificacion
                ORDER BY g.orden_visualizacion ASC, g.nombre_grado ASC
                """,
                tuple(parametros),
            )
            return [Grado.convertir_fila_a_diccionario(fila) for fila in cursor.fetchall()]
        finally:
            cursor.close()
            conexion.close()

    # Funcion: obtener_opciones_activas
    # Descripcion:
    #   Consulta solo los grados activos para el selector del formulario de secciones.
    #
    # Es llamada desde:
    #   La ruta GET /api/grados/opciones y desde obtenerOpcionesGrados() en React.
    #
    # Llama a:
    #   obtener_conexion() para consultar MySQL mediante SELECT directo.
    #
    # Parametros:
    #   No recibe parametros.
    #
    # Retorna:
    #   Una lista con id_grado, codigo_grado y nombre_grado.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que Flask responda HTTP 500 uniforme.
    @staticmethod
    def obtener_opciones_activas():
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT id_grado, codigo_grado, nombre_grado
                FROM grados
                WHERE estado = 'activo'
                ORDER BY orden_visualizacion ASC, nombre_grado ASC
                """
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conexion.close()

    # Funcion: obtener_por_id
    # Descripcion:
    #   Consulta un grado por su identificador, incluyendo el total de secciones relacionadas.
    #
    # Es llamada desde:
    #   Las rutas GET, PUT, PATCH y DELETE de /api/grados en grados_routes.py.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta SELECT con LEFT JOIN hacia secciones.
    #
    # Parametros:
    #   id_grado: identificador numerico del grado.
    #
    # Retorna:
    #   Un diccionario con el grado o None si no existe.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para que la ruta retorne HTTP 500 uniforme.
    @staticmethod
    def obtener_por_id(id_grado):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    g.id_grado,
                    g.codigo_grado,
                    g.nombre_grado,
                    g.descripcion,
                    g.orden_visualizacion,
                    g.estado,
                    g.fecha_creacion,
                    g.fecha_modificacion,
                    SUM(CASE WHEN s.id_institucion_grado IS NULL THEN 1 ELSE 0 END) AS total_secciones
                FROM grados g
                LEFT JOIN secciones s ON s.id_grado = g.id_grado
                WHERE g.id_grado = %s
                GROUP BY
                    g.id_grado,
                    g.codigo_grado,
                    g.nombre_grado,
                    g.descripcion,
                    g.orden_visualizacion,
                    g.estado,
                    g.fecha_creacion,
                    g.fecha_modificacion
                """,
                (id_grado,),
            )
            return Grado.convertir_fila_a_diccionario(cursor.fetchone())
        finally:
            cursor.close()
            conexion.close()

    # Funcion: existe
    # Descripcion:
    #   Verifica si un grado existe antes de crear o actualizar una seccion.
    #
    # Es llamada desde:
    #   El modelo Seccion en backend/models/seccion.py durante validaciones del CRUD de secciones.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta SELECT COUNT sobre grados.
    #
    # Parametros:
    #   id_grado: identificador numerico del grado.
    #
    # Retorna:
    #   True si el grado existe, False si no existe.
    #
    # Manejo de errores:
    #   Si ocurre un error de base de datos, se relanza para que Flask lo maneje.
    @staticmethod
    def existe(id_grado):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM grados WHERE id_grado = %s", (id_grado,))
            fila = cursor.fetchone()
            return fila["total"] > 0
        finally:
            cursor.close()
            conexion.close()

    # Funcion: existe_duplicado
    # Descripcion:
    #   Verifica duplicados de codigo o nombre antes de crear o actualizar un grado.
    #
    # Es llamada desde:
    #   crear() y actualizar() dentro de este modelo.
    #
    # Llama a:
    #   obtener_conexion() y ejecuta SELECT sobre grados.
    #
    # Parametros:
    #   codigo_grado, nombre_grado e id_grado_excluido opcional para ignorar el registro editado.
    #
    # Retorna:
    #   Un diccionario de errores si hay duplicados o un diccionario vacio si los datos estan disponibles.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para que Flask responda HTTP 500 uniforme.
    @staticmethod
    def existe_duplicado(codigo_grado, nombre_grado, id_grado_excluido=None):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            parametros = [codigo_grado, nombre_grado]
            filtro_exclusion = ""
            if id_grado_excluido:
                filtro_exclusion = "AND id_grado <> %s"
                parametros.append(id_grado_excluido)

            cursor.execute(
                f"""
                SELECT codigo_grado, nombre_grado
                FROM grados
                WHERE (codigo_grado = %s OR nombre_grado = %s)
                  {filtro_exclusion}
                """,
                tuple(parametros),
            )
            errores = {}
            for fila in cursor.fetchall():
                if fila["codigo_grado"] == codigo_grado:
                    errores["codigo_grado"] = "El codigo ya esta registrado."
                if fila["nombre_grado"] == nombre_grado:
                    errores["nombre_grado"] = "El nombre ya esta registrado."
            return errores
        finally:
            cursor.close()
            conexion.close()

    # Funcion: crear
    # Descripcion:
    #   Inserta un nuevo grado despues de validar datos y duplicados.
    #
    # Es llamada desde:
    #   La ruta POST /api/grados en backend/routes/grados_routes.py.
    #
    # Llama a:
    #   validar_datos(), existe_duplicado(), obtener_conexion() y obtener_por_id().
    #
    # Parametros:
    #   datos: JSON recibido por la ruta Flask.
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje, datos del grado y errores.
    #
    # Manejo de errores:
    #   Si falla MySQL, ejecuta rollback y relanza el error para respuesta HTTP 500 controlada.
    @staticmethod
    def crear(datos):
        datos_limpios, errores = Grado.validar_datos(datos)
        if errores:
            return "datos_invalidos", "Revise los datos ingresados.", None, errores

        errores_duplicado = Grado.existe_duplicado(datos_limpios["codigo_grado"], datos_limpios["nombre_grado"])
        if errores_duplicado:
            return "duplicado", "Ya existe un grado con el codigo o nombre ingresado.", None, errores_duplicado

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO grados (codigo_grado, nombre_grado, descripcion, orden_visualizacion, estado)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    datos_limpios["codigo_grado"],
                    datos_limpios["nombre_grado"],
                    datos_limpios["descripcion"],
                    datos_limpios["orden_visualizacion"],
                    datos_limpios["estado"],
                ),
            )
            conexion.commit()
            return "creado", "Grado creado correctamente.", Grado.obtener_por_id(cursor.lastrowid), {}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: actualizar
    # Descripcion:
    #   Actualiza un grado existente sin afectar sus secciones relacionadas.
    #
    # Es llamada desde:
    #   La ruta PUT /api/grados/<id_grado> en backend/routes/grados_routes.py.
    #
    # Llama a:
    #   obtener_por_id(), validar_datos(), existe_duplicado() y obtener_conexion().
    #
    # Parametros:
    #   id_grado: identificador del grado; datos: JSON recibido por Flask.
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje, grado actualizado y errores.
    #
    # Manejo de errores:
    #   Si falla MySQL, ejecuta rollback y relanza el error para respuesta HTTP 500 controlada.
    @staticmethod
    def actualizar(id_grado, datos):
        if not Grado.obtener_por_id(id_grado):
            return "no_existe", "El grado solicitado no existe.", None, {}

        datos_limpios, errores = Grado.validar_datos(datos)
        if errores:
            return "datos_invalidos", "Revise los datos ingresados.", None, errores

        errores_duplicado = Grado.existe_duplicado(
            datos_limpios["codigo_grado"],
            datos_limpios["nombre_grado"],
            id_grado,
        )
        if errores_duplicado:
            return "duplicado", "Ya existe un grado con el codigo o nombre ingresado.", None, errores_duplicado

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE grados
                SET codigo_grado = %s,
                    nombre_grado = %s,
                    descripcion = %s,
                    orden_visualizacion = %s,
                    estado = %s
                WHERE id_grado = %s
                """,
                (
                    datos_limpios["codigo_grado"],
                    datos_limpios["nombre_grado"],
                    datos_limpios["descripcion"],
                    datos_limpios["orden_visualizacion"],
                    datos_limpios["estado"],
                    id_grado,
                ),
            )
            conexion.commit()
            return "actualizado", "Grado actualizado correctamente.", Grado.obtener_por_id(id_grado), {}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: cambiar_estado
    # Descripcion:
    #   Activa o desactiva un grado sin eliminarlo y sin modificar sus secciones.
    #
    # Es llamada desde:
    #   La ruta PATCH /api/grados/<id_grado>/estado en backend/routes/grados_routes.py.
    #
    # Llama a:
    #   obtener_por_id() y obtener_conexion() para validar y actualizar MySQL.
    #
    # Parametros:
    #   id_grado: identificador del grado; estado: activo o inactivo.
    #
    # Retorna:
    #   Una tupla con codigo interno, mensaje, grado actualizado y errores.
    #
    # Manejo de errores:
    #   Si falla MySQL, ejecuta rollback y relanza el error para respuesta HTTP 500 controlada.
    @staticmethod
    def cambiar_estado(id_grado, estado):
        if estado not in ("activo", "inactivo"):
            return "datos_invalidos", "El estado debe ser activo o inactivo.", None, {"estado": "Valor no permitido."}
        if not Grado.obtener_por_id(id_grado):
            return "no_existe", "El grado solicitado no existe.", None, {}

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("UPDATE grados SET estado = %s WHERE id_grado = %s", (estado, id_grado))
            conexion.commit()
            return "actualizado", "Estado del grado actualizado correctamente.", Grado.obtener_por_id(id_grado), {}
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: tiene_relaciones_externas
    # Descripcion:
    #   Detecta tablas distintas de grados y secciones que tengan columna id_grado con registros asociados.
    #
    # Es llamada desde:
    #   eliminar() antes de borrar fisicamente un grado.
    #
    # Llama a:
    #   obtener_conexion() e information_schema para revisar columnas existentes.
    #
    # Parametros:
    #   id_grado: identificador del grado a revisar.
    #
    # Retorna:
    #   True si existen registros relacionados en otra tabla, False si no hay relaciones externas.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para que Flask responda HTTP 500 uniforme.
    @staticmethod
    def tiene_relaciones_externas(id_grado):
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT TABLE_NAME AS tabla
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND COLUMN_NAME = 'id_grado'
                  AND TABLE_NAME NOT IN ('grados', 'secciones')
                """
            )
            for fila in cursor.fetchall():
                tabla = fila["tabla"]
                cursor.execute(f"SELECT COUNT(*) AS total FROM `{tabla}` WHERE id_grado = %s", (id_grado,))
                if cursor.fetchone()["total"] > 0:
                    return True
            return False
        finally:
            cursor.close()
            conexion.close()

    @staticmethod
    def eliminar(id_grado):
        # Conserva compatibilidad interna: eliminar ahora solo desactiva y no borra fisicamente.
        grado = Grado.obtener_por_id(id_grado)
        if not grado:
            return "no_existe", "El grado solicitado no existe.", None, {}
        return Grado.cambiar_estado(id_grado, "inactivo")
