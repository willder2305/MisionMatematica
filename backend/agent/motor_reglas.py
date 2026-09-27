ACCION_AUMENTAR = "aumentar"
ACCION_MANTENER = "mantener"
ACCION_REDUCIR = "reducir"
ACCION_REFORZAR = "reforzar"


class MotorReglasAdaptativo:
    # Ordena niveles y reglas activas para decidir el siguiente ajuste.
    def __init__(self, niveles, reglas=None):
        self.niveles = sorted(niveles, key=lambda nivel: nivel["orden_nivel"])
        self.reglas = sorted(reglas or [], key=lambda regla: regla.get("prioridad", 999))

    # Evalua las metricas del estudiante y retorna aumentar, mantener, reducir o reforzar.
    def decidir(self, metricas, nivel_actual):
        contexto = {
            "metricas": metricas,
            "nivel_actual": nivel_actual,
            "accion": ACCION_MANTENER,
            "nivel_recomendado": nivel_actual,
            "recomendar_refuerzo": False,
            "codigo_regla": "fallback_mantener",
            "mensaje": "Continua en el mismo nivel.",
            "explicacion": "No se activo una regla de ajuste.",
        }

        for regla in self.reglas:
            codigo = regla.get("codigo_regla")
            parametros = regla.get("parametros_json") or {}
            if codigo == "dos_errores_consecutivos" and self._dos_errores(metricas, parametros):
                return self._aplicar_reduccion_o_refuerzo(contexto, regla, "Tiene dos errores consecutivos.")
            if codigo == "tres_aciertos_consecutivos" and self._tres_aciertos(metricas, parametros):
                return self._aplicar_aumento(contexto, regla, "Tiene tres aciertos consecutivos.")
            if codigo == "porcentaje_bajo" and self._porcentaje_bajo(metricas, parametros):
                return self._aplicar_reduccion_o_refuerzo(contexto, regla, "El porcentaje de aciertos esta por debajo del minimo.")
            if codigo == "porcentaje_alto" and self._porcentaje_alto(metricas, parametros):
                return self._aplicar_aumento(contexto, regla, "El porcentaje de aciertos supera el objetivo.")
            if codigo == "rango_estable" and self._rango_estable(metricas, parametros):
                return self._mantener(contexto, regla, "El rendimiento esta dentro del rango estable.")

        return contexto

    # Detecta exactamente dos errores seguidos para evitar castigar varias veces la misma racha.
    def _dos_errores(self, metricas, parametros):
        limite = int(parametros.get("incorrectas_consecutivas", 2))
        return metricas.get("incorrectas_consecutivas", 0) == limite

    # Detecta exactamente tres aciertos seguidos para subir una sola vez por racha.
    def _tres_aciertos(self, metricas, parametros):
        limite = int(parametros.get("correctas_consecutivas", 3))
        return metricas.get("correctas_consecutivas", 0) == limite

    # Detecta bajo rendimiento con minimo de intentos y cooldown de reduccion.
    def _porcentaje_bajo(self, metricas, parametros):
        min_intentos = int(parametros.get("min_intentos", 5))
        porcentaje_maximo = float(parametros.get("porcentaje_maximo", 60))
        cooldown = int(parametros.get("cooldown_intentos", 3))
        return (
            metricas.get("total_intentos", 0) >= min_intentos
            and metricas.get("porcentaje_aciertos", 0) < porcentaje_maximo
            and not self._accion_reciente(metricas, ACCION_REDUCIR, cooldown)
            and not self._accion_reciente(metricas, ACCION_REFORZAR, cooldown)
        )

    # Detecta alto rendimiento con minimo de intentos y cooldown de aumento.
    def _porcentaje_alto(self, metricas, parametros):
        min_intentos = int(parametros.get("min_intentos", 5))
        porcentaje_minimo = float(parametros.get("porcentaje_minimo", 80))
        cooldown = int(parametros.get("cooldown_intentos", 3))
        return (
            metricas.get("total_intentos", 0) >= min_intentos
            and metricas.get("porcentaje_aciertos", 0) > porcentaje_minimo
            and not self._accion_reciente(metricas, ACCION_AUMENTAR, cooldown)
        )

    # Mantiene nivel cuando el porcentaje queda en el rango esperado.
    def _rango_estable(self, metricas, parametros):
        min_intentos = int(parametros.get("min_intentos", 5))
        porcentaje_minimo = float(parametros.get("porcentaje_minimo", 60))
        porcentaje_maximo = float(parametros.get("porcentaje_maximo", 80))
        porcentaje = metricas.get("porcentaje_aciertos", 0)
        return metricas.get("total_intentos", 0) >= min_intentos and porcentaje_minimo <= porcentaje <= porcentaje_maximo

    # Busca si una accion ya ocurrio en las decisiones recientes.
    def _accion_reciente(self, metricas, accion, limite):
        recientes = metricas.get("decisiones_recientes", [])[:limite]
        return any(decision.get("accion") == accion for decision in recientes)

    # Calcula el siguiente nivel superior sin pasar del maximo.
    def _aplicar_aumento(self, contexto, regla, explicacion):
        siguiente = self._nivel_superior(contexto["nivel_actual"])
        accion = ACCION_AUMENTAR if siguiente["id_nivel"] != contexto["nivel_actual"]["id_nivel"] else ACCION_MANTENER
        return {
            **contexto,
            "accion": accion,
            "nivel_recomendado": siguiente,
            "codigo_regla": regla["codigo_regla"],
            "mensaje": "Sube la dificultad." if accion == ACCION_AUMENTAR else "Se mantiene en el nivel maximo.",
            "explicacion": explicacion,
        }

    # Calcula reduccion de nivel o refuerzo si ya esta en el minimo.
    def _aplicar_reduccion_o_refuerzo(self, contexto, regla, explicacion):
        anterior = self._nivel_inferior(contexto["nivel_actual"])
        en_minimo = anterior["id_nivel"] == contexto["nivel_actual"]["id_nivel"]
        return {
            **contexto,
            "accion": ACCION_REFORZAR if en_minimo else ACCION_REDUCIR,
            "nivel_recomendado": anterior,
            "recomendar_refuerzo": True,
            "codigo_regla": regla["codigo_regla"],
            "mensaje": "Activa refuerzo." if en_minimo else "Baja la dificultad.",
            "explicacion": explicacion,
        }

    # Devuelve una decision explicita de mantener dificultad.
    def _mantener(self, contexto, regla, explicacion):
        return {
            **contexto,
            "accion": ACCION_MANTENER,
            "nivel_recomendado": contexto["nivel_actual"],
            "codigo_regla": regla["codigo_regla"],
            "mensaje": "Mantiene la dificultad.",
            "explicacion": explicacion,
        }

    # Obtiene el nivel inmediato superior al actual.
    def _nivel_superior(self, nivel_actual):
        indice = self._indice_nivel(nivel_actual)
        return self.niveles[min(indice + 1, len(self.niveles) - 1)]

    # Obtiene el nivel inmediato inferior al actual.
    def _nivel_inferior(self, nivel_actual):
        indice = self._indice_nivel(nivel_actual)
        return self.niveles[max(indice - 1, 0)]

    # Localiza la posicion del nivel actual en la lista ordenada.
    def _indice_nivel(self, nivel_actual):
        for indice, nivel in enumerate(self.niveles):
            if nivel["id_nivel"] == nivel_actual["id_nivel"]:
                return indice
        return 0
