-- Migración: simplifica los parámetros procedimentales del nivel Fácil.
-- Fecha: 2026-09-26.
-- Objetivo: conservar Fácil como introducción y refuerzo sin alterar Intermedio, Difícil ni plantillas manuales.
-- Compatibilidad: se puede ejecutar sobre instalaciones existentes después del catálogo matemático adaptativo.
USE tesis_matematica_app;

-- El nivel Fácil es la entrada y el refuerzo: rangos pequeños, pocos pasos y resultados comprobables.
-- Solo se ajustan las plantillas procedimentales de catálogo; las creadas manualmente se conservan intactas.
UPDATE plantillas_ejercicios p
INNER JOIN grados g ON g.id_grado = p.id_grado
INNER JOIN temas t ON t.id_tema = p.id_tema
INNER JOIN niveles_dificultad n ON n.id_nivel = p.id_nivel
SET p.configuracion_json = CASE t.nombre_tema
    WHEN 'Suma' THEN JSON_OBJECT('operacion', 'suma', 'min_operandos', 2, 'max_operandos', 2, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END)
    ))
    WHEN 'Resta' THEN JSON_OBJECT('operacion', 'resta', 'permitir_negativos', false, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END)
    ))
    WHEN 'Multiplicacion' THEN JSON_OBJECT('operacion', 'multiplicacion', 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 21 WHEN '5P' THEN 99 ELSE 999 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 9 WHEN '5P' THEN 12 ELSE 25 END)
    ))
    WHEN 'Division' THEN JSON_OBJECT('operacion', 'division', 'division_exacta', true, 'variables', JSON_OBJECT(
        'resultado', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 9 WHEN '5P' THEN 12 ELSE 99 END),
        'divisor', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 9 WHEN '5P' THEN 10 ELSE 25 END)
    ))
    WHEN 'Potencias' THEN JSON_OBJECT('operacion', 'potencia', 'incluir_base_10', true, 'variables', JSON_OBJECT(
        'base', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 10 WHEN '5P' THEN 10 ELSE 12 END),
        'exponente', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 2 ELSE 3 END)
    ))
    WHEN 'Raiz cuadrada' THEN JSON_OBJECT('operacion', 'raiz_cuadrada', 'variables', JSON_OBJECT(
        'raiz', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 10 WHEN '5P' THEN 15 ELSE 20 END)
    ))
    WHEN 'Operaciones combinadas' THEN JSON_OBJECT('operacion', 'operaciones_combinadas', 'cantidad_operaciones', 2, 'con_parentesis', false, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 10 WHEN '5P' THEN 20 ELSE 30 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 9 WHEN '5P' THEN 12 ELSE 15 END),
        'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 9 WHEN '5P' THEN 12 ELSE 15 END),
        'd', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 9)
    ))
    WHEN 'Suma de fracciones' THEN JSON_OBJECT('operacion', 'suma_fracciones', 'denominadores_iguales', true, 'fracciones_propias', true, 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT(
        'a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 3, 'max', 6),
        'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 3, 'max', 6)
    ))
    WHEN 'Resta de fracciones' THEN JSON_OBJECT('operacion', 'resta_fracciones', 'denominadores_iguales', true, 'fracciones_propias', true, 'permitir_negativos', false, 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT(
        'a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 3, 'max', 6),
        'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 3, 'max', 6)
    ))
    WHEN 'Multiplicacion de fracciones' THEN JSON_OBJECT('operacion', 'multiplicacion_fracciones', 'fracciones_propias', true, 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT(
        'a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6),
        'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6)
    ))
    WHEN 'Division de fracciones' THEN JSON_OBJECT('operacion', 'division_fracciones', 'fracciones_propias', true, 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT(
        'a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6),
        'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6)
    ))
    WHEN 'Suma de decimales' THEN JSON_OBJECT('operacion', 'suma_decimales', 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE g.codigo_grado WHEN '4P' THEN 9999 WHEN '5P' THEN 99999 ELSE 999999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END),
        'b', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE g.codigo_grado WHEN '4P' THEN 9999 WHEN '5P' THEN 99999 ELSE 999999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END)
    ))
    WHEN 'Resta de decimales' THEN JSON_OBJECT('operacion', 'resta_decimales', 'permitir_negativos', false, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE g.codigo_grado WHEN '4P' THEN 9999 WHEN '5P' THEN 99999 ELSE 999999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END),
        'b', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE g.codigo_grado WHEN '4P' THEN 9999 WHEN '5P' THEN 99999 ELSE 999999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END)
    ))
    WHEN 'Multiplicacion de decimales' THEN JSON_OBJECT('operacion', 'multiplicacion_decimales', 'segundo_entero', true, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 3 WHEN '5P' THEN 9 ELSE 12 END)
    ))
    WHEN 'Division de decimales' THEN JSON_OBJECT('operacion', 'division_decimales', 'divisor_entero', true, 'resultado_decimales', 1, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE g.codigo_grado WHEN '4P' THEN 999 WHEN '5P' THEN 9999 ELSE 99999 END, 'decimales', CASE g.codigo_grado WHEN '6P' THEN 3 ELSE 2 END),
        'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE g.codigo_grado WHEN '4P' THEN 4 WHEN '5P' THEN 10 ELSE 12 END),
        'resultado', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE g.codigo_grado WHEN '4P' THEN 99 WHEN '5P' THEN 199 ELSE 299 END)
    ))
    WHEN 'Porcentajes' THEN JSON_OBJECT('operacion', 'porcentaje', 'porcentajes_permitidos', JSON_ARRAY(10, 25, 50, 100), 'resultado_entero', true, 'variables', JSON_OBJECT(
        'cantidad', JSON_OBJECT('tipo', 'entero', 'min', 10, 'max', CASE g.codigo_grado WHEN '4P' THEN 100 WHEN '5P' THEN 200 ELSE 500 END),
        'porcentaje', JSON_OBJECT('tipo', 'entero', 'min', 10, 'max', 100)
    ))
    WHEN 'Regla de tres directa' THEN JSON_OBJECT('operacion', 'regla_tres_directa', 'relacion_entera', true, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 5), 'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 25),
        'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 5), 'factor', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5)
    ))
    WHEN 'Regla de tres inversa' THEN JSON_OBJECT('operacion', 'regla_tres_inversa', 'relacion_entera', true, 'variables', JSON_OBJECT(
        'a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 5), 'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 25),
        'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 5), 'factor', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 5)
    ))
    WHEN 'Operaciones combinadas de fracciones' THEN JSON_OBJECT('operacion', 'operaciones_combinadas_fracciones', 'fracciones_propias', true, 'variables', JSON_OBJECT(
        'a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6),
        'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6),
        'c_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 4), 'c_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 6)
    ))
    WHEN 'Conversiones de fracciones' THEN JSON_OBJECT('operacion', 'conversion_fracciones', 'subtipo', CASE g.codigo_grado WHEN '5P' THEN 'decimal' ELSE 'mixta' END, 'fracciones_propias', true, 'denominadores_permitidos', JSON_ARRAY(2, 4, 5), 'variables', JSON_OBJECT(
        'numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 3), 'denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', 5),
        'entero', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 3), 'resto', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', 3)
    ))
    ELSE JSON_OBJECT('operacion', 'geometria', 'figuras', JSON_ARRAY('cuadrado', 'rectangulo', 'triangulo'), 'calculos', JSON_ARRAY('area'), 'min_medida', 2, 'max_medida', 8, 'area_entera', true, 'pi', '3.14')
END
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND n.codigo = 'facil'
  AND p.estado = 'publicada'
  AND p.es_demo = 0
  AND p.nombre LIKE '% catalogo';
