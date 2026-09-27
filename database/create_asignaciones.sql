USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS asignaciones (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_institucion_grado INT NOT NULL,
    id_grupo INT NULL,
    id_seccion INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    instrucciones VARCHAR(500) NULL,
    tipo ENUM('generacion_automatica', 'ejercicios_especificos') NOT NULL DEFAULT 'generacion_automatica',
    id_nivel_inicial INT NOT NULL,
    cantidad_preguntas INT NOT NULL DEFAULT 10,
    fecha_inicio DATETIME NOT NULL,
    fecha_limite DATETIME NULL,
    obligatoria TINYINT(1) NOT NULL DEFAULT 1,
    estado ENUM('borrador', 'activa', 'pausada', 'finalizada', 'cancelada') NOT NULL DEFAULT 'activa',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_asignaciones_docente
        FOREIGN KEY (id_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_asignaciones_grupo
        FOREIGN KEY (id_grupo)
        REFERENCES grupos(id_grupo),
    CONSTRAINT fk_asignaciones_institucion_grado
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado),
    CONSTRAINT fk_asignaciones_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion),
    CONSTRAINT fk_asignaciones_nivel
        FOREIGN KEY (id_nivel_inicial)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS asignacion_temas (
    id_asignacion_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_tema INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_asignacion_tema UNIQUE (id_asignacion, id_tema),
    CONSTRAINT fk_asignacion_temas_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_asignacion_temas_tema
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema)
);

CREATE TABLE IF NOT EXISTS asignacion_ejercicios (
    id_asignacion_ejercicio INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_ejercicio INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_asignacion_ejercicio UNIQUE (id_asignacion, id_ejercicio),
    CONSTRAINT fk_asignacion_ejercicios_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_asignacion_ejercicios_ejercicio
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio)
);

CREATE TABLE IF NOT EXISTS estudiante_asignaciones (
    id_estudiante_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_estudiante INT NOT NULL,
    estado ENUM('pendiente','en_progreso','completada') NOT NULL DEFAULT 'pendiente',
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP NULL DEFAULT NULL,
    fecha_completada TIMESTAMP NULL DEFAULT NULL,
    cantidad_intentos INT NOT NULL DEFAULT 0,
    ultima_partida INT NULL,
    fecha_ultima_actividad TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_estudiante_asignacion UNIQUE (id_asignacion, id_estudiante),
    CONSTRAINT fk_estudiante_asignaciones_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_estudiante_asignaciones_estudiante
        FOREIGN KEY (id_estudiante)
        REFERENCES usuarios(id_usuario)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_partidas_asignaciones$$

CREATE PROCEDURE actualizar_partidas_asignaciones()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_asignacion'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_asignacion INT NULL AFTER id_usuario;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_asignaciones'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_asignaciones
                FOREIGN KEY (id_asignacion)
                REFERENCES asignaciones(id_asignacion);
    END IF;
END$$

DELIMITER ;

CALL actualizar_partidas_asignaciones();
DROP PROCEDURE IF EXISTS actualizar_partidas_asignaciones;
