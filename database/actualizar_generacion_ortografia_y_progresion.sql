-- Correcciones idempotentes para contenido ya almacenado y reglas documentadas.
UPDATE plantillas_ejercicios
SET plantilla_enunciado = CASE
    WHEN plantilla_enunciado LIKE 'Cuanto es %' THEN CONCAT('¿Cuánto es ', SUBSTRING(plantilla_enunciado, 11))
    WHEN plantilla_enunciado LIKE 'Cual es la raiz cuadrada%' THEN REPLACE(plantilla_enunciado, 'Cual es la raiz cuadrada', '¿Cuál es la raíz cuadrada')
    WHEN plantilla_enunciado LIKE 'Si {a} cuadernos cuestan Q{b}, cuanto cuestan {c}?' THEN 'Si {a} cuadernos cuestan Q{b}, ¿cuánto cuestan {c}?'
    WHEN plantilla_enunciado LIKE 'Si {a} trabajadores tardan {b} dias, cuantos dias tardan {c} trabajadores?' THEN 'Si {a} trabajadores tardan {b} días, ¿cuántos días tardan {c} trabajadores?'
    ELSE plantilla_enunciado
END;

UPDATE ejercicios
SET enunciado = CASE
    WHEN enunciado LIKE 'Cuanto es %' THEN CONCAT('¿Cuánto es ', SUBSTRING(enunciado, 11))
    WHEN enunciado LIKE 'Cual es la raiz cuadrada%' THEN REPLACE(enunciado, 'Cual es la raiz cuadrada', '¿Cuál es la raíz cuadrada')
    ELSE enunciado
END;

UPDATE reglas_adaptativas
SET estado = 'inactivo'
WHERE codigo_regla IN ('dos_errores_consecutivos', 'tres_aciertos_consecutivos', 'porcentaje_bajo', 'porcentaje_alto', 'rango_estable');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion, estado)
SELECT 'dominio_sostenido', 'Dominio sostenido', 'Promueve después de 8 intentos, 80% de precisión, 4 aciertos seguidos y 6 preguntas de espera.', 1,
       JSON_OBJECT('min_intentos', 8, 'precision_minima', 80, 'racha_minima', 4, 'max_errores_ultimas_5', 1, 'cooldown_intentos', 6), 'aumentar', 'activo'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'dominio_sostenido');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion, estado)
SELECT 'descenso_sostenido', 'Descenso sostenido', 'Reduce únicamente con 6 intentos y precisión menor a 50% o 3 errores recientes.', 2,
       JSON_OBJECT('min_intentos', 6, 'precision_maxima', 50, 'errores_ultimas_5', 3, 'cooldown_intentos', 6), 'reducir', 'activo'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'descenso_sostenido');
