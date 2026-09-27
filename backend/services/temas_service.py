from db import obtener_conexion


def obtener_temas_por_grado(id_grado):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id_tema, id_grado, nombre_tema, descripcion, estado
            FROM temas
            WHERE id_grado = %s
              AND estado = 'activo'
            ORDER BY nombre_tema ASC
            """,
            (id_grado,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

