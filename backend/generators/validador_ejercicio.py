OPERACIONES_PERMITIDAS = {
    "suma",
    "resta",
    "multiplicacion",
    "division",
    "potencia",
    "raiz_cuadrada",
    "operaciones_combinadas",
    "suma_fracciones",
    "resta_fracciones",
    "multiplicacion_fracciones",
    "division_fracciones",
    "suma_decimales",
    "resta_decimales",
    "multiplicacion_decimales",
    "division_decimales",
    "porcentaje",
    "regla_tres_directa",
    "regla_tres_inversa",
    "operaciones_combinadas_fracciones",
    "conversion_fracciones",
    "geometria",
}


def validar_ejercicio(ejercicio):
    # Comprueba que el ejercicio generado sea seguro y matematicamente valido.
    if not ejercicio.get("enunciado"):
        raise ValueError("El enunciado no puede estar vacio.")
    if ejercicio.get("operacion") not in OPERACIONES_PERMITIDAS:
        raise ValueError("Operacion no permitida.")
    if ejercicio.get("respuesta_correcta") in (None, ""):
        raise ValueError("Respuesta correcta invalida.")
    pasos = ejercicio.get("explicacion_pasos")
    if not isinstance(pasos, list) or not 1 <= len(pasos) <= 4 or any(not str(paso).strip() for paso in pasos):
        raise ValueError("El procedimiento debe contener entre uno y cuatro pasos breves.")

    parametros = ejercicio.get("parametros") or {}
    if ejercicio["operacion"] == "division":
        divisor = int(parametros.get("b", 0))
        dividendo = int(parametros.get("a", 0))
        if divisor == 0 or dividendo % divisor != 0:
            raise ValueError("La division generada no es exacta.")
    if ejercicio["operacion"].endswith("_fracciones"):
        for clave in ("f1", "f2", "f3"):
            fraccion = str(parametros.get(clave, ""))
            if "/" in fraccion and fraccion.split("/", 1)[1] == "0":
                raise ValueError("No se permiten fracciones con denominador cero.")
    if ejercicio["operacion"] in ("regla_tres_directa", "regla_tres_inversa"):
        tipo = parametros.get("tipo_proporcion")
        esperado = "directa" if ejercicio["operacion"].endswith("directa") else "inversa"
        if tipo != esperado:
            raise ValueError("La regla de tres no coincide con su tipo estructural.")
    if ejercicio["operacion"] == "geometria":
        if parametros.get("figura") not in ("cuadrado", "rectangulo", "triangulo", "circulo", "rombo", "poligono"):
            raise ValueError("Figura geometrica no permitida.")
        if parametros.get("calculo") not in ("area", "perimetro"):
            raise ValueError("Calculo geometrico no permitido.")

    if ejercicio.get("tipo_respuesta") == "seleccion_multiple":
        opciones = ejercicio.get("opciones") or []
        textos = [opcion["texto"] for opcion in opciones]
        if len(opciones) != 4:
            raise ValueError("La seleccion multiple debe tener 4 opciones.")
        if len(set(textos)) != 4:
            raise ValueError("Las opciones no pueden repetirse.")
        if str(ejercicio["respuesta_correcta"]) not in textos:
            raise ValueError("La respuesta correcta debe estar incluida en opciones.")

    return True
