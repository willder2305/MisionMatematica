import random
import json

from generators.generador_numerico import generar_parametros
from generators.generador_opciones import generar_opciones
from generators.explicaciones_pedagogicas import generar_explicacion_pasos
from generators.validador_ejercicio import validar_ejercicio

MAX_INTENTOS_GENERACION = 10


def _renderizar(texto, parametros):
    # Sustituye marcadores {a}, {b}, {respuesta} con valores ya calculados.
    resultado = texto or ""
    for clave, valor in parametros.items():
        resultado = resultado.replace("{" + clave + "}", str(valor))
    return resultado


def _firma_parametros(parametros):
    # Firma parametros complejos sin asumir que todos sean enteros simples.
    return json.dumps(parametros or {}, sort_keys=True, default=str)


def _explicacion_determinista(parametros):
    """Construye una explicacion desde valores matematicos ya validados, sin IA ni eval."""
    operacion = parametros.get("operacion")
    respuesta = parametros.get("respuesta")
    if operacion == "suma":
        return f"Suma {parametros['expresion']}. El resultado es {respuesta}."
    if operacion == "resta":
        return f"Resta {parametros['b']} a {parametros['a']}: {parametros['a']} - {parametros['b']} = {respuesta}."
    if operacion == "multiplicacion":
        return f"Multiplica {parametros['a']} por {parametros['b']}: {parametros['a']} x {parametros['b']} = {respuesta}."
    if operacion == "division":
        return f"Busca cuantas veces cabe {parametros['b']} en {parametros['a']}: {parametros['a']} / {parametros['b']} = {respuesta}."
    if operacion == "potencia":
        return f"Multiplica {parametros['base']} por si mismo {parametros['exponente']} veces. El resultado es {respuesta}."
    if operacion == "raiz_cuadrada":
        return f"Busca el numero que multiplicado por si mismo da {parametros['radicando']}. Es {respuesta}."
    if operacion == "operaciones_combinadas":
        return f"Resuelve primero la multiplicacion en {parametros['expresion']}; despues suma y resta. El resultado es {respuesta}."
    if operacion and operacion.endswith("_fracciones"):
        return f"Opera las fracciones {parametros.get('f1')} {parametros.get('simbolo', '')} {parametros.get('f2', '')} y simplifica. El resultado es {respuesta}."
    if operacion and operacion.endswith("_decimales"):
        return f"Alinea los decimales y calcula {parametros['a']} {parametros['simbolo']} {parametros['b']}. El resultado es {respuesta}."
    if operacion == "porcentaje":
        return f"Calcula {parametros['porcentaje']}% de {parametros['cantidad']}: multiplica y divide entre 100. El resultado es {respuesta}."
    if operacion and operacion.startswith("regla_tres"):
        return f"Plantea la proporcion con {parametros['a']}, {parametros['b']} y {parametros['c']}; al despejar obtienes {respuesta}."
    if operacion == "conversion_fracciones":
        return f"Convierte la fraccion {parametros['fraccion']} a la forma solicitada. El resultado es {respuesta}."
    if operacion == "geometria":
        return f"Usa la formula de {parametros['calculo']} para {parametros['figura']} con {parametros['datos']}. El resultado es {respuesta}."
    return f"Revisa los datos de la operacion y calcula paso a paso. El resultado es {respuesta}."


def construir_ejercicio_desde_plantilla(plantilla, historial_parametros=None, seed=None):
    # Genera, valida y devuelve un ejercicio nuevo a partir de una plantilla publicada.
    historial_parametros = historial_parametros or []
    historial = {_firma_parametros(params) for params in historial_parametros}
    contextos_recientes = {params.get("context_key") for params in historial_parametros if params.get("context_key")}
    ultimo_error = None

    for intento in range(MAX_INTENTOS_GENERACION):
        semilla = seed if seed is not None and intento == 0 else random.randint(100000, 999999)
        rng = random.Random(semilla)
        try:
            parametros = generar_parametros(rng, plantilla["configuracion_json"])
            firma = _firma_parametros(parametros)
            if firma in historial and intento < MAX_INTENTOS_GENERACION - 1:
                continue
            if parametros.get("context_key") in contextos_recientes and intento < MAX_INTENTOS_GENERACION - 1:
                continue

            enunciado = parametros.get("enunciado_contextual") or _renderizar(plantilla["plantilla_enunciado"], parametros)
            explicacion_pasos = generar_explicacion_pasos(parametros)
            explicacion = _renderizar(plantilla.get("plantilla_explicacion"), parametros) or _explicacion_determinista(parametros)
            pista = _renderizar(plantilla.get("plantilla_pista"), parametros)
            opciones = generar_opciones(rng, parametros) if plantilla["tipo_respuesta"] == "seleccion_multiple" else []
            ejercicio = {
                "id_plantilla": plantilla["id_plantilla"],
                "id_tema": plantilla["id_tema"],
                "id_nivel": plantilla["id_nivel"],
                "enunciado": enunciado,
                "tipo_respuesta": plantilla["tipo_respuesta"],
                "respuesta_correcta": str(parametros["respuesta"]),
                "explicacion": explicacion,
                "explicacion_pasos": explicacion_pasos,
                "pista": pista,
                "opciones": opciones,
                "parametros": parametros,
                "semilla_generacion": semilla,
                "operacion": parametros["operacion"],
            }
            validar_ejercicio(ejercicio)
            return ejercicio
        except ValueError as error:
            ultimo_error = error

    raise ValueError(f"No se pudo generar un ejercicio valido: {ultimo_error}")
