from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from fractions import Fraction
from math import gcd
import json

from generators.restricciones_matematicas import obtener_entero, validar_variables
from generators.contextos_regla_tres import elegir_contexto


def _cfg(configuracion, nombre, defecto):
    # Lee una configuracion opcional sin dispersar valores magicos por los generadores.
    return configuracion.get(nombre, defecto)


def _fraccion_texto(valor):
    # Representa fracciones exactas en texto simple para enunciados y respuestas.
    valor = Fraction(valor)
    return str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"


def _decimal_texto(valor):
    # Normaliza Decimal sin ceros sobrantes para comparar y mostrar respuestas.
    valor = Decimal(valor)
    texto = format(valor.normalize(), "f")
    return "0" if texto == "-0" else texto


def _lista_config(valor, defecto):
    # Acepta listas reales o listas JSON serializadas por MySQL.
    if isinstance(valor, list):
        return valor
    if isinstance(valor, str):
        try:
            parsed = json.loads(valor)
            return parsed if isinstance(parsed, list) else defecto
        except json.JSONDecodeError:
            return defecto
    return defecto


def _obtener_decimal(rng, config_variable):
    # Genera un Decimal exacto moviendo enteros por escala decimal configurable.
    minimo = int(config_variable["min"])
    maximo = int(config_variable["max"])
    decimales = int(config_variable.get("decimales", 2))
    escala = Decimal(10) ** decimales
    return Decimal(rng.randint(minimo, maximo)) / escala


def _limites_decimal(config_variable):
    # Convierte el rango entero escalado de una plantilla a limites Decimal exactos.
    escala = Decimal(10) ** int(config_variable.get("decimales", 2))
    return Decimal(int(config_variable["min"])) / escala, Decimal(int(config_variable["max"])) / escala


def _obtener_fraccion(rng, configuracion, prefijo=""):
    # Construye una fracción con denominador distinto de cero y rango configurable.
    variables = configuracion.get("variables") or {}
    num_cfg = variables.get(f"{prefijo}numerador") or variables.get("numerador") or {"min": 1, "max": 9}
    den_cfg = variables.get(f"{prefijo}denominador") or variables.get("denominador") or {"min": 2, "max": 9}
    denominador = obtener_entero(rng, den_cfg)
    if denominador == 0:
        raise ValueError("Denominador cero no permitido.")

    minimo_numerador = int(num_cfg["min"])
    maximo_numerador = int(num_cfg["max"])
    if configuracion.get("fracciones_propias"):
        maximo_numerador = min(maximo_numerador, denominador - 1)
    candidatos = [
        numero
        for numero in range(minimo_numerador, maximo_numerador + 1)
        if numero > 0 and gcd(numero, denominador) == 1
    ]
    if not candidatos:
        raise ValueError("No hay una fracción simple compatible con la configuración.")
    numerador = rng.choice(candidatos)
    return Fraction(numerador, denominador)


def _respuesta_mixta(valor):
    # Convierte una fraccion impropia positiva a numero mixto simplificado.
    valor = Fraction(valor)
    entero = valor.numerator // valor.denominator
    resto = valor - entero
    return str(entero) if resto == 0 else f"{entero} {_fraccion_texto(resto)}"


def generar_suma(rng, configuracion):
    # Genera una suma controlada y calcula la respuesta.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    cantidad = rng.randint(int(_cfg(configuracion, "min_operandos", 2)), int(_cfg(configuracion, "max_operandos", 2)))
    operandos = [obtener_entero(rng, variables["a" if indice == 0 else "b"]) for indice in range(cantidad)]
    expresion = " + ".join(str(valor) for valor in operandos)
    return {"a": operandos[0], "b": operandos[1], "expresion": expresion, "respuesta": sum(operandos), "operacion": "suma"}


def generar_resta(rng, configuracion):
    # Genera una resta y evita negativos cuando la plantilla lo exige.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    a = obtener_entero(rng, variables["a"])
    b = obtener_entero(rng, variables["b"])
    if not configuracion.get("permitir_negativos", False) and a < b:
        a, b = b, a
    return {"a": a, "b": b, "respuesta": a - b, "operacion": "resta"}


def generar_multiplicacion(rng, configuracion):
    # Genera una multiplicacion usando los rangos del nivel seleccionado.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    a = obtener_entero(rng, variables["a"])
    b = obtener_entero(rng, variables["b"])
    return {"a": a, "b": b, "respuesta": a * b, "operacion": "multiplicacion"}


def generar_division(rng, configuracion):
    # Genera una division exacta construyendo dividendo = resultado * divisor.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    resultado = obtener_entero(rng, variables["resultado"])
    divisor = obtener_entero(rng, variables["divisor"])
    if divisor == 0:
        raise ValueError("Division entre cero no permitida.")
    dividendo = resultado * divisor
    return {"a": dividendo, "b": divisor, "respuesta": resultado, "operacion": "division"}


def generar_potencia(rng, configuracion):
    # Genera potencias enteras positivas, incluyendo base 10 cuando la config lo permite.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    usar_base_10 = configuracion.get("incluir_base_10") and rng.randint(1, 4) == 1
    base = 10 if usar_base_10 else obtener_entero(rng, variables["base"])
    exponente = obtener_entero(rng, variables["exponente"])
    if exponente < 0:
        raise ValueError("Exponentes negativos no permitidos.")
    return {"base": base, "exponente": exponente, "respuesta": base ** exponente, "operacion": "potencia"}


def generar_raiz_cuadrada(rng, configuracion):
    # Genera raices cuadradas exactas creando primero la raiz.
    validar_variables(configuracion)
    raiz = obtener_entero(rng, configuracion["variables"]["raiz"])
    radicando = raiz * raiz
    return {"radicando": radicando, "respuesta": raiz, "operacion": "raiz_cuadrada"}


def generar_operaciones_combinadas(rng, configuracion):
    # Crea expresiones estructuradas con jerarquía segura, sin eval ni exec.
    variables = configuracion.get("variables") or {"a": {"min": 2, "max": 12}, "b": {"min": 2, "max": 12}}
    a = obtener_entero(rng, variables.get("a", {"min": 2, "max": 12}))
    b = obtener_entero(rng, variables.get("b", {"min": 2, "max": 12}))
    c = obtener_entero(rng, variables.get("c", {"min": 2, "max": 12}))
    d = obtener_entero(rng, variables.get("d", {"min": 2, "max": 12}))
    cantidad_operaciones = int(configuracion.get("cantidad_operaciones", 3))
    if cantidad_operaciones <= 2:
        # Fácil usa dos operaciones directas para servir como introducción y refuerzo.
        producto = b * c
        respuesta = a + producto
        expresion = f"{a} + {b} x {c}"
        return {
            "a": a,
            "b": b,
            "c": c,
            "d": None,
            "producto": producto,
            "expresion": expresion,
            "respuesta": respuesta,
            "cantidad_operaciones": 2,
            "operacion": "operaciones_combinadas",
        }

    con_parentesis = bool(configuracion.get("con_parentesis"))
    if con_parentesis:
        producto = c * d
        respuesta = a + b * c - d
        expresion = f"{a} + ({b} x {c}) - {d}"
    else:
        producto = c * d
        respuesta = a + producto - b
        expresion = f"{a} + {c} x {d} - {b}"
    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "producto": producto,
        "expresion": expresion,
        "respuesta": respuesta,
        "cantidad_operaciones": 3,
        "operacion": "operaciones_combinadas",
    }


def generar_fraccion(rng, configuracion, operador):
    # Opera fracciones con Fraction para conservar exactitud y simplificación.
    if configuracion.get("denominadores_iguales"):
        variables = configuracion.get("variables") or {}
        denominador_cfg = variables.get("a_denominador") or variables.get("denominador") or {"min": 2, "max": 9}
        denominador = obtener_entero(rng, denominador_cfg)
        configuracion_compartida = {
            **configuracion,
            "variables": {
                **variables,
                "a_denominador": {"min": denominador, "max": denominador},
                "b_denominador": {"min": denominador, "max": denominador},
            },
        }
        f1 = _obtener_fraccion(rng, configuracion_compartida, "a_")
        f2 = _obtener_fraccion(rng, configuracion_compartida, "b_")
    else:
        f1 = _obtener_fraccion(rng, configuracion, "a_")
        f2 = _obtener_fraccion(rng, configuracion, "b_")
    if operador == "resta" and not configuracion.get("permitir_negativos", False) and f1 < f2:
        f1, f2 = f2, f1
    if operador == "suma":
        respuesta = f1 + f2
        simbolo = "+"
        operacion = "suma_fracciones"
    elif operador == "resta":
        respuesta = f1 - f2
        simbolo = "-"
        operacion = "resta_fracciones"
    elif operador == "multiplicacion":
        respuesta = f1 * f2
        simbolo = "x"
        operacion = "multiplicacion_fracciones"
    else:
        if f2 == 0:
            raise ValueError("Division de fracciones entre cero no permitida.")
        respuesta = f1 / f2
        simbolo = "/"
        operacion = "division_fracciones"
    return {
        "f1": _fraccion_texto(f1),
        "f2": _fraccion_texto(f2),
        "simbolo": simbolo,
        "respuesta": _fraccion_texto(respuesta),
        "forma_simplificada_requerida": bool(configuracion.get("forma_simplificada_requerida", True)),
        "operacion": operacion,
    }


def generar_decimal(rng, configuracion, operador):
    # Opera numeros Decimal exactos para evitar errores binarios de float.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    a = _obtener_decimal(rng, variables["a"])
    b = (
        Decimal(obtener_entero(rng, variables["b"]))
        if configuracion.get("segundo_entero")
        else _obtener_decimal(rng, variables["b"])
    )
    if operador == "resta" and not configuracion.get("permitir_negativos", False) and a < b:
        a, b = b, a
    if operador == "suma":
        respuesta = a + b
        simbolo = "+"
        operacion = "suma_decimales"
    elif operador == "resta":
        respuesta = a - b
        simbolo = "-"
        operacion = "resta_decimales"
    elif operador == "multiplicacion":
        respuesta = a * b
        simbolo = "x"
        operacion = "multiplicacion_decimales"
    else:
        # Construye el dividendo desde un cociente entero para no mostrar
        # aproximaciones silenciosas como si fueran respuestas exactas.
        minimo_a, maximo_a = _limites_decimal(variables["a"])
        resultado_cfg = variables.get("resultado")
        resultado_decimales = int(configuracion.get("resultado_decimales", 0))
        for _ in range(12):
            b = (
                Decimal(obtener_entero(rng, variables["b"]))
                if configuracion.get("divisor_entero")
                else _obtener_decimal(rng, variables["b"])
            )
            if b <= 0:
                continue
            if resultado_cfg and resultado_decimales:
                escala = Decimal(10) ** resultado_decimales
                respuesta = Decimal(rng.randint(int(resultado_cfg["min"]), int(resultado_cfg["max"]))) / escala
                a = b * respuesta
                if minimo_a <= a <= maximo_a:
                    break
                continue
            minimo_resultado = int((minimo_a / b).to_integral_value(rounding=ROUND_CEILING))
            maximo_resultado = int((maximo_a / b).to_integral_value(rounding=ROUND_FLOOR))
            minimo_resultado = max(1, minimo_resultado)
            if minimo_resultado <= maximo_resultado:
                respuesta = Decimal(rng.randint(minimo_resultado, maximo_resultado))
                a = b * respuesta
                break
        else:
            raise ValueError("No existe una division decimal exacta dentro del rango configurado.")
        simbolo = "/"
        operacion = "division_decimales"
    return {
        "a": _decimal_texto(a),
        "b": _decimal_texto(b),
        "simbolo": simbolo,
        "respuesta": _decimal_texto(respuesta),
        "operacion": operacion,
    }


def generar_porcentaje(rng, configuracion):
    # Calcula porcentajes con Decimal para conservar precision controlada.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    porcentajes = configuracion.get("porcentajes_permitidos") or []
    porcentaje = Decimal(rng.choice(porcentajes)) if porcentajes else Decimal(obtener_entero(rng, variables["porcentaje"]))
    cantidad = Decimal(obtener_entero(rng, variables["cantidad"]))
    if configuracion.get("resultado_entero"):
        for _ in range(20):
            cantidad = Decimal(obtener_entero(rng, variables["cantidad"]))
            if (cantidad * porcentaje) % Decimal(100) == 0:
                break
        else:
            raise ValueError("No existe un porcentaje fácil con resultado entero.")
    respuesta = (cantidad * porcentaje / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "cantidad": _decimal_texto(cantidad),
        "porcentaje": _decimal_texto(porcentaje),
        "respuesta": _decimal_texto(respuesta),
        "operacion": "porcentaje",
    }


def generar_regla_tres(rng, configuracion, tipo):
    # Genera proporcionalidad directa o inversa desde su estructura matematica.
    validar_variables(configuracion)
    variables = configuracion["variables"]
    a = obtener_entero(rng, variables["a"])
    c = obtener_entero(rng, variables["c"])
    if configuracion.get("relacion_entera"):
        factor = obtener_entero(rng, variables.get("factor", {"min": 1, "max": 5}))
        b = a * factor if tipo == "directa" else c * factor
    else:
        b = obtener_entero(rng, variables["b"])
    if a == 0 or c == 0:
        raise ValueError("Regla de tres con cero no permitida.")
    respuesta = Fraction(b * c, a) if tipo == "directa" else Fraction(a * b, c)
    context_key, plantilla_contexto = elegir_contexto(rng, tipo)
    return {
        "a": a,
        "b": b,
        "c": c,
        "tipo_proporcion": tipo,
        "respuesta": _fraccion_texto(respuesta),
        "operacion": f"regla_tres_{tipo}",
        "context_key": context_key,
        "template_key": f"regla_tres_{tipo}.{context_key}",
        "enunciado_contextual": plantilla_contexto.format(a=a, b=b, c=c),
    }


def generar_operaciones_combinadas_fracciones(rng, configuracion):
    # Combina fracciones con una expresion estructurada y resultado exacto.
    f1 = _obtener_fraccion(rng, configuracion, "a_")
    f2 = _obtener_fraccion(rng, configuracion, "b_")
    f3 = _obtener_fraccion(rng, configuracion, "c_")
    respuesta = f1 + (f2 * f3)
    expresion = f"{_fraccion_texto(f1)} + ({_fraccion_texto(f2)} x {_fraccion_texto(f3)})"
    return {
        "f1": _fraccion_texto(f1),
        "f2": _fraccion_texto(f2),
        "f3": _fraccion_texto(f3),
        "expresion": expresion,
        "respuesta": _fraccion_texto(respuesta),
        "forma_simplificada_requerida": True,
        "operacion": "operaciones_combinadas_fracciones",
    }


def generar_conversion_fraccion(rng, configuracion):
    # Crea conversiones controladas a entero, decimal terminante o numero mixto.
    subtipo = configuracion.get("subtipo") or rng.choice(["entero", "decimal", "mixta"])
    variables = configuracion.get("variables") or {}
    if subtipo == "entero":
        denominador = obtener_entero(rng, variables.get("denominador", {"min": 2, "max": 9}))
        resultado = obtener_entero(rng, variables.get("resultado", {"min": 2, "max": 12}))
        numerador = resultado * denominador
        fraccion = Fraction(numerador, denominador)
        fraccion_origen = f"{numerador}/{denominador}"
        respuesta = str(resultado)
    elif subtipo == "decimal":
        denominadores = configuracion.get("denominadores_permitidos") or [2, 4, 5, 8, 10, 20, 25, 50, 100]
        denominador = rng.choice(denominadores)
        numerador_cfg = variables.get("numerador", {"min": 1, "max": denominador - 1})
        maximo_numerador = min(int(numerador_cfg["max"]), denominador - 1) if configuracion.get("fracciones_propias") else int(numerador_cfg["max"])
        candidatos = list(range(int(numerador_cfg["min"]), maximo_numerador + 1))
        if not candidatos:
            raise ValueError("No hay una conversión decimal fácil compatible con la configuración.")
        numerador = rng.choice(candidatos)
        fraccion = Fraction(numerador, denominador)
        fraccion_origen = f"{numerador}/{denominador}"
        respuesta = _decimal_texto(Decimal(fraccion.numerator) / Decimal(fraccion.denominator))
    else:
        denominador = obtener_entero(rng, variables.get("denominador", {"min": 2, "max": 9}))
        entero = obtener_entero(rng, variables.get("entero", {"min": 1, "max": 6}))
        resto = obtener_entero(rng, variables.get("resto", {"min": 1, "max": denominador - 1}))
        numerador = entero * denominador + resto
        fraccion = Fraction(numerador, denominador)
        fraccion_origen = f"{numerador}/{denominador}"
        respuesta = _respuesta_mixta(fraccion)
    return {
        "fraccion": fraccion_origen,
        "subtipo_conversion": subtipo,
        "respuesta": respuesta,
        "forma_simplificada_requerida": subtipo == "mixta",
        "operacion": "conversion_fracciones",
    }


def generar_geometria(rng, configuracion):
    # Calcula area o perimetro desde figura/calculo declarados en la configuracion.
    figuras = _lista_config(configuracion.get("figuras"), ["cuadrado", "rectangulo", "triangulo"])
    calculos = _lista_config(configuracion.get("calculos"), ["area", "perimetro"])
    figura = rng.choice(figuras)
    calculo = rng.choice(calculos)
    minimo = int(configuracion.get("min_medida", 2))
    maximo = int(configuracion.get("max_medida", 15))
    pi = Decimal(str(configuracion.get("pi", "3.14")))

    if figura == "cuadrado":
        lado = obtener_entero(rng, {"min": minimo, "max": maximo})
        respuesta = lado * lado if calculo == "area" else 4 * lado
        datos = f"lado {lado}"
        medidas = {"lado": lado}
    elif figura == "rectangulo":
        base = obtener_entero(rng, {"min": minimo, "max": maximo})
        altura = obtener_entero(rng, {"min": minimo, "max": maximo})
        respuesta = base * altura if calculo == "area" else 2 * (base + altura)
        datos = f"base {base} y altura {altura}"
        medidas = {"base": base, "altura": altura}
    elif figura == "triangulo":
        base = obtener_entero(rng, {"min": minimo, "max": maximo})
        altura = obtener_entero(rng, {"min": minimo, "max": maximo})
        if calculo == "area" and configuracion.get("area_entera"):
            # En Fácil la base y la altura siempre producen un área entera.
            for _ in range(12):
                if (base * altura) % 2 == 0:
                    break
                altura = obtener_entero(rng, {"min": minimo, "max": maximo})
            else:
                raise ValueError("No se pudo construir un triángulo con área entera.")
        lado_igual = obtener_entero(rng, {"min": (base // 2) + 1, "max": maximo + 1})
        respuesta = Fraction(base * altura, 2) if calculo == "area" else base + (2 * lado_igual)
        datos = (
            f"base {base} y altura {altura}"
            if calculo == "area"
            else f"base {base} y lados {lado_igual}, {lado_igual}"
        )
        medidas = {"base": base, "altura": altura, "lado_igual": lado_igual}
    elif figura == "circulo":
        radio = obtener_entero(rng, {"min": minimo, "max": maximo})
        respuesta = pi * Decimal(radio * radio) if calculo == "area" else Decimal(2) * pi * Decimal(radio)
        datos = f"radio {radio} usando pi = 3.14"
        medidas = {"radio": radio, "pi": str(pi)}
    elif figura == "rombo":
        lado = obtener_entero(rng, {"min": minimo, "max": maximo})
        diagonal_mayor = obtener_entero(rng, {"min": minimo + 2, "max": maximo + 4})
        diagonal_menor = obtener_entero(rng, {"min": minimo, "max": maximo})
        respuesta = Fraction(diagonal_mayor * diagonal_menor, 2) if calculo == "area" else 4 * lado
        datos = f"lado {lado}, diagonal mayor {diagonal_mayor} y diagonal menor {diagonal_menor}"
        medidas = {"lado": lado, "diagonal_mayor": diagonal_mayor, "diagonal_menor": diagonal_menor}
    else:
        lados = obtener_entero(rng, {"min": 5, "max": 8})
        longitud = obtener_entero(rng, {"min": minimo, "max": maximo})
        perimetro = lados * longitud
        apotema = obtener_entero(rng, {"min": minimo, "max": maximo})
        respuesta = Fraction(perimetro * apotema, 2) if calculo == "area" else perimetro
        datos = f"{lados} lados, lado {longitud} y apotema {apotema}"
        medidas = {"lados": lados, "longitud": longitud, "apotema": apotema, "perimetro": perimetro}

    if isinstance(respuesta, Decimal):
        respuesta_texto = _decimal_texto(respuesta.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    elif isinstance(respuesta, Fraction):
        respuesta_texto = _fraccion_texto(respuesta)
    else:
        respuesta_texto = str(respuesta)
    return {
        "figura": figura,
        "calculo": calculo,
        "datos": datos,
        "medidas": medidas,
        "respuesta": respuesta_texto,
        "operacion": "geometria",
    }


OPERACIONES = {
    "suma": generar_suma,
    "resta": generar_resta,
    "multiplicacion": generar_multiplicacion,
    "division": generar_division,
    "potencia": generar_potencia,
    "raiz_cuadrada": generar_raiz_cuadrada,
    "operaciones_combinadas": generar_operaciones_combinadas,
    "suma_fracciones": lambda rng, cfg: generar_fraccion(rng, cfg, "suma"),
    "resta_fracciones": lambda rng, cfg: generar_fraccion(rng, cfg, "resta"),
    "multiplicacion_fracciones": lambda rng, cfg: generar_fraccion(rng, cfg, "multiplicacion"),
    "division_fracciones": lambda rng, cfg: generar_fraccion(rng, cfg, "division"),
    "suma_decimales": lambda rng, cfg: generar_decimal(rng, cfg, "suma"),
    "resta_decimales": lambda rng, cfg: generar_decimal(rng, cfg, "resta"),
    "multiplicacion_decimales": lambda rng, cfg: generar_decimal(rng, cfg, "multiplicacion"),
    "division_decimales": lambda rng, cfg: generar_decimal(rng, cfg, "division"),
    "porcentaje": generar_porcentaje,
    "regla_tres_directa": lambda rng, cfg: generar_regla_tres(rng, cfg, "directa"),
    "regla_tres_inversa": lambda rng, cfg: generar_regla_tres(rng, cfg, "inversa"),
    "operaciones_combinadas_fracciones": generar_operaciones_combinadas_fracciones,
    "conversion_fracciones": generar_conversion_fraccion,
    "geometria": generar_geometria,
}


def generar_parametros(rng, configuracion):
    # Ejecuta solo operaciones permitidas; nunca interpreta codigo desde MySQL.
    operacion = configuracion.get("operacion")
    if operacion not in OPERACIONES:
        raise ValueError("Operacion no soportada.")
    return OPERACIONES[operacion](rng, configuracion)
