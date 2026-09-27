"""Audita y corrige datos históricos dañados por una importación Latin-1.

No participa en solicitudes HTTP ni en el frontend. Solo transforma valores que
coinciden con el patrón confirmado UTF-8 interpretado como Latin-1 y requiere
``--apply`` para escribir en MySQL.
"""

import argparse
import json
import sys
from pathlib import Path

# Permite ejecutar el archivo directamente dentro o fuera del contenedor.
RAIZ_BACKEND = Path(__file__).resolve().parents[1]
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from db import obtener_conexion


SENALES_MOJIBAKE = ("Ã", "Â", "\ufffd")
SENALES_REPARABLES = ("Ã", "Â")

# Columnas con textos que se muestran o influyen en preguntas, procedimientos y actividades.
TABLAS_AUDITADAS = (
    ("grados", "id_grado", ("codigo_grado", "nombre_grado", "descripcion"), ()),
    ("temas", "id_tema", ("nombre_tema", "descripcion"), ()),
    ("niveles_dificultad", "id_nivel", ("codigo", "nombre"), ()),
    ("ejercicios", "id_ejercicio", ("enunciado", "explicacion", "pista"), ("explicacion_pasos",)),
    ("opciones_ejercicio", "id_opcion", ("texto_opcion",), ()),
    (
        "plantillas_ejercicios",
        "id_plantilla",
        ("nombre", "descripcion", "plantilla_enunciado", "plantilla_explicacion", "plantilla_pista"),
        ("configuracion_json",),
    ),
    (
        "ejercicios_generados",
        "id_ejercicio_generado",
        ("enunciado", "explicacion", "pista"),
        ("explicacion_pasos", "opciones_json", "parametros_json"),
    ),
    ("reglas_adaptativas", "id_regla", ("codigo_regla", "nombre", "descripcion"), ("parametros_json",)),
    ("decisiones_agente", "id_decision", ("regla_aplicada", "motivo"), ("datos_entrada_json",)),
    ("asignaciones", "id_asignacion", ("nombre", "instrucciones"), ()),
    ("intentos_juego", "id_intento", ("respuesta_estudiante",), ("respuesta_api_json",)),
)


def tiene_mojibake(texto):
    """Detecta señales típicas del único daño de codificación auditado."""
    return isinstance(texto, str) and any(senal in texto for senal in SENALES_MOJIBAKE)


def recuperar_latin1_utf8(texto):
    """Recupera una cadena UTF-8 que fue interpretada una sola vez como Latin-1.

    Las cadenas sin el patrón confirmado se devuelven intactas. El carácter de
    reemplazo Unicode no es reversible y se conserva para revisión humana.
    """
    if not isinstance(texto, str) or not any(senal in texto for senal in SENALES_REPARABLES):
        return texto
    try:
        recuperado = texto.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return texto
    return recuperado if recuperado != texto and not tiene_mojibake(recuperado) else texto


def recuperar_json(valor):
    """Recorre JSON persistido y modifica únicamente cadenas reparables."""
    if isinstance(valor, str):
        return recuperar_latin1_utf8(valor)
    if isinstance(valor, list):
        return [recuperar_json(elemento) for elemento in valor]
    if isinstance(valor, dict):
        return {clave: recuperar_json(elemento) for clave, elemento in valor.items()}
    return valor


def _columnas_existentes(cursor, tabla):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        (tabla,),
    )
    return {fila["COLUMN_NAME"] for fila in cursor.fetchall()}


def _corregir_tabla(cursor, tabla, primaria, columnas_texto, columnas_json, aplicar):
    """Corrige una tabla declarada, ignorando columnas ausentes en esquemas antiguos."""
    disponibles = _columnas_existentes(cursor, tabla)
    columnas = [columna for columna in (*columnas_texto, *columnas_json) if columna in disponibles]
    if primaria not in disponibles or not columnas:
        return 0, 0

    seleccion = ", ".join(f"`{columna}`" for columna in (primaria, *columnas))
    cursor.execute(f"SELECT {seleccion} FROM `{tabla}`")
    filas = cursor.fetchall()
    corregidas = 0
    no_reversibles = 0

    for fila in filas:
        cambios = {}
        for columna in columnas_texto:
            if columna not in fila or fila[columna] is None:
                continue
            if "\ufffd" in fila[columna]:
                no_reversibles += 1
            corregido = recuperar_latin1_utf8(fila[columna])
            if corregido != fila[columna]:
                cambios[columna] = corregido

        for columna in columnas_json:
            valor = fila.get(columna)
            if valor is None:
                continue
            try:
                contenido = json.loads(valor) if isinstance(valor, str) else valor
            except json.JSONDecodeError:
                continue
            corregido = recuperar_json(contenido)
            if corregido != contenido:
                cambios[columna] = json.dumps(corregido, ensure_ascii=False, separators=(",", ":"))

        if not cambios:
            continue
        corregidas += 1
        if aplicar:
            asignaciones = ", ".join(f"`{columna}` = %s" for columna in cambios)
            cursor.execute(
                f"UPDATE `{tabla}` SET {asignaciones} WHERE `{primaria}` = %s",
                (*cambios.values(), fila[primaria]),
            )

    return corregidas, no_reversibles


def ejecutar(aplicar=False):
    """Ejecuta el diagnóstico o la migración transaccional y devuelve sus conteos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        resultados = {}
        reemplazos = 0
        for tabla, primaria, columnas_texto, columnas_json in TABLAS_AUDITADAS:
            corregidas, no_reversibles = _corregir_tabla(
                cursor, tabla, primaria, columnas_texto, columnas_json, aplicar
            )
            resultados[tabla] = corregidas
            reemplazos += no_reversibles
        if aplicar:
            conexion.commit()
        else:
            conexion.rollback()
        return resultados, reemplazos
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def main():
    """Exige confirmación explícita antes de modificar el contenido histórico."""
    parser = argparse.ArgumentParser(description="Audita mojibake Latin-1/UTF-8 en MySQL.")
    parser.add_argument("--apply", action="store_true", help="Confirma la actualización de filas detectadas.")
    args = parser.parse_args()
    resultados, reemplazos = ejecutar(aplicar=args.apply)
    modo = "aplicada" if args.apply else "simulada"
    print(f"Migración {modo}.")
    for tabla, cantidad in resultados.items():
        print(f"{tabla}: {cantidad} fila(s) reparable(s).")
    print(f"Valores con U+FFFD que requieren revisión humana: {reemplazos}.")


if __name__ == "__main__":
    main()
