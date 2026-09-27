USE tesis_matematica_app;

DELIMITER $$

DROP PROCEDURE IF EXISTS mm_add_column_if_missing$$
CREATE PROCEDURE mm_add_column_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table_name, ' ADD COLUMN ', p_column_name, ' ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_index_if_missing$$
CREATE PROCEDURE mm_add_index_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND INDEX_NAME = p_index_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table_name, ' ADD ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DELIMITER ;

CALL mm_add_column_if_missing('promociones_curriculares_tema', 'id_nivel_anterior', 'INT NULL AFTER id_grado_nuevo');
CALL mm_add_column_if_missing('promociones_curriculares_tema', 'id_nivel_nuevo', 'INT NULL AFTER id_nivel_anterior');
CALL mm_add_column_if_missing('promociones_curriculares_tema', 'tipo_movimiento', 'ENUM(''promocion'', ''descenso'') NOT NULL DEFAULT ''promocion'' AFTER id_nivel_nuevo');
CALL mm_add_index_if_missing('temas', 'idx_temas_grado_estado_nombre', 'INDEX idx_temas_grado_estado_nombre (id_grado, estado, nombre_tema)');
CALL mm_add_index_if_missing('plantillas_ejercicios', 'idx_plantillas_catalogo', 'INDEX idx_plantillas_catalogo (id_grado, id_tema, id_nivel, estado, es_demo)');
CALL mm_add_index_if_missing('promociones_curriculares_tema', 'idx_promociones_curricular_fecha', 'INDEX idx_promociones_curricular_fecha (id_usuario, fecha_promocion, id_promocion)');

DROP PROCEDURE IF EXISTS mm_add_column_if_missing;
DROP PROCEDURE IF EXISTS mm_add_index_if_missing;

UPDATE temas
SET estado = 'inactivo'
WHERE nombre_tema = 'Operaciones basicas';

INSERT INTO temas (id_grado, nombre_tema, descripcion, estado)
SELECT g.id_grado, catalogo.nombre_tema, catalogo.descripcion, 'activo'
FROM grados g
INNER JOIN (
    SELECT 'Suma' AS nombre_tema, 'Suma de numeros naturales con dificultad progresiva.' AS descripcion, '4P' AS desde
    UNION ALL SELECT 'Resta', 'Resta de numeros naturales con reagrupacion progresiva.', '4P'
    UNION ALL SELECT 'Multiplicacion', 'Multiplicacion de numeros naturales por complejidad curricular.', '4P'
    UNION ALL SELECT 'Division', 'Division exacta generada desde resultado y divisor.', '4P'
    UNION ALL SELECT 'Potencias', 'Potencias enteras positivas y potencias de base 10.', '4P'
    UNION ALL SELECT 'Raiz cuadrada', 'Raices cuadradas exactas con cuadrados perfectos.', '4P'
    UNION ALL SELECT 'Operaciones combinadas', 'Jerarquia de operaciones con y sin agrupacion.', '4P'
    UNION ALL SELECT 'Suma de fracciones', 'Suma de fracciones con resultado simplificado.', '4P'
    UNION ALL SELECT 'Resta de fracciones', 'Resta de fracciones con resultado no negativo cuando corresponde.', '4P'
    UNION ALL SELECT 'Multiplicacion de fracciones', 'Multiplicacion de fracciones con simplificacion.', '4P'
    UNION ALL SELECT 'Division de fracciones', 'Division de fracciones mediante inverso multiplicativo.', '4P'
    UNION ALL SELECT 'Suma de decimales', 'Suma decimal exacta por nivel.', '4P'
    UNION ALL SELECT 'Resta de decimales', 'Resta decimal exacta por nivel.', '4P'
    UNION ALL SELECT 'Multiplicacion de decimales', 'Multiplicacion decimal exacta por nivel.', '4P'
    UNION ALL SELECT 'Division de decimales', 'Division decimal con precision controlada.', '4P'
    UNION ALL SELECT 'Porcentajes', 'Porcentaje de una cantidad con Decimal.', '4P'
    UNION ALL SELECT 'Regla de tres directa', 'Proporcionalidad directa estructurada.', '5P'
    UNION ALL SELECT 'Regla de tres inversa', 'Proporcionalidad inversa estructurada.', '5P'
    UNION ALL SELECT 'Operaciones combinadas de fracciones', 'Operaciones combinadas con fracciones exactas.', '5P'
    UNION ALL SELECT 'Conversiones de fracciones', 'Conversion a entero, decimal o numero mixto.', '5P'
    UNION ALL SELECT 'Geometria', 'Area y perimetro de figuras planas.', '6P'
) catalogo
WHERE (
        catalogo.desde = '4P'
        OR (catalogo.desde = '5P' AND g.codigo_grado IN ('5P', '6P'))
        OR (catalogo.desde = '6P' AND g.codigo_grado = '6P')
      )
  AND g.codigo_grado IN ('4P', '5P', '6P')
  AND NOT EXISTS (
      SELECT 1
      FROM temas t
      WHERE t.id_grado = g.id_grado
        AND t.nombre_tema = catalogo.nombre_tema
  );

UPDATE temas t
INNER JOIN grados g ON g.id_grado = t.id_grado
SET t.estado = 'activo'
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND t.nombre_tema IN (
      'Suma', 'Resta', 'Multiplicacion', 'Division', 'Potencias', 'Raiz cuadrada',
      'Operaciones combinadas', 'Suma de fracciones', 'Resta de fracciones',
      'Multiplicacion de fracciones', 'Division de fracciones', 'Suma de decimales',
      'Resta de decimales', 'Multiplicacion de decimales', 'Division de decimales',
      'Porcentajes', 'Regla de tres directa', 'Regla de tres inversa',
      'Operaciones combinadas de fracciones', 'Conversiones de fracciones', 'Geometria'
  );

INSERT INTO plantillas_ejercicios
    (id_grado, id_tema, id_nivel, nombre, descripcion, tipo_respuesta, plantilla_enunciado,
     configuracion_json, plantilla_explicacion, plantilla_pista, estado, es_demo)
SELECT g.id_grado, t.id_tema, n.id_nivel,
       CONCAT(t.nombre_tema, ' ', n.nombre, ' catalogo'),
       CONCAT('Plantilla procedimental de catalogo para ', t.nombre_tema, ' en ', g.nombre_grado, ' ', n.nombre),
       'seleccion_multiple',
       CASE t.nombre_tema
           WHEN 'Suma' THEN 'Cuanto es {expresion}?'
           WHEN 'Resta' THEN 'Cuanto es {a} - {b}?'
           WHEN 'Multiplicacion' THEN 'Cuanto es {a} x {b}?'
           WHEN 'Division' THEN 'Cuanto es {a} / {b}?'
           WHEN 'Potencias' THEN 'Cuanto es {base}^{exponente}?'
           WHEN 'Raiz cuadrada' THEN 'Cual es la raiz cuadrada de {radicando}?'
           WHEN 'Operaciones combinadas' THEN 'Resuelve: {expresion}'
           WHEN 'Suma de fracciones' THEN 'Resuelve: {f1} + {f2}'
           WHEN 'Resta de fracciones' THEN 'Resuelve: {f1} - {f2}'
           WHEN 'Multiplicacion de fracciones' THEN 'Resuelve: {f1} x {f2}'
           WHEN 'Division de fracciones' THEN 'Resuelve: {f1} / {f2}'
           WHEN 'Suma de decimales' THEN 'Resuelve: {a} + {b}'
           WHEN 'Resta de decimales' THEN 'Resuelve: {a} - {b}'
           WHEN 'Multiplicacion de decimales' THEN 'Resuelve: {a} x {b}'
           WHEN 'Division de decimales' THEN 'Resuelve: {a} / {b}'
           WHEN 'Porcentajes' THEN 'Cuanto es el {porcentaje}% de {cantidad}?'
           WHEN 'Regla de tres directa' THEN 'Si {a} cuadernos cuestan Q{b}, cuanto cuestan {c}?'
           WHEN 'Regla de tres inversa' THEN 'Si {a} trabajadores tardan {b} dias, cuantos dias tardan {c} trabajadores?'
           WHEN 'Operaciones combinadas de fracciones' THEN 'Resuelve: {expresion}'
           WHEN 'Conversiones de fracciones' THEN 'Convierte {fraccion} segun el tipo: {subtipo_conversion}'
           ELSE 'Calcula {calculo} de {figura} con {datos}.'
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN JSON_OBJECT('operacion', 'suma', 'min_operandos', 2, 'max_operandos', CASE n.codigo WHEN 'facil' THEN 2 ELSE 3 END, 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 10000 ELSE 1000000 END, 'max', CASE n.codigo WHEN 'facil' THEN 9999 WHEN 'intermedio' THEN 999999 ELSE CASE g.codigo_grado WHEN '4P' THEN 999999999 WHEN '5P' THEN 999999999999 ELSE 999999999999 END END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 10000 ELSE 1000000 END, 'max', CASE n.codigo WHEN 'facil' THEN 9999 WHEN 'intermedio' THEN 999999 ELSE CASE g.codigo_grado WHEN '4P' THEN 999999999 WHEN '5P' THEN 999999999999 ELSE 999999999999 END END)
           ))
           WHEN 'Resta' THEN JSON_OBJECT('operacion', 'resta', 'permitir_negativos', false, 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 10000 ELSE 1000000 END, 'max', CASE n.codigo WHEN 'facil' THEN 9999 WHEN 'intermedio' THEN 999999 ELSE CASE g.codigo_grado WHEN '4P' THEN 999999999 ELSE 999999999999 END END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 10000 ELSE 1000000 END, 'max', CASE n.codigo WHEN 'facil' THEN 9999 WHEN 'intermedio' THEN 999999 ELSE CASE g.codigo_grado WHEN '4P' THEN 999999999 ELSE 999999999999 END END)
           ))
           WHEN 'Multiplicacion' THEN JSON_OBJECT('operacion', 'multiplicacion', 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 10 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 99 WHEN 'intermedio' THEN 999 ELSE CASE g.codigo_grado WHEN '4P' THEN 9999 ELSE 99999 END END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE CASE g.codigo_grado WHEN '4P' THEN 999 ELSE 999 END END)
           ))
           WHEN 'Division' THEN JSON_OBJECT('operacion', 'division', 'division_exacta', true, 'variables', JSON_OBJECT(
               'resultado', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 99 WHEN 'intermedio' THEN 999 ELSE CASE g.codigo_grado WHEN '4P' THEN 9999 ELSE 99999 END END),
               'divisor', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 999 END)
           ))
           WHEN 'Potencias' THEN JSON_OBJECT('operacion', 'potencia', 'incluir_base_10', true, 'variables', JSON_OBJECT(
               'base', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 12 ELSE 15 END),
               'exponente', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 3 ELSE CASE g.codigo_grado WHEN '4P' THEN 4 WHEN '5P' THEN 5 ELSE 5 END END)
           ))
           WHEN 'Raiz cuadrada' THEN JSON_OBJECT('operacion', 'raiz_cuadrada', 'variables', JSON_OBJECT(
               'raiz', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 12 WHEN 'intermedio' THEN 31 ELSE CASE g.codigo_grado WHEN '4P' THEN 31 WHEN '5P' THEN 99 ELSE 150 END END)
           ))
           WHEN 'Operaciones combinadas' THEN JSON_OBJECT('operacion', 'operaciones_combinadas', 'con_parentesis', CASE n.codigo WHEN 'facil' THEN false ELSE true END, 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 12 ELSE 50 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 12 ELSE 50 END),
               'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 20 END),
               'd', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 20 END)
           ))
           WHEN 'Suma de fracciones' THEN JSON_OBJECT('operacion', 'suma_fracciones', 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT('a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9999 ELSE 999999999 END), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 9999 END), 'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9999 ELSE 999999999 END), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 9999 END)))
           WHEN 'Resta de fracciones' THEN JSON_OBJECT('operacion', 'resta_fracciones', 'permitir_negativos', false, 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT('a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9999 ELSE 999999999 END), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 9999 END), 'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9999 ELSE 999999999 END), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 9999 END)))
           WHEN 'Multiplicacion de fracciones' THEN JSON_OBJECT('operacion', 'multiplicacion_fracciones', 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT('a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END)))
           WHEN 'Division de fracciones' THEN JSON_OBJECT('operacion', 'division_fracciones', 'forma_simplificada_requerida', true, 'variables', JSON_OBJECT('a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 999 ELSE 9999 END)))
           WHEN 'Suma de decimales' THEN JSON_OBJECT('operacion', 'suma_decimales', 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE n.codigo WHEN 'facil' THEN 99999 WHEN 'intermedio' THEN 999999999 ELSE 9999999999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 3 ELSE 4 END), 'b', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE n.codigo WHEN 'facil' THEN 99999 WHEN 'intermedio' THEN 999999999 ELSE 9999999999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 3 ELSE 4 END)))
           WHEN 'Resta de decimales' THEN JSON_OBJECT('operacion', 'resta_decimales', 'permitir_negativos', false, 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE n.codigo WHEN 'facil' THEN 99999 WHEN 'intermedio' THEN 999999999 ELSE 9999999999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 3 ELSE 4 END), 'b', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE n.codigo WHEN 'facil' THEN 99999 WHEN 'intermedio' THEN 999999999 ELSE 9999999999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 3 ELSE 4 END)))
           WHEN 'Multiplicacion de decimales' THEN JSON_OBJECT('operacion', 'multiplicacion_decimales', 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE n.codigo WHEN 'facil' THEN 999 WHEN 'intermedio' THEN 99999 ELSE 99999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 3 ELSE 4 END), 'b', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE n.codigo WHEN 'facil' THEN 999 WHEN 'intermedio' THEN 99999 ELSE 99999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 3 ELSE 4 END)))
           WHEN 'Division de decimales' THEN JSON_OBJECT('operacion', 'division_decimales', 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'decimal', 'min', 100, 'max', CASE n.codigo WHEN 'facil' THEN 9999 WHEN 'intermedio' THEN 999999 ELSE 99999999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 3 ELSE 4 END), 'b', JSON_OBJECT('tipo', 'decimal', 'min', 10, 'max', CASE n.codigo WHEN 'facil' THEN 99 WHEN 'intermedio' THEN 999 ELSE 9999 END, 'decimales', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 2 ELSE 3 END)))
           WHEN 'Porcentajes' THEN JSON_OBJECT('operacion', 'porcentaje', 'variables', JSON_OBJECT('cantidad', JSON_OBJECT('tipo', 'entero', 'min', 10, 'max', CASE n.codigo WHEN 'facil' THEN 200 WHEN 'intermedio' THEN 999 ELSE 9999 END), 'porcentaje', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 10 ELSE 1 END, 'max', 100)))
           WHEN 'Regla de tres directa' THEN JSON_OBJECT('operacion', 'regla_tres_directa', 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 10 ELSE 99 END), 'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 50 ELSE 999 END), 'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 10 ELSE 99 END)))
           WHEN 'Regla de tres inversa' THEN JSON_OBJECT('operacion', 'regla_tres_inversa', 'variables', JSON_OBJECT('a', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 10 ELSE 50 END), 'b', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 20 ELSE 100 END), 'c', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 10 ELSE 50 END)))
           WHEN 'Operaciones combinadas de fracciones' THEN JSON_OBJECT('operacion', 'operaciones_combinadas_fracciones', 'variables', JSON_OBJECT('a_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END), 'a_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END), 'b_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END), 'b_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END), 'c_numerador', JSON_OBJECT('tipo', 'entero', 'min', 1, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END), 'c_denominador', JSON_OBJECT('tipo', 'entero', 'min', 2, 'max', CASE n.codigo WHEN 'facil' THEN 9 ELSE 99 END)))
           WHEN 'Conversiones de fracciones' THEN JSON_OBJECT('operacion', 'conversion_fracciones', 'subtipo', CASE n.codigo WHEN 'facil' THEN 'entero' WHEN 'intermedio' THEN 'decimal' ELSE 'mixta' END)
           ELSE JSON_OBJECT('operacion', 'geometria', 'figuras', CASE n.codigo WHEN 'facil' THEN JSON_ARRAY('cuadrado', 'rectangulo', 'triangulo') WHEN 'intermedio' THEN JSON_ARRAY('cuadrado', 'rectangulo', 'triangulo', 'circulo', 'rombo') ELSE JSON_ARRAY('cuadrado', 'rectangulo', 'triangulo', 'circulo', 'rombo', 'poligono') END, 'calculos', JSON_ARRAY('area', 'perimetro'), 'min_medida', 2, 'max_medida', CASE n.codigo WHEN 'facil' THEN 10 WHEN 'intermedio' THEN 25 ELSE 50 END, 'pi', '3.14')
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN '{expresion} = {respuesta}.'
           WHEN 'Resta' THEN '{a} - {b} = {respuesta}.'
           WHEN 'Multiplicacion' THEN '{a} x {b} = {respuesta}.'
           WHEN 'Division' THEN '{a} / {b} = {respuesta}.'
           ELSE 'Respuesta correcta: {respuesta}.'
       END,
       'Resuelve paso a paso y revisa la operacion indicada.',
       'publicada',
       0
FROM grados g
INNER JOIN temas t ON t.id_grado = g.id_grado
CROSS JOIN niveles_dificultad n
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND n.codigo IN ('facil', 'intermedio', 'dificil')
  AND t.estado = 'activo'
  AND NOT EXISTS (
      SELECT 1
      FROM plantillas_ejercicios p
      WHERE p.id_grado = g.id_grado
        AND p.id_tema = t.id_tema
        AND p.id_nivel = n.id_nivel
        AND p.nombre = CONCAT(t.nombre_tema, ' ', n.nombre, ' catalogo')
  );
