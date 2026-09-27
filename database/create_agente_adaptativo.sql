CREATE TABLE IF NOT EXISTS temas (
    id_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT NOT NULL,
    nombre_tema VARCHAR(120) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_temas_grados
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),

    CONSTRAINT uk_temas_grado_nombre
        UNIQUE (id_grado, nombre_tema)
);

CREATE TABLE IF NOT EXISTS niveles_dificultad (
    id_nivel INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    orden_nivel INT NOT NULL,
    es_inicial TINYINT(1) NOT NULL DEFAULT 0,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_niveles_codigo UNIQUE (codigo),
    CONSTRAINT uk_niveles_orden UNIQUE (orden_nivel)
);

CREATE TABLE IF NOT EXISTS ejercicios (
    id_ejercicio INT AUTO_INCREMENT PRIMARY KEY,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    enunciado VARCHAR(500) NOT NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    respuesta_correcta VARCHAR(255) NOT NULL,
    explicacion VARCHAR(500) NULL,
    pista VARCHAR(255) NULL,
    estado ENUM('borrador', 'publicado', 'desactivado') NOT NULL DEFAULT 'borrador',
    es_demo TINYINT(1) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ejercicios_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),

    CONSTRAINT fk_ejercicios_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS opciones_ejercicio (
    id_opcion INT AUTO_INCREMENT PRIMARY KEY,
    id_ejercicio INT NOT NULL,
    texto_opcion VARCHAR(255) NOT NULL,
    orden_visualizacion INT NOT NULL DEFAULT 1,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_opciones_ejercicio_orden UNIQUE (id_ejercicio, orden_visualizacion),
    CONSTRAINT fk_opciones_ejercicios
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio)
);

CREATE TABLE IF NOT EXISTS intentos_juego (
    id_intento INT AUTO_INCREMENT PRIMARY KEY,
    id_partida INT NOT NULL,
    id_ejercicio INT NOT NULL,
    respuesta_estudiante VARCHAR(255) NOT NULL,
    es_correcta TINYINT(1) NOT NULL,
    nivel_al_responder INT NOT NULL,
    tiempo_respuesta_ms INT NOT NULL DEFAULT 0,
    casilla_antes INT NOT NULL,
    casilla_despues INT NOT NULL,
    vidas_antes INT NOT NULL,
    vidas_despues INT NOT NULL,
    fecha_respuesta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request_id VARCHAR(80) NOT NULL,
    respuesta_api_json JSON NULL,

    CONSTRAINT uk_intentos_request_id UNIQUE (request_id),
    CONSTRAINT fk_intentos_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_intentos_ejercicios
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio),
    CONSTRAINT fk_intentos_niveles
        FOREIGN KEY (nivel_al_responder)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS reglas_adaptativas (
    id_regla INT AUTO_INCREMENT PRIMARY KEY,
    codigo_regla VARCHAR(80) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500) NULL,
    prioridad INT NOT NULL,
    parametros_json JSON NOT NULL,
    accion ENUM('mantener', 'aumentar', 'reducir', 'reforzar') NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_reglas_codigo UNIQUE (codigo_regla)
);

CREATE TABLE IF NOT EXISTS decisiones_agente (
    id_decision INT AUTO_INCREMENT PRIMARY KEY,
    id_partida INT NOT NULL,
    id_intento INT NOT NULL,
    id_tema INT NOT NULL,
    nivel_anterior INT NOT NULL,
    nivel_nuevo INT NOT NULL,
    accion ENUM('mantener', 'aumentar', 'reducir', 'reforzar') NOT NULL,
    regla_aplicada VARCHAR(80) NOT NULL,
    motivo VARCHAR(500) NOT NULL,
    datos_entrada_json JSON NOT NULL,
    fecha_decision TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_decisiones_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_decisiones_intentos
        FOREIGN KEY (id_intento)
        REFERENCES intentos_juego(id_intento),
    CONSTRAINT fk_decisiones_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_decisiones_nivel_anterior
        FOREIGN KEY (nivel_anterior)
        REFERENCES niveles_dificultad(id_nivel),
    CONSTRAINT fk_decisiones_nivel_nuevo
        FOREIGN KEY (nivel_nuevo)
        REFERENCES niveles_dificultad(id_nivel)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_partidas_juego_adaptativo$$

CREATE PROCEDURE actualizar_partidas_juego_adaptativo()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_grado'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_grado INT NULL AFTER id_usuario;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_tema'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_tema INT NULL AFTER id_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'request_id'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN request_id VARCHAR(80) NULL AFTER id_tema;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_nivel_inicial'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_nivel_inicial INT NULL AFTER id_tema;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_nivel_actual'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_nivel_actual INT NULL AFTER id_nivel_inicial;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_ejercicio_actual'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_ejercicio_actual INT NULL AFTER id_nivel_actual;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'vidas_iniciales'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN vidas_iniciales INT NOT NULL DEFAULT 5 AFTER total_errores;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'vidas_restantes'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN vidas_restantes INT NOT NULL DEFAULT 5 AFTER vidas_iniciales;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'preguntas_respondidas'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN preguntas_respondidas INT NOT NULL DEFAULT 0 AFTER vidas_restantes;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'motivo_finalizacion'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN motivo_finalizacion VARCHAR(80) NULL AFTER estado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'fecha_ultima_actividad'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN fecha_ultima_actividad TIMESTAMP NULL DEFAULT NULL AFTER fecha_fin;
    END IF;

    ALTER TABLE partidas_juego
        MODIFY estado ENUM('en_curso', 'completada', 'sin_vidas', 'abandonada') NOT NULL DEFAULT 'en_curso';

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND INDEX_NAME = 'uk_partidas_request_id'
    ) THEN
        ALTER TABLE partidas_juego ADD UNIQUE KEY uk_partidas_request_id (request_id);
    END IF;
END$$

DELIMITER ;

CALL actualizar_partidas_juego_adaptativo();
DROP PROCEDURE IF EXISTS actualizar_partidas_juego_adaptativo;

DELIMITER $$

CREATE PROCEDURE agregar_foreign_keys_partidas_adaptativas()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_grados'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_grados
                FOREIGN KEY (id_grado)
                REFERENCES grados(id_grado);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_temas'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_temas
                FOREIGN KEY (id_tema)
                REFERENCES temas(id_tema);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_nivel_inicial'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_nivel_inicial
                FOREIGN KEY (id_nivel_inicial)
                REFERENCES niveles_dificultad(id_nivel);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_nivel_actual'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_nivel_actual
                FOREIGN KEY (id_nivel_actual)
                REFERENCES niveles_dificultad(id_nivel);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_ejercicio_actual'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_ejercicio_actual
                FOREIGN KEY (id_ejercicio_actual)
                REFERENCES ejercicios(id_ejercicio);
    END IF;
END$$

DELIMITER ;

CALL agregar_foreign_keys_partidas_adaptativas();
DROP PROCEDURE IF EXISTS agregar_foreign_keys_partidas_adaptativas;

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'facil', 'Facil', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'facil');

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'intermedio', 'Intermedio', 2, 0
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'intermedio');

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'dificil', 'Dificil', 3, 0
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'dificil');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'dos_errores_consecutivos', 'Dos errores consecutivos', 'Reduce dificultad o recomienda refuerzo cuando hay dos errores consecutivos.', 1,
       JSON_OBJECT('incorrectas_consecutivas', 2, 'cooldown_intentos', 2), 'reducir'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'dos_errores_consecutivos');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'tres_aciertos_consecutivos', 'Tres aciertos consecutivos', 'Aumenta dificultad al alcanzar exactamente tres respuestas correctas consecutivas.', 2,
       JSON_OBJECT('correctas_consecutivas', 3, 'cooldown_intentos', 2), 'aumentar'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'tres_aciertos_consecutivos');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'porcentaje_bajo', 'Porcentaje bajo', 'Reduce dificultad o recomienda refuerzo cuando el porcentaje de aciertos es menor a 60.', 3,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_maximo', 60, 'cooldown_intentos', 3), 'reducir'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'porcentaje_bajo');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'porcentaje_alto', 'Porcentaje alto', 'Puede aumentar dificultad cuando el porcentaje supera 80 y no existe aumento reciente.', 4,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_minimo', 80, 'cooldown_intentos', 3), 'aumentar'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'porcentaje_alto');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'rango_estable', 'Rango estable', 'Mantiene dificultad cuando el porcentaje esta entre 60 y 80.', 5,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_minimo', 60, 'porcentaje_maximo', 80), 'mantener'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'rango_estable');

INSERT INTO temas (id_grado, nombre_tema, descripcion)
SELECT g.id_grado, 'Operaciones basicas', 'Ejercicios demo de suma, resta, multiplicacion y division.'
FROM grados g
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND NOT EXISTS (
      SELECT 1 FROM temas t
      WHERE t.id_grado = g.id_grado
        AND t.nombre_tema = 'Operaciones basicas'
  );

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Cuanto es 2 + 3?', 'seleccion_multiple', '5', '2 + 3 = 5.', 'Suma primero las unidades.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'facil'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Cuanto es 2 + 3?');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Cuanto es 9 - 4?', 'seleccion_multiple', '5', '9 - 4 = 5.', 'Resta cuatro pasos desde nueve.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'facil'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Cuanto es 9 - 4?');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Cuanto es 6 + 7?', 'numerica', '13', '6 + 7 = 13.', 'Completa a diez y suma lo restante.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'facil'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Cuanto es 6 + 7?');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Cuanto es 8 x 4?', 'seleccion_multiple', '32', '8 x 4 = 32.', 'Piensa en cuatro grupos de ocho.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'intermedio'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Cuanto es 8 x 4?');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Resuelve: 45 / 5', 'numerica', '9', '45 / 5 = 9.', 'Busca cuantas veces cabe 5 en 45.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'intermedio'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Resuelve: 45 / 5');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Cuanto es 12 x 7?', 'seleccion_multiple', '84', '12 x 7 = 84.', 'Multiplica 10 x 7 y 2 x 7.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'dificil'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Cuanto es 12 x 7?');

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, 'Resuelve: 144 / 12', 'numerica', '12', '144 / 12 = 12.', '12 x 12 = 144.', 'publicado', 1
FROM temas t JOIN grados g ON g.id_grado = t.id_grado JOIN niveles_dificultad n ON n.codigo = 'dificil'
WHERE g.codigo_grado IN ('4P', '5P', '6P') AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE e.id_tema = t.id_tema AND e.enunciado = 'Resuelve: 144 / 12');

INSERT INTO opciones_ejercicio (id_ejercicio, texto_opcion, orden_visualizacion)
SELECT e.id_ejercicio, opciones.texto, opciones.orden
FROM ejercicios e
JOIN (
    SELECT 'Cuanto es 2 + 3?' AS enunciado, '4' AS texto, 1 AS orden
    UNION ALL SELECT 'Cuanto es 2 + 3?', '5', 2
    UNION ALL SELECT 'Cuanto es 2 + 3?', '6', 3
    UNION ALL SELECT 'Cuanto es 2 + 3?', '7', 4
    UNION ALL SELECT 'Cuanto es 9 - 4?', '3', 1
    UNION ALL SELECT 'Cuanto es 9 - 4?', '4', 2
    UNION ALL SELECT 'Cuanto es 9 - 4?', '5', 3
    UNION ALL SELECT 'Cuanto es 9 - 4?', '6', 4
    UNION ALL SELECT 'Cuanto es 8 x 4?', '24', 1
    UNION ALL SELECT 'Cuanto es 8 x 4?', '32', 2
    UNION ALL SELECT 'Cuanto es 8 x 4?', '36', 3
    UNION ALL SELECT 'Cuanto es 8 x 4?', '40', 4
    UNION ALL SELECT 'Cuanto es 12 x 7?', '72', 1
    UNION ALL SELECT 'Cuanto es 12 x 7?', '84', 2
    UNION ALL SELECT 'Cuanto es 12 x 7?', '92', 3
    UNION ALL SELECT 'Cuanto es 12 x 7?', '96', 4
) opciones ON opciones.enunciado = e.enunciado
WHERE e.tipo_respuesta = 'seleccion_multiple'
  AND NOT EXISTS (
      SELECT 1 FROM opciones_ejercicio oe
      WHERE oe.id_ejercicio = e.id_ejercicio
        AND oe.texto_opcion = opciones.texto
  );
