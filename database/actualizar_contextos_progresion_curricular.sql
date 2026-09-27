USE tesis_matematica_app;

-- Separa el estado adaptativo del juego personal de cada actividad docente.
-- La migracion no elimina historicos: solo etiqueta partidas y crea estados nuevos.

DELIMITER $$

DROP PROCEDURE IF EXISTS mm_context_add_column$$
CREATE PROCEDURE mm_context_add_column(
    IN p_table VARCHAR(64),
    IN p_column VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table
          AND COLUMN_NAME = p_column
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' ADD COLUMN ', p_column, ' ', p_definition);
        PREPARE statement FROM @sql;
        EXECUTE statement;
        DEALLOCATE PREPARE statement;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_context_add_index$$
CREATE PROCEDURE mm_context_add_index(
    IN p_table VARCHAR(64),
    IN p_index VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table
          AND INDEX_NAME = p_index
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' ADD ', p_definition);
        PREPARE statement FROM @sql;
        EXECUTE statement;
        DEALLOCATE PREPARE statement;
    END IF;
END$$

DELIMITER ;

CALL mm_context_add_column(
    'partidas_juego',
    'tipo_contexto',
    'ENUM(''personal'', ''asignacion'') NOT NULL DEFAULT ''personal'' AFTER id_asignacion'
);
CALL mm_context_add_column(
    'decisiones_agente',
    'tipo_contexto',
    'ENUM(''personal'', ''asignacion'') NOT NULL DEFAULT ''personal'' AFTER id_tema'
);

-- La referencia a una asignacion es evidencia suficiente; las demas partidas
-- se preservan como juego personal. El progreso agregado ambiguo no se copia.
UPDATE partidas_juego
SET tipo_contexto = CASE WHEN id_asignacion IS NULL THEN 'personal' ELSE 'asignacion' END;

UPDATE decisiones_agente d
INNER JOIN partidas_juego p ON p.id_partida = d.id_partida
SET d.tipo_contexto = p.tipo_contexto;

ALTER TABLE decisiones_agente
    MODIFY accion ENUM('mantener', 'aumentar', 'reducir', 'reforzar', 'promover_grado') NOT NULL;

CREATE TABLE IF NOT EXISTS progreso_personal_catalogo (
    id_progreso_personal_catalogo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_grado_desbloqueado INT NOT NULL,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_progreso_personal_catalogo_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_progreso_personal_catalogo_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_progreso_personal_catalogo_grado FOREIGN KEY (id_grado_desbloqueado) REFERENCES grados(id_grado)
);

CREATE TABLE IF NOT EXISTS progreso_personal_tema (
    id_progreso_personal_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    tema_clave VARCHAR(160) NOT NULL,
    id_tema_actual INT NOT NULL,
    id_grado_curricular INT NOT NULL,
    id_nivel_actual INT NOT NULL,
    total_intentos INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    racha_correctas INT NOT NULL DEFAULT 0,
    racha_incorrectas INT NOT NULL DEFAULT 0,
    partidas_distintas INT NOT NULL DEFAULT 0,
    estado_dominio ENUM('inicial', 'en_progreso', 'dominado') NOT NULL DEFAULT 'inicial',
    tiempo_promedio_ms INT NOT NULL DEFAULT 0,
    cambios_dificultad INT NOT NULL DEFAULT 0,
    ultima_practica TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_progreso_personal_tema UNIQUE (id_usuario, tema_clave),
    CONSTRAINT fk_progreso_personal_tema_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_progreso_personal_tema_tema FOREIGN KEY (id_tema_actual) REFERENCES temas(id_tema),
    CONSTRAINT fk_progreso_personal_tema_grado FOREIGN KEY (id_grado_curricular) REFERENCES grados(id_grado),
    CONSTRAINT fk_progreso_personal_tema_nivel FOREIGN KEY (id_nivel_actual) REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS progreso_asignacion_tema_estudiante (
    id_progreso_asignacion_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_estudiante INT NOT NULL,
    id_tema INT NOT NULL,
    id_grado_asignacion INT NOT NULL,
    id_nivel_actual INT NOT NULL,
    total_intentos INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    racha_correctas INT NOT NULL DEFAULT 0,
    racha_incorrectas INT NOT NULL DEFAULT 0,
    partidas_distintas INT NOT NULL DEFAULT 0,
    tiempo_promedio_ms INT NOT NULL DEFAULT 0,
    cambios_dificultad INT NOT NULL DEFAULT 0,
    ultima_practica TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_progreso_asignacion_tema UNIQUE (id_asignacion, id_estudiante, id_tema),
    CONSTRAINT fk_progreso_asignacion_tema_asignacion FOREIGN KEY (id_asignacion) REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_progreso_asignacion_tema_estudiante FOREIGN KEY (id_estudiante) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_progreso_asignacion_tema_tema FOREIGN KEY (id_tema) REFERENCES temas(id_tema),
    CONSTRAINT fk_progreso_asignacion_tema_grado FOREIGN KEY (id_grado_asignacion) REFERENCES grados(id_grado),
    CONSTRAINT fk_progreso_asignacion_tema_nivel FOREIGN KEY (id_nivel_actual) REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS incidencias_contexto_progresion (
    id_incidencia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tema INT NOT NULL,
    tipo VARCHAR(120) NOT NULL,
    detalle_json JSON NOT NULL,
    estado ENUM('pendiente', 'resuelta') NOT NULL DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_incidencia_contexto_progreso UNIQUE (id_usuario, id_tema, tipo),
    CONSTRAINT fk_incidencia_contexto_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_incidencia_contexto_tema FOREIGN KEY (id_tema) REFERENCES temas(id_tema)
);

CALL mm_context_add_index('partidas_juego', 'idx_partidas_contexto_usuario', 'INDEX idx_partidas_contexto_usuario (tipo_contexto, id_usuario, id_tema)');
CALL mm_context_add_index('partidas_juego', 'idx_partidas_contexto_asignacion', 'INDEX idx_partidas_contexto_asignacion (tipo_contexto, id_asignacion, estado)');
CALL mm_context_add_index('decisiones_agente', 'idx_decisiones_contexto_tema', 'INDEX idx_decisiones_contexto_tema (tipo_contexto, id_tema, fecha_decision)');
CALL mm_context_add_index('progreso_personal_tema', 'idx_progreso_personal_usuario_grado', 'INDEX idx_progreso_personal_usuario_grado (id_usuario, id_grado_curricular)');
CALL mm_context_add_index('progreso_asignacion_tema_estudiante', 'idx_progreso_asignacion_estudiante', 'INDEX idx_progreso_asignacion_estudiante (id_estudiante, id_asignacion, id_tema)');

-- Solo se preserva como estado personal lo que no comparte tema con partidas
-- asignadas. Los agregados mezclados quedan documentados y se reinician de forma segura.
INSERT INTO incidencias_contexto_progresion (id_usuario, id_tema, tipo, detalle_json)
SELECT pte.id_usuario, pte.id_tema, 'progreso_historico_contexto_ambiguo',
       JSON_OBJECT('estrategia', 'no_copiado_a_estado_adaptativo_nuevo')
FROM progreso_tema_estudiante pte
WHERE EXISTS (
    SELECT 1 FROM partidas_juego p
    WHERE p.id_usuario = pte.id_usuario AND p.id_tema = pte.id_tema AND p.tipo_contexto = 'personal'
)
  AND EXISTS (
    SELECT 1 FROM partidas_juego p
    WHERE p.id_usuario = pte.id_usuario AND p.id_tema = pte.id_tema AND p.tipo_contexto = 'asignacion'
)
ON DUPLICATE KEY UPDATE detalle_json = VALUES(detalle_json);

INSERT INTO progreso_personal_tema
    (id_usuario, tema_clave, id_tema_actual, id_grado_curricular, id_nivel_actual,
     total_intentos, total_aciertos, total_errores, porcentaje_aciertos,
     racha_correctas, racha_incorrectas, estado_dominio, tiempo_promedio_ms,
     cambios_dificultad, ultima_practica)
SELECT pte.id_usuario, t.nombre_tema, pte.id_tema,
       COALESCE(pte.id_grado_curricular_actual, t.id_grado),
       COALESCE(pte.id_nivel_actual, n.id_nivel),
       pte.total_intentos, pte.total_aciertos, pte.total_errores, pte.porcentaje_aciertos,
       pte.racha_correctas, pte.racha_incorrectas, pte.estado_dominio,
       pte.tiempo_promedio_ms, pte.cambios_dificultad, pte.ultima_practica
FROM progreso_tema_estudiante pte
INNER JOIN temas t ON t.id_tema = pte.id_tema
INNER JOIN niveles_dificultad n ON n.codigo = 'facil' AND n.estado = 'activo'
WHERE NOT EXISTS (
    SELECT 1 FROM incidencias_contexto_progresion icp
    WHERE icp.id_usuario = pte.id_usuario
      AND icp.id_tema = pte.id_tema
      AND icp.tipo = 'progreso_historico_contexto_ambiguo'
)
  AND EXISTS (
    SELECT 1 FROM partidas_juego p
    WHERE p.id_usuario = pte.id_usuario AND p.id_tema = pte.id_tema AND p.tipo_contexto = 'personal'
)
ON DUPLICATE KEY UPDATE fecha_actualizacion = fecha_actualizacion;

INSERT INTO progreso_personal_catalogo (id_usuario, id_grado_desbloqueado)
SELECT DISTINCT ppt.id_usuario,
       (SELECT id_grado FROM grados WHERE codigo_grado = '4P' AND estado = 'activo' LIMIT 1)
FROM progreso_personal_tema ppt
WHERE NOT EXISTS (
    SELECT 1 FROM progreso_personal_catalogo ppc WHERE ppc.id_usuario = ppt.id_usuario
);

DROP PROCEDURE IF EXISTS mm_context_add_index;
DROP PROCEDURE IF EXISTS mm_context_add_column;
