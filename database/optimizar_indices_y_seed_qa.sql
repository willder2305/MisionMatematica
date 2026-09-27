-- Migración: índices de consultas frecuentes y datos auxiliares de desarrollo.
-- Fecha: 2026-09-26.
-- Objetivo: acelerar filtros de partidas, intentos, inventario y actividades sin cambiar reglas de negocio.
-- Compatibilidad: idempotente; cada índice se crea solo cuando no existe.
USE tesis_matematica_app;

-- Indices compuestos basados en los filtros y ordenes usados por partidas,
-- intentos, decisiones, inventario, movimientos y actividades del estudiante.
DELIMITER $$
DROP PROCEDURE IF EXISTS aplicar_indices_optimizacion$$
CREATE PROCEDURE aplicar_indices_optimizacion()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'partidas_juego'
          AND INDEX_NAME = 'idx_partidas_usuario_estado_actividad'
    ) THEN
        ALTER TABLE partidas_juego
            ADD INDEX idx_partidas_usuario_estado_actividad (id_usuario, estado, fecha_ultima_actividad);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'intentos_juego'
          AND INDEX_NAME = 'idx_intentos_partida_fecha'
    ) THEN
        ALTER TABLE intentos_juego ADD INDEX idx_intentos_partida_fecha (id_partida, fecha_respuesta);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'decisiones_agente'
          AND INDEX_NAME = 'idx_decisiones_partida_fecha'
    ) THEN
        ALTER TABLE decisiones_agente ADD INDEX idx_decisiones_partida_fecha (id_partida, fecha_decision);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas'
          AND INDEX_NAME = 'idx_movimientos_usuario_fecha'
    ) THEN
        ALTER TABLE movimientos_monedas ADD INDEX idx_movimientos_usuario_fecha (id_usuario, fecha);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario_items'
          AND INDEX_NAME = 'idx_usuario_items_usuario_estado'
    ) THEN
        ALTER TABLE usuario_items ADD INDEX idx_usuario_items_usuario_estado (id_usuario, estado);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'estudiante_asignaciones'
          AND INDEX_NAME = 'idx_estudiante_asignaciones_estudiante_estado'
    ) THEN
        ALTER TABLE estudiante_asignaciones
            ADD INDEX idx_estudiante_asignaciones_estudiante_estado (id_estudiante, estado, fecha_ultima_actividad);
    END IF;
END$$
DELIMITER ;

CALL aplicar_indices_optimizacion();
DROP PROCEDURE aplicar_indices_optimizacion;

-- El tipo se extiende para registrar la semilla local sin sobrecargar ajustes reales.
ALTER TABLE movimientos_monedas
    MODIFY COLUMN tipo ENUM(
        'compra', 'recompensa', 'ajuste',
        'recompensa_partida', 'recompensa_partida_perfecta',
        'continuar_partida', 'compra_personaje', 'compra_mapa', 'ajuste_pruebas'
    ) NOT NULL;
