USE tesis_matematica_app;

-- Guarda procedimientos deterministas para reutilizarlos exactamente después de un error.
DELIMITER $$

DROP PROCEDURE IF EXISTS mm_feedback_add_column$$
CREATE PROCEDURE mm_feedback_add_column(IN p_table VARCHAR(64))
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table
          AND COLUMN_NAME = 'explicacion_pasos'
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' ADD COLUMN explicacion_pasos JSON NULL AFTER explicacion');
        PREPARE statement FROM @sql;
        EXECUTE statement;
        DEALLOCATE PREPARE statement;
    END IF;
END$$

DELIMITER ;

CALL mm_feedback_add_column('ejercicios');
CALL mm_feedback_add_column('ejercicios_generados');

DROP PROCEDURE IF EXISTS mm_feedback_add_column;
