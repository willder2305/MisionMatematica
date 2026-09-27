USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS plantillas_ejercicios (
    id_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT NOT NULL,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500) NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    plantilla_enunciado VARCHAR(500) NOT NULL,
    configuracion_json JSON NOT NULL,
    plantilla_explicacion VARCHAR(500) NULL,
    plantilla_pista VARCHAR(255) NULL,
    estado ENUM('borrador', 'publicada', 'desactivada') NOT NULL DEFAULT 'borrador',
    es_demo TINYINT(1) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_plantillas_grados
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_plantillas_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_plantillas_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel),
    CONSTRAINT uk_plantilla_nombre_nivel
        UNIQUE (id_grado, id_tema, id_nivel, nombre)
);

CREATE TABLE IF NOT EXISTS ejercicios_generados (
    id_ejercicio_generado INT AUTO_INCREMENT PRIMARY KEY,
    id_plantilla INT NOT NULL,
    id_partida INT NOT NULL,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    enunciado VARCHAR(500) NOT NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    respuesta_correcta VARCHAR(255) NOT NULL,
    explicacion VARCHAR(500) NULL,
    explicacion_pasos JSON NULL,
    pista VARCHAR(255) NULL,
    opciones_json JSON NULL,
    parametros_json JSON NOT NULL,
    semilla_generacion INT NOT NULL,
    estado_validacion ENUM('valido', 'invalido') NOT NULL DEFAULT 'valido',
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_generados_plantillas
        FOREIGN KEY (id_plantilla)
        REFERENCES plantillas_ejercicios(id_plantilla),
    CONSTRAINT fk_generados_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_generados_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_generados_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_tablas_generador_adaptativo$$

CREATE PROCEDURE actualizar_tablas_generador_adaptativo()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_ejercicio_generado_actual'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_ejercicio_generado_actual INT NULL AFTER id_ejercicio_actual;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'intentos_juego'
          AND COLUMN_NAME = 'id_ejercicio'
          AND IS_NULLABLE = 'NO'
    ) THEN
        ALTER TABLE intentos_juego MODIFY id_ejercicio INT NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'intentos_juego'
          AND COLUMN_NAME = 'id_ejercicio_generado'
    ) THEN
        ALTER TABLE intentos_juego ADD COLUMN id_ejercicio_generado INT NULL AFTER id_ejercicio;
    END IF;
END$$

DROP PROCEDURE IF EXISTS agregar_foreign_keys_generador_adaptativo$$

CREATE PROCEDURE agregar_foreign_keys_generador_adaptativo()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_ejercicio_generado_actual'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_ejercicio_generado_actual
                FOREIGN KEY (id_ejercicio_generado_actual)
                REFERENCES ejercicios_generados(id_ejercicio_generado);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'intentos_juego'
          AND CONSTRAINT_NAME = 'fk_intentos_ejercicios_generados'
    ) THEN
        ALTER TABLE intentos_juego
            ADD CONSTRAINT fk_intentos_ejercicios_generados
                FOREIGN KEY (id_ejercicio_generado)
                REFERENCES ejercicios_generados(id_ejercicio_generado);
    END IF;
END$$

DELIMITER ;

CALL actualizar_tablas_generador_adaptativo();
DROP PROCEDURE IF EXISTS actualizar_tablas_generador_adaptativo;

CALL agregar_foreign_keys_generador_adaptativo();
DROP PROCEDURE IF EXISTS agregar_foreign_keys_generador_adaptativo;

INSERT INTO temas (id_grado, nombre_tema, descripcion)
SELECT g.id_grado, tema.nombre_tema, tema.descripcion
FROM grados g
CROSS JOIN (
    SELECT 'Suma' AS nombre_tema, 'Plantillas demo de suma.' AS descripcion
    UNION ALL SELECT 'Resta', 'Plantillas demo de resta.'
    UNION ALL SELECT 'Multiplicacion', 'Plantillas demo de multiplicacion.'
    UNION ALL SELECT 'Division', 'Plantillas demo de division exacta.'
) tema
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND NOT EXISTS (
      SELECT 1 FROM temas t
      WHERE t.id_grado = g.id_grado
        AND t.nombre_tema = tema.nombre_tema
  );

INSERT INTO plantillas_ejercicios
    (id_grado, id_tema, id_nivel, nombre, descripcion, tipo_respuesta, plantilla_enunciado,
     configuracion_json, plantilla_explicacion, plantilla_pista, estado, es_demo)
SELECT g.id_grado, t.id_tema, n.id_nivel,
       CONCAT(t.nombre_tema, ' ', n.nombre),
       CONCAT('Plantilla demo para ', t.nombre_tema, ' en nivel ', n.nombre),
       CASE WHEN t.nombre_tema IN ('Suma', 'Multiplicacion') THEN 'seleccion_multiple' ELSE 'numerica' END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN '¿Cuánto es {a} + {b}?'
           WHEN 'Resta' THEN '¿Cuánto es {a} - {b}?'
           WHEN 'Multiplicacion' THEN '¿Cuánto es {a} x {b}?'
           ELSE '¿Cuánto es {a} / {b}?'
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN JSON_OBJECT('operacion', 'suma', 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 20 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 20 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END)
           ))
           WHEN 'Resta' THEN JSON_OBJECT('operacion', 'resta', 'permitir_negativos', false, 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 5 WHEN 'intermedio' THEN 30 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 30 WHEN 'intermedio' THEN 150 ELSE 800 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 10 ELSE 50 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END)
           ))
           WHEN 'Multiplicacion' THEN JSON_OBJECT('operacion', 'multiplicacion', 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 10 ELSE 20 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 99 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 2 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9 ELSE 99 END)
           ))
           ELSE JSON_OBJECT('operacion', 'division', 'division_exacta', true, 'variables', JSON_OBJECT(
               'resultado', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 5 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 30 ELSE 99 END),
               'divisor', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 2 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 12 ELSE 25 END)
           ))
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN '{a} + {b} = {respuesta}.'
           WHEN 'Resta' THEN '{a} - {b} = {respuesta}.'
           WHEN 'Multiplicacion' THEN '{a} x {b} = {respuesta}.'
           ELSE '{a} / {b} = {respuesta}.'
       END,
       'Usa la operacion indicada y revisa cada numero.',
       'publicada',
       1
FROM grados g
INNER JOIN temas t ON t.id_grado = g.id_grado
CROSS JOIN niveles_dificultad n
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND t.nombre_tema IN ('Suma', 'Resta', 'Multiplicacion', 'Division')
  AND n.codigo IN ('facil', 'intermedio', 'dificil')
  AND NOT EXISTS (
      SELECT 1 FROM plantillas_ejercicios p
      WHERE p.id_grado = g.id_grado
        AND p.id_tema = t.id_tema
        AND p.id_nivel = n.id_nivel
        AND p.nombre = CONCAT(t.nombre_tema, ' ', n.nombre)
  );
