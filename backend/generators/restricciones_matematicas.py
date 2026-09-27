def obtener_entero(rng, config_variable):
    # Genera un entero dentro del rango permitido por la plantilla.
    minimo = int(config_variable["min"])
    maximo = int(config_variable["max"])
    if minimo > maximo:
        raise ValueError("Rango invalido: min no puede ser mayor que max.")
    return rng.randint(minimo, maximo)


def validar_variables(configuracion):
    # Verifica que la configuracion tenga variables con rangos validos.
    variables = configuracion.get("variables") or {}
    if not variables:
        raise ValueError("La plantilla no define variables.")
    for nombre, config in variables.items():
        if "min" not in config or "max" not in config:
            raise ValueError(f"La variable {nombre} no define min y max.")
        if int(config["min"]) > int(config["max"]):
            raise ValueError(f"La variable {nombre} tiene rango invalido.")

