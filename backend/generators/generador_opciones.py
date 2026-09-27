from decimal import Decimal, InvalidOperation
from fractions import Fraction


def _decimal_texto(valor):
    # Muestra decimales sin ceros sobrantes y con punto como separador interno.
    texto = format(Decimal(valor).normalize(), "f")
    return "0" if texto == "-0" else texto


def _fraccion_texto(valor):
    # Muestra fracciones simplificadas para evitar opciones equivalentes ambiguas.
    valor = Fraction(valor)
    return str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"


def _parse_numero(valor):
    # Intenta interpretar enteros, decimales, fracciones y mixtos sin usar eval.
    texto = str(valor).strip().replace(",", ".")
    if " " in texto and "/" in texto:
        entero, fraccion = texto.split(" ", 1)
        signo = -1 if entero.startswith("-") else 1
        return Fraction(int(entero), 1) + signo * Fraction(fraccion)
    if "/" in texto:
        return Fraction(texto)
    return Decimal(texto)


def _clave(valor):
    # Normaliza matematicamente para no ofrecer dos opciones equivalentes.
    try:
        numero = _parse_numero(valor)
        if isinstance(numero, Fraction):
            return f"f:{numero.numerator}/{numero.denominator}"
        return f"d:{_decimal_texto(numero)}"
    except (ValueError, InvalidOperation, ZeroDivisionError):
        return f"t:{str(valor).strip().lower()}"


def _formatear_like(correcta, valor):
    # Conserva el estilo de respuesta correcta: fraccion, decimal o entero.
    correcta_texto = str(correcta)
    if "/" in correcta_texto:
        return _fraccion_texto(Fraction(valor))
    if "." in correcta_texto or "," in correcta_texto:
        return _decimal_texto(Decimal(valor))
    return str(int(valor))


def _agregar(opciones, usado, valor, correcta):
    # Agrega distractores no negativos, no duplicados y distintos de la correcta.
    texto = str(valor)
    clave = _clave(texto)
    if clave == _clave(correcta) or clave in usado:
        return False
    try:
        numero = _parse_numero(texto)
        if numero < 0:
            return False
    except (ValueError, InvalidOperation, ZeroDivisionError):
        pass
    usado.add(clave)
    opciones.append(texto)
    return True


def generar_opciones(rng, parametros):
    # Crea una correcta y tres distractores plausibles segun el tipo de respuesta.
    correcta = str(parametros["respuesta"])
    opciones = []
    usado = {_clave(correcta)}

    try:
        numero = _parse_numero(correcta)
        pasos = [1, 2, 5, 10]
        if isinstance(numero, Fraction):
            base = numero
            candidatos = [
                base + Fraction(1, max(2, base.denominator)),
                base - Fraction(1, max(2, base.denominator)),
                Fraction(base.numerator + 1, base.denominator),
                Fraction(max(0, base.numerator - 1), base.denominator),
                base + 1,
                base - 1,
            ]
        else:
            base = Decimal(numero)
            candidatos = [base + Decimal(paso) for paso in pasos] + [base - Decimal(paso) for paso in pasos]
            if "." in correcta or "," in correcta:
                candidatos.extend([base + Decimal("0.1"), base - Decimal("0.1"), base * Decimal("10")])
        for candidato in candidatos:
            _agregar(opciones, usado, _formatear_like(correcta, candidato), correcta)
            if len(opciones) == 3:
                break
        while len(opciones) < 3:
            variacion = rng.randint(1, 12)
            signo = -1 if rng.randint(0, 1) == 0 else 1
            _agregar(opciones, usado, _formatear_like(correcta, base + signo * variacion), correcta)
    except (ValueError, InvalidOperation, ZeroDivisionError):
        for sufijo in (" aproximado", " sin simplificar", " invertido", " incompleto"):
            _agregar(opciones, usado, f"{correcta}{sufijo}", correcta)

    valores = opciones[:3] + [correcta]
    rng.shuffle(valores)
    return [{"id": chr(97 + indice), "texto": str(valor)} for indice, valor in enumerate(valores)]
