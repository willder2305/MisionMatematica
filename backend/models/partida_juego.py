from db import obtener_conexion
from services.asignaciones_service import registrar_cierre_partida_asignada


PERSONAJES_PERMITIDOS = ("masculino", "femenino")
MAPAS_PERMITIDOS = ("bosque", "mapa_2", "mapa_3")
CASILLA_FINAL = 10


class PartidaJuego:
    # Funcion: crear_tabla_si_no_existe
    # Descripcion:
    #   Garantiza que exista la tabla minima partidas_juego antes de usar los endpoints del juego.
    #
    # Es llamada desde:
    #   Las rutas de backend/routes/juego_routes.py antes de crear, consultar o actualizar partidas.
    #
    # Llama a:
    #   obtener_conexion() para reutilizar la conexion MySQL 
    #
    # Parametros:
    #   No recibe parametros.
    #
    # Retorna:
    #   No retorna valores; crea la tabla si todavia no existe.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para que la ruta devuelva un error 500 controlado.
    @staticmethod
    def crear_tabla_si_no_existe():
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS partidas_juego (
                    id_partida INT AUTO_INCREMENT PRIMARY KEY,
                    id_usuario INT NULL,
                    personaje VARCHAR(50) NOT NULL,
                    mapa VARCHAR(100) NOT NULL,
                    casilla_actual INT NOT NULL DEFAULT 0,
                    total_correctos INT NOT NULL DEFAULT 0,
                    total_errores INT NOT NULL DEFAULT 0,
                    estado ENUM('en_curso', 'completada', 'abandonada') NOT NULL DEFAULT 'en_curso',
                    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin TIMESTAMP NULL DEFAULT NULL
                )
                """
            )
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

    # Funcion: convertir_fila_a_diccionario
    # Descripcion:
    #   Transforma una fila de MySQL en el formato JSON uniforme esperado por React.
    #
    # Es llamada desde:
    #   obtener_por_id(), crear(), registrar_correcto(), registrar_error() y abandonar().
    #
    # Llama a:
    #   No llama a servicios externos; solo formatea fechas y campos de la partida.
    #
    # Parametros:
    #   fila: diccionario retornado por mysql-connector.
    #
    # Retorna:
    #   Diccionario serializable o None si la fila no existe.
    #
    # Manejo de errores:
    #   Si recibe None, retorna None para que la ruta responda 404 sin romper serializacion.
    @staticmethod
    def convertir_fila_a_diccionario(fila):
        if fila is None:
            return None

        return {
            "id_partida": fila["id_partida"],
            "id_usuario": fila.get("id_usuario"),
            "personaje": fila["personaje"],
            "mapa": fila["mapa"],
            "casilla_actual": fila["casilla_actual"],
            "total_correctos": fila["total_correctos"],
            "total_errores": fila["total_errores"],
            "estado": fila["estado"],
            "fecha_inicio": fila["fecha_inicio"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_inicio") else None,
            "fecha_fin": fila["fecha_fin"].strftime("%Y-%m-%d %H:%M:%S") if fila.get("fecha_fin") else None,
        }

    # Funcion: validar_inicio
    # Descripcion:
    #   Valida los datos enviados al iniciar una partida visual del juego.
    #
    # Es llamada desde:
    #   crear() antes de insertar la partida.
    #
    # Llama a:
    #   No llama a otros servicios; usa las listas PERSONAJES_PERMITIDOS y MAPAS_PERMITIDOS.
    #
    # Parametros:
    #   datos: JSON recibido por POST /api/juego/partidas.
    #
    # Retorna:
    #   Tupla con datos normalizados y diccionario de errores.
    #
    # Manejo de errores:
    #   Acumula errores por campo para evitar que datos invalidos lleguen a MySQL.
    @staticmethod
    def validar_inicio(datos):
        personaje = (datos.get("personaje") or "").strip().lower()
        mapa = (datos.get("mapa") or "").strip().lower()
        errores = {}

        if personaje not in PERSONAJES_PERMITIDOS:
            errores["personaje"] = "Seleccione un personaje valido."
        if mapa not in MAPAS_PERMITIDOS:
            errores["mapa"] = "Seleccione un mapa disponible."

        return {"personaje": personaje, "mapa": mapa}, errores

    # Funcion: obtener_por_id
    # Descripcion:
    #   Consulta una partida del juego por su identificador.
    #
    # Es llamada desde:
    #   Las rutas GET, correcto, error y salir de backend/routes/juego_routes.py.
    #
    # Llama a:
    #   crear_tabla_si_no_existe() y obtener_conexion().
    #
    # Parametros:
    #   id_partida: identificador numerico recibido desde la ruta.
    #
    # Retorna:
    #   Diccionario con la partida o None si no existe.
    #
    # Manejo de errores:
    #   Si MySQL falla, relanza la excepcion para respuesta 500 uniforme.
    @staticmethod
    def obtener_por_id(id_partida):
        PartidaJuego.crear_tabla_si_no_existe()
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT id_partida, id_usuario, personaje, mapa, casilla_actual,
                       total_correctos, total_errores, estado, fecha_inicio, fecha_fin
                FROM partidas_juego
                WHERE id_partida = %s
                """,
                (id_partida,),
            )
            return PartidaJuego.convertir_fila_a_diccionario(cursor.fetchone())
        finally:
            cursor.close()
            conexion.close()

    # Funcion: crear
    # Descripcion:
    #   Crea una partida nueva en casilla 0 con contadores en cero y estado en_curso.
    #
    # Es llamada desde:
    #   La ruta POST /api/juego/partidas.
    #
    # Llama a:
    #   validar_inicio(), crear_tabla_si_no_existe(), obtener_conexion() y obtener_por_id().
    #
    # Parametros:
    #   datos: JSON con personaje y mapa.
    #
    # Retorna:
    #   Tupla con codigo interno, mensaje, partida creada y errores.
    #
    # Manejo de errores:
    #   Ejecuta rollback si falla el INSERT y relanza el error para que Flask responda 500.
    @staticmethod
    def crear(datos):
        datos_limpios, errores = PartidaJuego.validar_inicio(datos)
        if errores:
            return "datos_invalidos", "Revise la seleccion de personaje y mapa.", None, errores

        PartidaJuego.crear_tabla_si_no_existe()
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO partidas_juego
                    (id_usuario, personaje, mapa, casilla_actual, total_correctos, total_errores, estado)
                VALUES (NULL, %s, %s, 0, 0, 0, 'en_curso')
                """,
                (datos_limpios["personaje"], datos_limpios["mapa"]),
            )
            conexion.commit()
            return (
                "creado",
                "Partida iniciada correctamente.",
                PartidaJuego.obtener_por_id(cursor.lastrowid),
                {},
            )
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: validar_partida_en_curso
    # Descripcion:
    #   Revisa que una partida exista y permita registrar movimientos.
    #
    # Es llamada desde:
    #   registrar_correcto(), registrar_error() y abandonar() antes de modificar MySQL.
    #
    # Llama a:
    #   obtener_por_id() para leer el estado actual.
    #
    # Parametros:
    #   id_partida: identificador numerico de la partida.
    #
    # Retorna:
    #   Tupla con codigo interno, mensaje y partida actual.
    #
    # Manejo de errores:
    #   No captura errores de MySQL; deja que la ruta los convierta en 500 controlado.
    @staticmethod
    def validar_partida_en_curso(id_partida):
        partida = PartidaJuego.obtener_por_id(id_partida)
        if not partida:
            return "no_existe", "La partida solicitada no existe.", None
        if partida["estado"] != "en_curso":
            return "estado_incompatible", "La partida ya ha finalizado.", partida
        return "ok", "Partida lista para actualizar.", partida

    # Funcion: registrar_correcto
    # Descripcion:
    #   Registra una respuesta correcta temporal, avanza una sola casilla y completa al llegar a 10.
    #
    # Es llamada desde:
    #   La ruta POST /api/juego/partidas/<id_partida>/correcto.
    #
    # Llama a:
    #   validar_partida_en_curso(), obtener_conexion() y obtener_por_id().
    #
    # Parametros:
    #   id_partida: identificador recibido desde la URL.
    #
    # Retorna:
    #   Tupla con codigo interno, mensaje, partida actualizada y errores.
    #
    # Manejo de errores:
    #   Nunca permite superar la casilla 10; ejecuta rollback si falla la persistencia.
    @staticmethod
    def registrar_correcto(id_partida):
        codigo, mensaje, partida = PartidaJuego.validar_partida_en_curso(id_partida)
        if codigo != "ok":
            return codigo, mensaje, partida, {}
        if partida["casilla_actual"] >= CASILLA_FINAL:
            return "estado_incompatible", "La partida ya llego a la casilla final.", partida, {}

        nueva_casilla = min(partida["casilla_actual"] + 1, CASILLA_FINAL)
        nuevo_estado = "completada" if nueva_casilla == CASILLA_FINAL else "en_curso"

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE partidas_juego
                SET casilla_actual = %s,
                    total_correctos = total_correctos + 1,
                    estado = %s,
                    fecha_fin = CASE WHEN %s = 'completada' THEN CURRENT_TIMESTAMP ELSE fecha_fin END
                WHERE id_partida = %s
                """,
                (nueva_casilla, nuevo_estado, nuevo_estado, id_partida),
            )
            conexion.commit()
            return (
                "actualizado",
                "Movimiento registrado correctamente.",
                PartidaJuego.obtener_por_id(id_partida),
                {},
            )
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: registrar_error
    # Descripcion:
    #   Registra una respuesta incorrecta temporal sin mover la casilla actual.
    #
    # Es llamada desde:
    #   La ruta POST /api/juego/partidas/<id_partida>/error.
    #
    # Llama a:
    #   validar_partida_en_curso(), obtener_conexion() y obtener_por_id().
    #
    # Parametros:
    #   id_partida: identificador recibido desde la URL.
    #
    # Retorna:
    #   Tupla con codigo interno, mensaje, partida actualizada y errores.
    #
    # Manejo de errores:
    #   No modifica casilla_actual; ejecuta rollback si falla MySQL.
    @staticmethod
    def registrar_error(id_partida):
        codigo, mensaje, partida = PartidaJuego.validar_partida_en_curso(id_partida)
        if codigo != "ok":
            return codigo, mensaje, partida, {}

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE partidas_juego
                SET total_errores = total_errores + 1
                WHERE id_partida = %s
                """,
                (id_partida,),
            )
            conexion.commit()
            return (
                "actualizado",
                "Error registrado correctamente.",
                PartidaJuego.obtener_por_id(id_partida),
                {},
            )
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()

    # Funcion: abandonar
    # Descripcion:
    #   Marca una partida en curso como abandonada y registra fecha de finalizacion.
    #
    # Es llamada desde:
    #   La ruta POST /api/juego/partidas/<id_partida>/salir.
    #
    # Llama a:
    #   validar_partida_en_curso(), obtener_conexion() y obtener_por_id().
    #
    # Parametros:
    #   id_partida: identificador recibido desde la URL.
    #
    # Retorna:
    #   Tupla con codigo interno, mensaje, partida actualizada y errores.
    #
    # Manejo de errores:
    #   Ejecuta rollback si falla el UPDATE; no permite abandonar partidas ya finalizadas.
    @staticmethod
    def abandonar(id_partida):
        codigo, mensaje, partida = PartidaJuego.validar_partida_en_curso(id_partida)
        if codigo != "ok":
            return codigo, mensaje, partida, {}

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT id_usuario, id_asignacion, total_correctos, casilla_actual
                FROM partidas_juego
                WHERE id_partida = %s
                """,
                (id_partida,),
            )
            partida_actual = cursor.fetchone() or {}
            cursor.execute(
                """
                UPDATE partidas_juego
                SET estado = 'abandonada',
                    fecha_fin = CURRENT_TIMESTAMP,
                    fecha_ultima_actividad = CURRENT_TIMESTAMP
                WHERE id_partida = %s
                """,
                (id_partida,),
            )
            registrar_cierre_partida_asignada(
                partida_actual.get("id_asignacion"),
                partida_actual.get("id_usuario"),
                id_partida,
                "abandonada",
                int(partida_actual.get("total_correctos") or 0),
                int(partida_actual.get("casilla_actual") or 0),
                cursor,
            )
            conexion.commit()
            return (
                "actualizado",
                "Partida abandonada correctamente.",
                PartidaJuego.obtener_por_id(id_partida),
                {},
            )
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()
            conexion.close()
