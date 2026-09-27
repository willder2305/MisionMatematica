"""Procedimientos breves y deterministas para ejercicios generados."""

from fractions import Fraction
from math import gcd


def _fraccion_texto(valor):
    valor = Fraction(valor)
    return str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"


def _pasos_fracciones(parametros, operador):
    primera = Fraction(str(parametros["f1"]))
    segunda = Fraction(str(parametros["f2"]))
    respuesta = str(parametros["respuesta"])
    if operador in ("suma", "resta"):
        comun = primera.denominator * segunda.denominator // gcd(primera.denominator, segunda.denominator)
        primera_equivalente = Fraction(primera.numerator * (comun // primera.denominator), comun)
        segunda_equivalente = Fraction(segunda.numerator * (comun // segunda.denominator), comun)
        simbolo = "+" if operador == "suma" else "−"
        bruto = Fraction(
            primera_equivalente.numerator + segunda_equivalente.numerator
            if operador == "suma"
            else primera_equivalente.numerator - segunda_equivalente.numerator,
            comun,
        )
        pasos = []
        if primera.denominator != comun:
            pasos.append(f"{_fraccion_texto(primera)} = {_fraccion_texto(primera_equivalente)}.")
        if segunda.denominator != comun:
            pasos.append(f"{_fraccion_texto(segunda)} = {_fraccion_texto(segunda_equivalente)}.")
        pasos.append(
            f"{_fraccion_texto(primera_equivalente)} {simbolo} {_fraccion_texto(segunda_equivalente)} = {_fraccion_texto(bruto)}."
        )
        if _fraccion_texto(bruto) != respuesta:
            pasos.append(f"Simplifica: {_fraccion_texto(bruto)} = {respuesta}.")
        return pasos
    if operador == "multiplicacion":
        numerador = primera.numerator * segunda.numerator
        denominador = primera.denominator * segunda.denominator
        bruto = Fraction(numerador, denominador)
        bruto_texto = str(numerador) if denominador == 1 else f"{numerador}/{denominador}"
        pasos = [
            f"{primera.numerator} × {segunda.numerator} = {numerador}.",
            f"{primera.denominator} × {segunda.denominator} = {denominador}.",
            f"{bruto_texto} = {respuesta}.",
        ]
        return pasos
    invertida = Fraction(segunda.denominator, segunda.numerator)
    bruto = primera * invertida
    pasos = [
        f"Invierte la segunda fracción: {_fraccion_texto(segunda)} se vuelve {_fraccion_texto(invertida)}.",
        f"{_fraccion_texto(primera)} × {_fraccion_texto(invertida)} = {_fraccion_texto(bruto)}.",
    ]
    if _fraccion_texto(bruto) != respuesta:
        pasos.append(f"Simplifica: {_fraccion_texto(bruto)} = {respuesta}.")
    return pasos


def _pasos_geometria(parametros):
    medidas = parametros.get("medidas") or {}
    figura = parametros.get("figura")
    calculo = parametros.get("calculo")
    respuesta = parametros["respuesta"]
    if figura == "cuadrado":
        lado = medidas["lado"]
        return [f"{calculo.title()} = {lado} × {lado}." if calculo == "area" else f"Perímetro = 4 × {lado}.", f"Resultado: {respuesta}."]
    if figura == "rectangulo":
        base, altura = medidas["base"], medidas["altura"]
        formula = f"{base} × {altura}" if calculo == "area" else f"2 × ({base} + {altura})"
        return [f"{calculo.title()} = {formula}.", f"Resultado: {respuesta}."]
    if figura == "triangulo":
        if calculo == "area":
            return [f"Área = ({medidas['base']} × {medidas['altura']}) ÷ 2.", f"Resultado: {respuesta}."]
        return [f"Perímetro = {medidas['base']} + {medidas['lado_igual']} + {medidas['lado_igual']}.", f"Resultado: {respuesta}."]
    if figura == "circulo":
        radio = medidas["radio"]
        formula = f"3.14 × {radio}²" if calculo == "area" else f"2 × 3.14 × {radio}"
        return [f"{calculo.title()} = {formula}.", f"Resultado: {respuesta}."]
    if figura == "rombo":
        if calculo == "area":
            return [f"Área = ({medidas['diagonal_mayor']} × {medidas['diagonal_menor']}) ÷ 2.", f"Resultado: {respuesta}."]
        return [f"Perímetro = 4 × {medidas['lado']}.", f"Resultado: {respuesta}."]
    if calculo == "area":
        return [f"Perímetro = {medidas['lados']} × {medidas['longitud']} = {medidas['perimetro']}.", f"Área = ({medidas['perimetro']} × {medidas['apotema']}) ÷ 2 = {respuesta}."]
    return [f"Perímetro = {medidas['lados']} × {medidas['longitud']}.", f"Resultado: {respuesta}."]


def generar_explicacion_pasos(parametros):
    # Usa únicamente parámetros que ya generó y validó el ejercicio.
    operacion = parametros.get("operacion")
    respuesta = str(parametros.get("respuesta"))
    if operacion == "suma":
        return [f"{parametros['expresion']} = {respuesta}."]
    if operacion == "resta":
        return [f"{parametros['a']} − {parametros['b']} = {respuesta}."]
    if operacion == "multiplicacion":
        a, b = parametros["a"], parametros["b"]
        if 10 <= b <= 99:
            decenas, unidades = (b // 10) * 10, b % 10
            return [f"{a} × {decenas} = {a * decenas}.", f"{a} × {unidades} = {a * unidades}.", f"{a * decenas} + {a * unidades} = {respuesta}."]
        return [f"{a} × {b} = {respuesta}."]
    if operacion == "division":
        return [f"{parametros['a']} ÷ {parametros['b']} = {respuesta}.", f"Comprueba: {parametros['b']} × {respuesta} = {parametros['a']}."]
    if operacion == "potencia":
        factores = " × ".join([str(parametros["base"])] * parametros["exponente"])
        return [f"{parametros['base']}^{parametros['exponente']} = {factores}.", f"Resultado: {respuesta}."]
    if operacion == "raiz_cuadrada":
        return [f"{respuesta} × {respuesta} = {parametros['radicando']}.", f"Por eso √{parametros['radicando']} = {respuesta}."]
    if operacion == "operaciones_combinadas":
        if parametros.get("cantidad_operaciones") == 2:
            return [
                f"Primero: {parametros['b']} × {parametros['c']} = {parametros['producto']}.",
                f"Luego: {parametros['a']} + {parametros['producto']} = {respuesta}.",
            ]
        termina = parametros["d"] if f"({parametros['b']} x {parametros['c']})" in parametros["expresion"] else parametros["b"]
        return [f"Primero: {parametros['c']} × {parametros['d']} = {parametros['producto']}.", f"Luego: {parametros['a']} + {parametros['producto']} − {termina} = {respuesta}."]
    if operacion in ("suma_fracciones", "resta_fracciones", "multiplicacion_fracciones", "division_fracciones"):
        return _pasos_fracciones(parametros, operacion.split("_", 1)[0])
    if operacion.endswith("_decimales"):
        return [f"{parametros['a']} {parametros['simbolo']} {parametros['b']} = {respuesta}."]
    if operacion == "porcentaje":
        return [f"{parametros['porcentaje']}% = {parametros['porcentaje']}/100.", f"{parametros['porcentaje']}/100 × {parametros['cantidad']} = {respuesta}."]
    if operacion == "regla_tres_directa":
        intermedio = Fraction(parametros["b"] * parametros["c"], parametros["a"])
        return [f"x = ({parametros['c']} × {parametros['b']}) ÷ {parametros['a']}.", f"x = {_fraccion_texto(intermedio)} = {respuesta}."]
    if operacion == "regla_tres_inversa":
        return [f"{parametros['a']} × {parametros['b']} = {parametros['c']} × x.", f"x = ({parametros['a']} × {parametros['b']}) ÷ {parametros['c']} = {respuesta}."]
    if operacion == "operaciones_combinadas_fracciones":
        parcial = Fraction(str(parametros["f2"])) * Fraction(str(parametros["f3"]))
        return [f"Primero: {parametros['f2']} × {parametros['f3']} = {_fraccion_texto(parcial)}.", f"Luego: {parametros['f1']} + {_fraccion_texto(parcial)} = {respuesta}."]
    if operacion == "conversion_fracciones":
        fraccion = Fraction(str(parametros["fraccion"]))
        if parametros["subtipo_conversion"] == "mixta":
            entero, resto = divmod(fraccion.numerator, fraccion.denominator)
            return [f"{fraccion.numerator} ÷ {fraccion.denominator} = {entero} y sobran {resto}.", f"{parametros['fraccion']} = {respuesta}."]
        return [f"{fraccion.numerator} ÷ {fraccion.denominator} = {respuesta}."]
    if operacion == "geometria":
        return _pasos_geometria(parametros)
    return [f"Resuelve la operación paso a paso para obtener {respuesta}."]
