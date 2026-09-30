"""Audita y, bajo confirmación explícita, reconcilia puntajes por tema físico.

La clasificación agrega después los temas equivalentes entre grados; este script
conserva los intentos y solo iguala cada fila almacenada a sus aciertos válidos.
"""

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script directamente desde backend/scripts o como módulo.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db import obtener_conexion


CONSULTA_DIFERENCIAS = """
SELECT COALESCE(h.id_usuario, pte.id_usuario) AS id_usuario,
       COALESCE(h.id_tema, pte.id_tema) AS id_tema,
       t.nombre_tema,
       COALESCE(pte.puntos_acumulados, 0) AS puntos_actuales,
       COALESCE(h.aciertos, 0) AS aciertos_validos,
       COALESCE(h.aciertos, 0) * 2 AS puntos_esperados
FROM progreso_tema_estudiante pte
LEFT JOIN (
    SELECT p.id_usuario, COALESCE(eg.id_tema, e.id_tema) AS id_tema,
           COUNT(DISTINCT i.id_intento) AS aciertos
    FROM intentos_juego i
    INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
    LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
    LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
    WHERE i.es_correcta = 1
      AND p.id_usuario IS NOT NULL
      AND COALESCE(eg.id_tema, e.id_tema) IS NOT NULL
    GROUP BY p.id_usuario, COALESCE(eg.id_tema, e.id_tema)
) h ON h.id_usuario = pte.id_usuario AND h.id_tema = pte.id_tema
INNER JOIN temas t ON t.id_tema = COALESCE(h.id_tema, pte.id_tema)
WHERE COALESCE(pte.puntos_acumulados, 0) <> COALESCE(h.aciertos, 0) * 2
UNION ALL
SELECT h.id_usuario, h.id_tema, t.nombre_tema, 0, h.aciertos, h.aciertos * 2
FROM (
    SELECT p.id_usuario, COALESCE(eg.id_tema, e.id_tema) AS id_tema,
           COUNT(DISTINCT i.id_intento) AS aciertos
    FROM intentos_juego i
    INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
    LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
    LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
    WHERE i.es_correcta = 1
      AND p.id_usuario IS NOT NULL
      AND COALESCE(eg.id_tema, e.id_tema) IS NOT NULL
    GROUP BY p.id_usuario, COALESCE(eg.id_tema, e.id_tema)
) h
INNER JOIN temas t ON t.id_tema = h.id_tema
LEFT JOIN progreso_tema_estudiante pte
    ON pte.id_usuario = h.id_usuario AND pte.id_tema = h.id_tema
WHERE pte.id_progreso_tema_estudiante IS NULL
ORDER BY id_usuario, id_tema
"""

RECONCILIAR = """
INSERT INTO progreso_tema_estudiante
    (id_usuario, id_tema, puntos_acumulados, aciertos_puntuados)
SELECT p.id_usuario, COALESCE(eg.id_tema, e.id_tema), COUNT(DISTINCT i.id_intento) * 2,
       COUNT(DISTINCT i.id_intento)
FROM intentos_juego i
INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
WHERE i.es_correcta = 1
  AND p.id_usuario IS NOT NULL
  AND COALESCE(eg.id_tema, e.id_tema) IS NOT NULL
GROUP BY p.id_usuario, COALESCE(eg.id_tema, e.id_tema)
ON DUPLICATE KEY UPDATE
    puntos_acumulados = VALUES(puntos_acumulados),
    aciertos_puntuados = VALUES(aciertos_puntuados)
"""


def obtener_diferencias(cursor):
    """Devuelve el reporte antes o después de reconciliar sin alterar datos."""
    cursor.execute(CONSULTA_DIFERENCIAS)
    return cursor.fetchall()


def main():
    """Muestra diferencias y solo escribe cuando se usa --apply explícitamente."""
    parser = argparse.ArgumentParser(description="Reconcilia puntuaciones desde intentos correctos.")
    parser.add_argument("--apply", action="store_true", help="Aplica SET lógico idempotente a los puntajes.")
    args = parser.parse_args()
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        antes = obtener_diferencias(cursor)
        print(f"Diferencias detectadas: {len(antes)}")
        for fila in antes:
            print(fila)
        if not args.apply:
            return
        cursor.execute(RECONCILIAR)
        conexion.commit()
        despues = obtener_diferencias(cursor)
        print(f"Diferencias restantes: {len(despues)}")
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    main()
