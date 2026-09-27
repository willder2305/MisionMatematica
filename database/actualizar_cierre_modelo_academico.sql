-- Migracion incremental: cierre del modelo academico institucional.
-- Ejecutar despues de un backup logico de la base existente.

CREATE TABLE IF NOT EXISTS migration_issues (
    id_issue INT AUTO_INCREMENT PRIMARY KEY,
    entidad VARCHAR(80) NOT NULL,
    id_registro INT NULL,
    tipo_problema VARCHAR(120) NOT NULL,
    detalle JSON NULL,
    resuelto TINYINT(1) NOT NULL DEFAULT 0,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_migration_issue (entidad, id_registro, tipo_problema)
);

CREATE TABLE IF NOT EXISTS migration_report (
    id_report INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    metrica VARCHAR(120) NOT NULL,
    valor INT NOT NULL DEFAULT 0,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_migration_report (nombre, metrica)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS mm_add_column_if_missing$$
CREATE PROCEDURE mm_add_column_if_missing(
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

CALL mm_add_column_if_missing('docente_secciones', 'fecha_fin', 'TIMESTAMP NULL DEFAULT NULL AFTER fecha_asignacion');
CALL mm_add_column_if_missing('docente_secciones', 'fecha_modificacion', 'TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_fin');

CALL mm_add_column_if_missing('grupo_secciones', 'estado', 'ENUM(''activo'', ''inactivo'') NOT NULL DEFAULT ''activo'' AFTER id_seccion');
CALL mm_add_column_if_missing('grupo_secciones', 'fecha_fin', 'TIMESTAMP NULL DEFAULT NULL AFTER fecha_creacion');
CALL mm_add_column_if_missing('grupo_secciones', 'fecha_modificacion', 'TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_fin');

CALL mm_add_column_if_missing('asignaciones', 'id_institucion_grado', 'INT NULL AFTER id_docente');
ALTER TABLE asignaciones MODIFY id_grupo INT NULL;

CALL mm_add_column_if_missing('asignacion_temas', 'estado', 'ENUM(''activo'', ''inactivo'') NOT NULL DEFAULT ''activo'' AFTER id_tema');
CALL mm_add_column_if_missing('asignacion_temas', 'fecha_fin', 'TIMESTAMP NULL DEFAULT NULL AFTER fecha_creacion');
CALL mm_add_column_if_missing('asignacion_temas', 'fecha_modificacion', 'TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_fin');

CALL mm_add_column_if_missing('asignacion_ejercicios', 'estado', 'ENUM(''activo'', ''inactivo'') NOT NULL DEFAULT ''activo'' AFTER id_ejercicio');
CALL mm_add_column_if_missing('asignacion_ejercicios', 'fecha_fin', 'TIMESTAMP NULL DEFAULT NULL AFTER fecha_creacion');
CALL mm_add_column_if_missing('asignacion_ejercicios', 'fecha_modificacion', 'TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_fin');

CALL mm_add_column_if_missing('opciones_ejercicio', 'estado', 'ENUM(''activo'', ''inactivo'') NOT NULL DEFAULT ''activo'' AFTER orden_visualizacion');
CALL mm_add_column_if_missing('opciones_ejercicio', 'fecha_fin', 'TIMESTAMP NULL DEFAULT NULL AFTER estado');
CALL mm_add_column_if_missing('opciones_ejercicio', 'fecha_modificacion', 'TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_fin');

CALL mm_add_fk_if_missing(
    'asignaciones',
    'fk_asignaciones_institucion_grado',
    'FOREIGN KEY (id_institucion_grado) REFERENCES institucion_grados(id_institucion_grado)'
);

CALL mm_add_index_if_missing('institucion_grados', 'idx_institucion_grados_institucion', 'INDEX idx_institucion_grados_institucion (id_institucion)');
CALL mm_add_index_if_missing('institucion_grados', 'idx_institucion_grados_base', 'INDEX idx_institucion_grados_base (id_grado_base)');
CALL mm_add_index_if_missing('secciones', 'idx_secciones_institucion_grado', 'INDEX idx_secciones_institucion_grado (id_institucion_grado)');
CALL mm_add_index_if_missing('docente_secciones', 'idx_docente_secciones_docente', 'INDEX idx_docente_secciones_docente (id_docente)');
CALL mm_add_index_if_missing('docente_secciones', 'idx_docente_secciones_seccion', 'INDEX idx_docente_secciones_seccion (id_seccion)');
CALL mm_add_index_if_missing('asignaciones', 'idx_asignaciones_institucion_grado', 'INDEX idx_asignaciones_institucion_grado (id_institucion_grado)');
CALL mm_add_index_if_missing('asignaciones', 'idx_asignaciones_seccion', 'INDEX idx_asignaciones_seccion (id_seccion)');
CALL mm_add_index_if_missing('intentos_juego', 'idx_intentos_fecha', 'INDEX idx_intentos_fecha (fecha_respuesta)');
CALL mm_add_index_if_missing('partidas_juego', 'idx_partidas_usuario', 'INDEX idx_partidas_usuario (id_usuario)');
CALL mm_add_index_if_missing('opciones_ejercicio', 'uk_opciones_ejercicio_orden', 'UNIQUE KEY uk_opciones_ejercicio_orden (id_ejercicio, orden_visualizacion)');

UPDATE grupos gr
INNER JOIN docente_grados dg
    ON dg.id_usuario_docente = gr.id_docente
   AND dg.id_grado = gr.id_grado
   AND dg.estado = 'activo'
SET gr.id_institucion_grado = dg.id_institucion_grado
WHERE gr.id_institucion_grado IS NULL
  AND dg.id_institucion_grado IS NOT NULL;

UPDATE secciones s
INNER JOIN grupo_secciones gs ON gs.id_seccion = s.id_seccion
INNER JOIN grupos gr ON gr.id_grupo = gs.id_grupo
SET s.id_institucion_grado = gr.id_institucion_grado
WHERE s.id_institucion_grado IS NULL
  AND gr.id_institucion_grado IS NOT NULL;

UPDATE secciones s
INNER JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion
INNER JOIN docente_grados dg
    ON dg.id_usuario_docente = ds.id_docente
   AND dg.id_grado = s.id_grado
   AND dg.estado = 'activo'
SET s.id_institucion_grado = dg.id_institucion_grado
WHERE s.id_institucion_grado IS NULL
  AND dg.id_institucion_grado IS NOT NULL;

UPDATE secciones
SET nombre_seccion = CASE
    WHEN UPPER(TRIM(nombre_seccion)) = 'A' THEN 'A'
    WHEN UPPER(TRIM(nombre_seccion)) = 'B' THEN 'B'
    WHEN UPPER(TRIM(nombre_seccion)) = 'C' THEN 'C'
    WHEN UPPER(TRIM(nombre_seccion)) = 'D' THEN 'D'
    WHEN LOWER(TRIM(nombre_seccion)) IN ('unica', 'única') THEN 'Única'
    ELSE nombre_seccion
END;

INSERT IGNORE INTO migration_issues (entidad, id_registro, tipo_problema, detalle)
SELECT 'secciones', s.id_seccion, 'nombre_historico_invalido',
       JSON_OBJECT('nombre_seccion', s.nombre_seccion, 'id_grado', s.id_grado)
FROM secciones s
WHERE s.nombre_seccion NOT IN ('A', 'B', 'C', 'D', 'Única');

UPDATE secciones s
LEFT JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion AND ds.estado = 'activo'
LEFT JOIN grupo_secciones gs ON gs.id_seccion = s.id_seccion AND gs.estado = 'activo'
LEFT JOIN pines_acceso p ON p.id_seccion = s.id_seccion AND p.estado = 'activo'
LEFT JOIN asignaciones a ON a.id_seccion = s.id_seccion AND a.estado IN ('borrador', 'activa', 'pausada')
SET s.estado = 'inactivo'
WHERE s.id_institucion_grado IS NULL
  AND s.estado = 'activo'
  AND (s.nombre_seccion NOT IN ('A', 'B', 'C', 'D', 'Única') OR s.nombre_seccion IS NULL)
  AND ds.id_docente_seccion IS NULL
  AND gs.id_grupo_seccion IS NULL
  AND p.id_pin IS NULL
  AND a.id_asignacion IS NULL;

UPDATE secciones s
LEFT JOIN docente_secciones ds ON ds.id_seccion = s.id_seccion AND ds.estado = 'activo'
LEFT JOIN grupo_secciones gs ON gs.id_seccion = s.id_seccion AND gs.estado = 'activo'
LEFT JOIN pines_acceso p ON p.id_seccion = s.id_seccion AND p.estado = 'activo'
LEFT JOIN asignaciones a ON a.id_seccion = s.id_seccion AND a.estado IN ('borrador', 'activa', 'pausada')
SET s.estado = 'inactivo'
WHERE s.id_institucion_grado IS NULL
  AND s.estado = 'activo'
  AND ds.id_docente_seccion IS NULL
  AND gs.id_grupo_seccion IS NULL
  AND p.id_pin IS NULL
  AND a.id_asignacion IS NULL;

INSERT INTO secciones (id_grado, id_institucion_grado, nombre_seccion, descripcion, estado)
SELECT ig.id_grado_base, dg.id_institucion_grado, 'Única', 'Seccion unica generada por migracion', 'activo'
FROM docente_grados dg
INNER JOIN institucion_grados ig ON ig.id_institucion_grado = dg.id_institucion_grado
WHERE dg.estado = 'activo'
  AND NOT EXISTS (
      SELECT 1
      FROM docente_secciones ds
      INNER JOIN secciones s ON s.id_seccion = ds.id_seccion
      WHERE ds.id_docente = dg.id_usuario_docente
        AND ds.estado = 'activo'
        AND s.estado = 'activo'
        AND s.id_institucion_grado = dg.id_institucion_grado
  )
  AND NOT EXISTS (
      SELECT 1
      FROM secciones sx
      WHERE sx.id_institucion_grado = dg.id_institucion_grado
        AND sx.nombre_seccion = 'Única'
  );

INSERT INTO docente_secciones (id_docente, id_seccion, estado)
SELECT dg.id_usuario_docente, s.id_seccion, 'activo'
FROM docente_grados dg
INNER JOIN secciones s
    ON s.id_institucion_grado = dg.id_institucion_grado
   AND s.nombre_seccion = 'Única'
WHERE dg.estado = 'activo'
  AND NOT EXISTS (
      SELECT 1
      FROM docente_secciones ds
      INNER JOIN secciones sx ON sx.id_seccion = ds.id_seccion
      WHERE ds.id_docente = dg.id_usuario_docente
        AND ds.estado = 'activo'
        AND sx.estado = 'activo'
        AND sx.id_institucion_grado = dg.id_institucion_grado
  )
ON DUPLICATE KEY UPDATE estado = 'activo', fecha_fin = NULL;

UPDATE asignaciones a
INNER JOIN secciones s ON s.id_seccion = a.id_seccion
SET a.id_institucion_grado = s.id_institucion_grado
WHERE a.id_institucion_grado IS NULL
  AND s.id_institucion_grado IS NOT NULL;

UPDATE asignaciones a
INNER JOIN grupos gr ON gr.id_grupo = a.id_grupo
SET a.id_institucion_grado = gr.id_institucion_grado
WHERE a.id_institucion_grado IS NULL
  AND gr.id_institucion_grado IS NOT NULL;

UPDATE asignaciones a
INNER JOIN (
    SELECT gs.id_grupo, MIN(gs.id_seccion) AS id_seccion, COUNT(*) AS total
    FROM grupo_secciones gs
    INNER JOIN secciones s ON s.id_seccion = gs.id_seccion
    WHERE gs.estado = 'activo'
      AND s.estado = 'activo'
    GROUP BY gs.id_grupo
    HAVING total = 1
) unica ON unica.id_grupo = a.id_grupo
SET a.id_seccion = unica.id_seccion
WHERE a.id_seccion IS NULL
  AND a.id_grupo IS NOT NULL;

UPDATE asignaciones a
INNER JOIN secciones s ON s.id_seccion = a.id_seccion
SET a.id_institucion_grado = s.id_institucion_grado
WHERE a.id_institucion_grado IS NULL
  AND s.id_institucion_grado IS NOT NULL;

UPDATE asignaciones a
INNER JOIN grupos gr ON gr.id_grupo = a.id_grupo
INNER JOIN secciones s
    ON s.id_institucion_grado = gr.id_institucion_grado
   AND s.nombre_seccion = 'Única'
   AND s.estado = 'activo'
SET a.id_seccion = s.id_seccion,
    a.id_institucion_grado = gr.id_institucion_grado
WHERE a.id_seccion IS NULL
  AND a.id_institucion_grado IS NULL;

UPDATE perfiles_estudiante pe
INNER JOIN estudiantes_grupos eg ON eg.id_usuario_estudiante = pe.id_usuario AND eg.estado = 'activo'
INNER JOIN grupos gr ON gr.id_grupo = eg.id_grupo
LEFT JOIN secciones s_directa ON s_directa.id_seccion = eg.id_seccion
LEFT JOIN (
    SELECT gs.id_grupo, MIN(gs.id_seccion) AS id_seccion, COUNT(*) AS total
    FROM grupo_secciones gs
    INNER JOIN secciones s ON s.id_seccion = gs.id_seccion
    WHERE gs.estado = 'activo'
      AND s.estado = 'activo'
    GROUP BY gs.id_grupo
    HAVING total = 1
) s_unica ON s_unica.id_grupo = eg.id_grupo
LEFT JOIN secciones s_resuelta ON s_resuelta.id_seccion = COALESCE(eg.id_seccion, s_unica.id_seccion)
LEFT JOIN institucion_grados ig ON ig.id_institucion_grado = COALESCE(s_directa.id_institucion_grado, s_resuelta.id_institucion_grado, gr.id_institucion_grado)
SET pe.id_grado = ig.id_grado_base,
    pe.id_institucion = ig.id_institucion,
    pe.id_institucion_grado = ig.id_institucion_grado,
    pe.id_seccion = COALESCE(eg.id_seccion, s_unica.id_seccion)
WHERE pe.modalidad = 'grupo_educativo'
  AND ig.id_institucion_grado IS NOT NULL;

INSERT IGNORE INTO migration_issues (entidad, id_registro, tipo_problema, detalle)
SELECT 'secciones', s.id_seccion, 'sin_grado_institucional',
       JSON_OBJECT('id_grado', s.id_grado, 'nombre_seccion', s.nombre_seccion, 'estado', s.estado)
FROM secciones s
WHERE s.estado = 'activo'
  AND s.id_institucion_grado IS NULL;

INSERT IGNORE INTO migration_issues (entidad, id_registro, tipo_problema, detalle)
SELECT 'asignaciones', a.id_asignacion, 'sin_contexto_institucional',
       JSON_OBJECT('id_grupo', a.id_grupo, 'id_seccion', a.id_seccion, 'estado', a.estado)
FROM asignaciones a
WHERE a.estado IN ('borrador', 'activa', 'pausada')
  AND (a.id_institucion_grado IS NULL OR a.id_seccion IS NULL);

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'secciones_total', COUNT(*) FROM secciones
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'secciones_migradas', COUNT(*) FROM secciones WHERE id_institucion_grado IS NOT NULL
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'secciones_activas_sin_grado_institucional', COUNT(*) FROM secciones WHERE estado = 'activo' AND id_institucion_grado IS NULL
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'asignaciones_total', COUNT(*) FROM asignaciones
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'asignaciones_migradas', COUNT(*) FROM asignaciones WHERE id_institucion_grado IS NOT NULL AND id_seccion IS NOT NULL
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

INSERT INTO migration_report (nombre, metrica, valor)
SELECT 'cierre_modelo_academico', 'asignaciones_activas_sin_contexto', COUNT(*) FROM asignaciones WHERE estado IN ('borrador', 'activa', 'pausada') AND (id_institucion_grado IS NULL OR id_seccion IS NULL)
ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha = CURRENT_TIMESTAMP;

DROP PROCEDURE IF EXISTS mm_add_column_if_missing;
DROP PROCEDURE IF EXISTS mm_add_index_if_missing;
DROP PROCEDURE IF EXISTS mm_add_fk_if_missing;
