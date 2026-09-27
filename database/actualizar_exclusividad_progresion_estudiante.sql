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

DROP PROCEDURE IF EXISTS mm_drop_index_if_exists$$
CREATE PROCEDURE mm_drop_index_if_exists(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64)
)
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND INDEX_NAME = p_index_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table_name, ' DROP INDEX ', p_index_name);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_fk_if_missing$$
CREATE PROCEDURE mm_add_fk_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_constraint_name VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND CONSTRAINT_NAME = p_constraint_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table_name, ' ADD CONSTRAINT ', p_constraint_name, ' ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_unique_docente_seccion_activa$$
CREATE PROCEDURE mm_add_unique_docente_seccion_activa()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'docente_secciones'
          AND INDEX_NAME = 'uk_docente_seccion_activa'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM docente_secciones
        WHERE estado = 'activo'
        GROUP BY id_seccion
        HAVING COUNT(*) > 1
    ) THEN
        ALTER TABLE docente_secciones
            ADD UNIQUE KEY uk_docente_seccion_activa (id_seccion_activa);
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_unique_estudiante_matricula_activa$$
CREATE PROCEDURE mm_add_unique_estudiante_matricula_activa()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'estudiantes_grupos'
          AND INDEX_NAME = 'uk_estudiante_matricula_activa'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM estudiantes_grupos
        WHERE estado = 'activo'
        GROUP BY id_usuario_estudiante
        HAVING COUNT(*) > 1
    ) THEN
        ALTER TABLE estudiantes_grupos
            ADD UNIQUE KEY uk_estudiante_matricula_activa (id_usuario_estudiante_activo);
    END IF;
END$$

DELIMITER ;

CREATE TABLE IF NOT EXISTS incidencias_migracion (
    id_incidencia INT AUTO_INCREMENT PRIMARY KEY,
    entidad VARCHAR(80) NOT NULL,
    entidad_id INT NULL,
    tipo VARCHAR(120) NOT NULL,
    detalle_json JSON NOT NULL,
    estado ENUM('pendiente', 'resuelta') NOT NULL DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion TIMESTAMP NULL DEFAULT NULL
);

INSERT INTO incidencias_migracion (entidad, entidad_id, tipo, detalle_json)
SELECT
    'docente_secciones',
    ds.id_seccion,
    'docentes_activos_duplicados_por_seccion',
    JSON_OBJECT(
        'id_seccion', ds.id_seccion,
        'docentes', GROUP_CONCAT(ds.id_docente ORDER BY ds.fecha_asignacion ASC),
        'relaciones', GROUP_CONCAT(ds.id_docente_seccion ORDER BY ds.fecha_asignacion ASC)
    )
FROM docente_secciones ds
WHERE ds.estado = 'activo'
GROUP BY ds.id_seccion
HAVING COUNT(*) > 1
   AND NOT EXISTS (
       SELECT 1
       FROM incidencias_migracion im
       WHERE im.entidad = 'docente_secciones'
         AND im.entidad_id = ds.id_seccion
         AND im.tipo = 'docentes_activos_duplicados_por_seccion'
         AND im.estado = 'pendiente'
   );

INSERT INTO incidencias_migracion (entidad, entidad_id, tipo, detalle_json)
SELECT
    'estudiantes_grupos',
    eg.id_usuario_estudiante,
    'matriculas_activas_duplicadas',
    JSON_OBJECT(
        'id_usuario_estudiante', eg.id_usuario_estudiante,
        'grupos', GROUP_CONCAT(eg.id_grupo ORDER BY eg.fecha_ingreso ASC),
        'relaciones', GROUP_CONCAT(eg.id_estudiante_grupo ORDER BY eg.fecha_ingreso ASC)
    )
FROM estudiantes_grupos eg
WHERE eg.estado = 'activo'
GROUP BY eg.id_usuario_estudiante
HAVING COUNT(*) > 1
   AND NOT EXISTS (
       SELECT 1
       FROM incidencias_migracion im
       WHERE im.entidad = 'estudiantes_grupos'
         AND im.entidad_id = eg.id_usuario_estudiante
         AND im.tipo = 'matriculas_activas_duplicadas'
         AND im.estado = 'pendiente'
   );

CALL mm_add_column_if_missing(
    'docente_secciones',
    'id_seccion_activa',
    'INT GENERATED ALWAYS AS (CASE WHEN estado = ''activo'' THEN id_seccion ELSE NULL END) STORED AFTER id_seccion'
);

CALL mm_add_column_if_missing(
    'estudiantes_grupos',
    'id_usuario_estudiante_activo',
    'INT GENERATED ALWAYS AS (CASE WHEN estado = ''activo'' THEN id_usuario_estudiante ELSE NULL END) STORED AFTER id_usuario_estudiante'
);

CALL mm_add_index_if_missing(
    'estudiantes_grupos',
    'idx_estudiantes_grupos_usuario',
    'INDEX idx_estudiantes_grupos_usuario (id_usuario_estudiante)'
);

CALL mm_drop_index_if_exists('estudiantes_grupos', 'uk_estudiante_grupo_activo');

CALL mm_add_column_if_missing(
    'progreso_tema_estudiante',
    'id_grado_curricular_actual',
    'INT NULL AFTER id_tema'
);

CALL mm_add_column_if_missing(
    'progreso_tema_estudiante',
    'racha_correctas',
    'INT NOT NULL DEFAULT 0 AFTER porcentaje_aciertos'
);

CALL mm_add_column_if_missing(
    'progreso_tema_estudiante',
    'racha_incorrectas',
    'INT NOT NULL DEFAULT 0 AFTER racha_correctas'
);

CALL mm_add_column_if_missing(
    'progreso_tema_estudiante',
    'estado_dominio',
    'ENUM(''inicial'', ''en_progreso'', ''dominado'') NOT NULL DEFAULT ''inicial'' AFTER racha_incorrectas'
);

CALL mm_add_fk_if_missing(
    'progreso_tema_estudiante',
    'fk_progreso_tema_grado_curricular',
    'FOREIGN KEY (id_grado_curricular_actual) REFERENCES grados(id_grado)'
);

CALL mm_add_index_if_missing(
    'progreso_tema_estudiante',
    'idx_progreso_tema_grado_curricular',
    'INDEX idx_progreso_tema_grado_curricular (id_grado_curricular_actual)'
);

CREATE TABLE IF NOT EXISTS promociones_curriculares_tema (
    id_promocion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tema_anterior INT NOT NULL,
    id_tema_nuevo INT NOT NULL,
    id_grado_anterior INT NOT NULL,
    id_grado_nuevo INT NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    metricas_json JSON NOT NULL,
    fecha_promocion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_promociones_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_promociones_tema_anterior
        FOREIGN KEY (id_tema_anterior)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_promociones_tema_nuevo
        FOREIGN KEY (id_tema_nuevo)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_promociones_grado_anterior
        FOREIGN KEY (id_grado_anterior)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_promociones_grado_nuevo
        FOREIGN KEY (id_grado_nuevo)
        REFERENCES grados(id_grado)
);

CALL mm_add_index_if_missing(
    'promociones_curriculares_tema',
    'idx_promociones_usuario_tema',
    'INDEX idx_promociones_usuario_tema (id_usuario, id_tema_anterior, id_tema_nuevo)'
);

CALL mm_add_unique_docente_seccion_activa();
CALL mm_add_unique_estudiante_matricula_activa();

SELECT
    'exclusividad_docente_seccion' AS verificacion,
    COUNT(*) AS conflictos_pendientes
FROM (
    SELECT id_seccion
    FROM docente_secciones
    WHERE estado = 'activo'
    GROUP BY id_seccion
    HAVING COUNT(*) > 1
) conflictos;

SELECT
    'matricula_estudiante_activa' AS verificacion,
    COUNT(*) AS conflictos_pendientes
FROM (
    SELECT id_usuario_estudiante
    FROM estudiantes_grupos
    WHERE estado = 'activo'
    GROUP BY id_usuario_estudiante
    HAVING COUNT(*) > 1
) conflictos;

DROP PROCEDURE IF EXISTS mm_add_unique_estudiante_matricula_activa;
DROP PROCEDURE IF EXISTS mm_add_unique_docente_seccion_activa;
DROP PROCEDURE IF EXISTS mm_add_fk_if_missing;
DROP PROCEDURE IF EXISTS mm_drop_index_if_exists;
DROP PROCEDURE IF EXISTS mm_add_index_if_missing;
DROP PROCEDURE IF EXISTS mm_add_column_if_missing;
