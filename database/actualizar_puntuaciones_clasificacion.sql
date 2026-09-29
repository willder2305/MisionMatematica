-- Migración idempotente: puntuación académica global por tema y clasificación.
-- La puntuación no comparte columnas con monedas, inventario ni recompensas.
USE tesis_matematica_app;

DELIMITER $$
DROP PROCEDURE IF EXISTS actualizar_puntuaciones_clasificacion$$
CREATE PROCEDURE actualizar_puntuaciones_clasificacion()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'progreso_tema_estudiante'
          AND COLUMN_NAME = 'puntos_acumulados'
    ) THEN
        ALTER TABLE progreso_tema_estudiante
            ADD COLUMN puntos_acumulados INT UNSIGNED NOT NULL DEFAULT 0 AFTER total_errores;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'progreso_tema_estudiante'
          AND COLUMN_NAME = 'aciertos_puntuados'
    ) THEN
        ALTER TABLE progreso_tema_estudiante
            ADD COLUMN aciertos_puntuados INT UNSIGNED NOT NULL DEFAULT 0 AFTER puntos_acumulados;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'progreso_tema_estudiante'
          AND INDEX_NAME = 'idx_progreso_tema_clasificacion'
    ) THEN
        ALTER TABLE progreso_tema_estudiante
            ADD INDEX idx_progreso_tema_clasificacion (id_tema, puntos_acumulados, id_usuario);
    END IF;
END$$
DELIMITER ;

CALL actualizar_puntuaciones_clasificacion();
DROP PROCEDURE IF EXISTS actualizar_puntuaciones_clasificacion;

-- Reconcilia el acumulado derivado de todos los intentos correctos registrados.
-- Puede ejecutarse otra vez sin duplicar puntos y no modifica intentos históricos.
UPDATE progreso_tema_estudiante
SET puntos_acumulados = 0,
    aciertos_puntuados = 0;

UPDATE progreso_tema_estudiante pte
INNER JOIN (
    SELECT p.id_usuario,
           COALESCE(eg.id_tema, e.id_tema) AS id_tema,
           COUNT(*) AS aciertos
    FROM intentos_juego i
    INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
    LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
    LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
    INNER JOIN usuarios u ON u.id_usuario = p.id_usuario
    INNER JOIN temas t ON t.id_tema = COALESCE(eg.id_tema, e.id_tema)
    WHERE i.es_correcta = 1
      AND COALESCE(eg.id_tema, e.id_tema) IS NOT NULL
    GROUP BY p.id_usuario, COALESCE(eg.id_tema, e.id_tema)
) historico
    ON historico.id_usuario = pte.id_usuario
   AND historico.id_tema = pte.id_tema
SET pte.aciertos_puntuados = historico.aciertos,
    pte.puntos_acumulados = historico.aciertos * 2;

INSERT INTO progreso_tema_estudiante
    (id_usuario, id_tema, puntos_acumulados, aciertos_puntuados)
SELECT historico.id_usuario,
       historico.id_tema,
       historico.aciertos * 2,
       historico.aciertos
FROM (
    SELECT p.id_usuario,
           COALESCE(eg.id_tema, e.id_tema) AS id_tema,
           COUNT(*) AS aciertos
    FROM intentos_juego i
    INNER JOIN partidas_juego p ON p.id_partida = i.id_partida
    LEFT JOIN ejercicios_generados eg ON eg.id_ejercicio_generado = i.id_ejercicio_generado
    LEFT JOIN ejercicios e ON e.id_ejercicio = i.id_ejercicio
    INNER JOIN usuarios u ON u.id_usuario = p.id_usuario
    INNER JOIN temas t ON t.id_tema = COALESCE(eg.id_tema, e.id_tema)
    WHERE i.es_correcta = 1
      AND COALESCE(eg.id_tema, e.id_tema) IS NOT NULL
    GROUP BY p.id_usuario, COALESCE(eg.id_tema, e.id_tema)
) historico
LEFT JOIN progreso_tema_estudiante pte
    ON pte.id_usuario = historico.id_usuario
   AND pte.id_tema = historico.id_tema
WHERE pte.id_progreso_tema_estudiante IS NULL;
