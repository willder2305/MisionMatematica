-- Corrige restricciones legacy que impiden crear secciones A-D por institucion.
-- Es incremental: conserva usuarios, partidas, intentos, plantillas y reportes.

USE tesis_matematica_app;

DELIMITER $$

DROP PROCEDURE IF EXISTS mm_drop_index_if_columns$$
CREATE PROCEDURE mm_drop_index_if_columns(
    IN p_table VARCHAR(64),
    IN p_index VARCHAR(64),
    IN p_columns VARCHAR(255)
)
BEGIN
    SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ',')
    INTO @actual_columns
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table
      AND INDEX_NAME = p_index;

    IF @actual_columns = p_columns THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' DROP INDEX ', p_index);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_index_if_missing$$
CREATE PROCEDURE mm_add_index_if_missing(
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
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DROP PROCEDURE IF EXISTS mm_add_fk_if_missing$$
CREATE PROCEDURE mm_add_fk_if_missing(
    IN p_table VARCHAR(64),
    IN p_constraint VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table
          AND CONSTRAINT_NAME = p_constraint
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' ADD CONSTRAINT ', p_constraint, ' ', p_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DELIMITER ;

CALL mm_add_index_if_missing(
    'secciones',
    'idx_secciones_grado',
    'INDEX idx_secciones_grado (id_grado)'
);
CALL mm_drop_index_if_columns('secciones', 'uk_grado_seccion', 'id_grado,nombre_seccion');
CALL mm_add_index_if_missing(
    'secciones',
    'uk_grado_seccion',
    'UNIQUE KEY uk_grado_seccion (id_grado, id_institucion_grado, nombre_seccion)'
);
CALL mm_add_index_if_missing(
    'secciones',
    'uk_institucion_grado_seccion',
    'UNIQUE KEY uk_institucion_grado_seccion (id_institucion_grado, nombre_seccion)'
);
CALL mm_add_index_if_missing(
    'secciones',
    'idx_secciones_institucion_grado',
    'INDEX idx_secciones_institucion_grado (id_institucion_grado)'
);
CALL mm_add_fk_if_missing(
    'secciones',
    'fk_secciones_institucion_grados',
    'FOREIGN KEY (id_institucion_grado) REFERENCES institucion_grados(id_institucion_grado)'
);
CALL mm_add_fk_if_missing(
    'perfiles_docente',
    'fk_perfiles_docente_institucion',
    'FOREIGN KEY (id_institucion) REFERENCES instituciones(id_institucion)'
);

DROP PROCEDURE IF EXISTS mm_drop_index_if_columns;
DROP PROCEDURE IF EXISTS mm_add_index_if_missing;
DROP PROCEDURE IF EXISTS mm_add_fk_if_missing;
