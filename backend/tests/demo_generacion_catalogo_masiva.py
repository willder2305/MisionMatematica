import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import obtener_conexion
from generators.generador_ejercicios import construir_ejercicio_desde_plantilla
from services.plantillas_service import _serializar_plantilla


def main():
    # Genera 100 ejercicios por plantilla de catalogo publicada en la base local.
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT p.*
            FROM plantillas_ejercicios p
            WHERE p.nombre LIKE '% catalogo'
              AND p.estado = 'publicada'
            ORDER BY p.id_plantilla ASC
            """
        )
        plantillas = [_serializar_plantilla(fila) for fila in cursor.fetchall()]
    finally:
        cursor.close()
        conexion.close()

    total = 0
    errores = []
    for plantilla in plantillas:
        historial = []
        for seed in range(100):
            try:
                ejercicio = construir_ejercicio_desde_plantilla(
                    plantilla,
                    historial_parametros=historial,
                    seed=seed,
                )
                historial.append(ejercicio["parametros"])
                total += 1
            except Exception as error:
                errores.append((plantilla["id_plantilla"], plantilla["nombre"], seed, str(error)))
                break

    print({
        "plantillas": len(plantillas),
        "ejercicios_generados": total,
        "errores": errores[:5],
    })
    if errores:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
