-- Migración: soporte de consultas por estudiante y tema para reportes globales.
-- Es idempotente y no modifica datos académicos ni usuarios.
USE tesis_matematica_app;

DELIMITER $$
DROP PROCEDURE IF EXISTS aplicar_indices_reportes_globales$$
CREATE PROCEDURE aplicar_indices_reportes_globales()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'partidas_juego'
          AND INDEX_NAME = 'idx_partidas_usuario_tema'
    ) THEN
        ALTER TABLE partidas_juego
            ADD INDEX idx_partidas_usuario_tema (id_usuario, id_tema, id_partida);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'intentos_juego'
          AND INDEX_NAME = 'idx_intentos_partida_fecha_id'
    ) THEN
        ALTER TABLE intentos_juego
            ADD INDEX idx_intentos_partida_fecha_id (id_partida, fecha_respuesta, id_intento);
    END IF;
END$$
DELIMITER ;

CALL aplicar_indices_reportes_globales();
DROP PROCEDURE aplicar_indices_reportes_globales;
