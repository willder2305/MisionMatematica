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

        if self._descenso_sostenido(metricas):
            return self._aplicar_reduccion_o_refuerzo(
                contexto, {"codigo_regla": "descenso_sostenido"}, "Los errores recientes requieren práctica de refuerzo."
            )
        if self._dominio_sostenido(metricas):
            return self._aplicar_aumento(
                contexto, {"codigo_regla": "dominio_sostenido"}, "Demostró dominio estable en este nivel."
            )
        return contexto

    def _sin_cooldown(self, metricas):
        return int(metricas.get("preguntas_desde_ultimo_cambio", 999)) >= 6

    # Exige una ventana suficiente, precisión y un cierre consistente antes de subir.
    def _dominio_sostenido(self, metricas):
        return (
            metricas.get("total_intentos", 0) >= 8
            and metricas.get("porcentaje_aciertos", 0) >= 80
            and metricas.get("correctas_consecutivas", 0) >= 4
            and metricas.get("errores_ultimas_cinco", 0) <= 1
            and self._sin_cooldown(metricas)
        )

    # Un descenso requiere evidencia repetida; un fallo aislado no altera el nivel.
    def _descenso_sostenido(self, metricas):
        return (
            metricas.get("total_intentos", 0) >= 6
            and (metricas.get("porcentaje_aciertos", 0) < 50 or metricas.get("errores_ultimas_cinco", 0) >= 3)
            and self._sin_cooldown(metricas)
        )

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
