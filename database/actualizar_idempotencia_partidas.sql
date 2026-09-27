USE tesis_matematica_app;

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_idempotencia_partidas$$

CREATE PROCEDURE actualizar_idempotencia_partidas()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'request_id'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN request_id VARCHAR(80) NULL AFTER id_tema;
    END IF;

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

CALL actualizar_idempotencia_partidas();
DROP PROCEDURE IF EXISTS actualizar_idempotencia_partidas;
