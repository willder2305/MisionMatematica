USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS progreso_estudiante (
    id_progreso_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    total_partidas INT NOT NULL DEFAULT 0,
    total_ejercicios INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    puntos INT NOT NULL DEFAULT 0,
    mejor_puntuacion INT NOT NULL DEFAULT 0,
    tiempo_total_ms BIGINT NOT NULL DEFAULT 0,
    ultima_actividad TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_progreso_estudiante_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_progreso_estudiante_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS progreso_tema_estudiante (
    id_progreso_tema_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tema INT NOT NULL,
    id_nivel_actual INT NULL,
    total_intentos INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    tiempo_promedio_ms INT NOT NULL DEFAULT 0,
    cambios_dificultad INT NOT NULL DEFAULT 0,
    ultima_practica TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_progreso_tema_usuario UNIQUE (id_usuario, id_tema),
    CONSTRAINT fk_progreso_tema_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_progreso_tema_tema
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_progreso_tema_nivel
        FOREIGN KEY (id_nivel_actual)
        REFERENCES niveles_dificultad(id_nivel)
);
