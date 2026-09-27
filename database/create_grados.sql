CREATE TABLE IF NOT EXISTS grados (
    id_grado INT AUTO_INCREMENT PRIMARY KEY,
    codigo_grado VARCHAR(20) NOT NULL,
    nombre_grado VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NULL,
    orden_visualizacion INT NOT NULL DEFAULT 1,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_grados_codigo UNIQUE (codigo_grado),
    CONSTRAINT uk_grados_nombre UNIQUE (nombre_grado)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_estructura_grados$$

CREATE PROCEDURE actualizar_estructura_grados()
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'grados'
          AND COLUMN_NAME = 'codigo_grado'
          AND CHARACTER_MAXIMUM_LENGTH < 20
    ) THEN
        ALTER TABLE grados MODIFY codigo_grado VARCHAR(20) NOT NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'grados'
          AND COLUMN_NAME = 'descripcion'
    ) THEN
        ALTER TABLE grados ADD COLUMN descripcion VARCHAR(255) NULL AFTER nombre_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'grados'
          AND COLUMN_NAME = 'orden_visualizacion'
    ) THEN
        ALTER TABLE grados ADD COLUMN orden_visualizacion INT NOT NULL DEFAULT 1 AFTER descripcion;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'grados'
          AND COLUMN_NAME = 'fecha_modificacion'
    ) THEN
        ALTER TABLE grados ADD COLUMN fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP AFTER fecha_creacion;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'grados'
          AND COLUMN_NAME = 'nombre_grado'
          AND NON_UNIQUE = 0
    ) THEN
        ALTER TABLE grados ADD CONSTRAINT uk_grados_nombre UNIQUE (nombre_grado);
    END IF;
END$$

DELIMITER ;

CALL actualizar_estructura_grados();

DROP PROCEDURE IF EXISTS actualizar_estructura_grados;

INSERT INTO grados
    (codigo_grado, nombre_grado, descripcion, orden_visualizacion)
SELECT '4P', 'Cuarto', 'Cuarto grado base', 1
WHERE NOT EXISTS (
    SELECT 1 FROM grados WHERE codigo_grado = '4P'
);

INSERT INTO grados
    (codigo_grado, nombre_grado, descripcion, orden_visualizacion)
SELECT '5P', 'Quinto', 'Quinto grado base', 2
WHERE NOT EXISTS (
    SELECT 1 FROM grados WHERE codigo_grado = '5P'
);

INSERT INTO grados
    (codigo_grado, nombre_grado, descripcion, orden_visualizacion)
SELECT '6P', 'Sexto', 'Sexto grado base', 3
WHERE NOT EXISTS (
    SELECT 1 FROM grados WHERE codigo_grado = '6P'
);

UPDATE grados
SET descripcion = CASE codigo_grado
        WHEN '4P' THEN 'Cuarto grado base'
        WHEN '5P' THEN 'Quinto grado base'
        WHEN '6P' THEN 'Sexto grado base'
        ELSE descripcion
    END,
    nombre_grado = CASE codigo_grado
        WHEN '4P' THEN 'Cuarto'
        WHEN '5P' THEN 'Quinto'
        WHEN '6P' THEN 'Sexto'
        ELSE nombre_grado
    END,
    estado = CASE codigo_grado
        WHEN '4P' THEN 'activo'
        WHEN '5P' THEN 'activo'
        WHEN '6P' THEN 'activo'
        ELSE estado
    END,
    orden_visualizacion = CASE codigo_grado
        WHEN '4P' THEN 1
        WHEN '5P' THEN 2
        WHEN '6P' THEN 3
        ELSE orden_visualizacion
    END
WHERE codigo_grado IN ('4P', '5P', '6P');
