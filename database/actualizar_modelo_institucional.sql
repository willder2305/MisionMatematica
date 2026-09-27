USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS instituciones (
    id_institucion INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(180) NOT NULL,
    nombre_normalizado VARCHAR(180) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_instituciones_nombre_normalizado UNIQUE (nombre_normalizado)
);

CREATE TABLE IF NOT EXISTS institucion_grados (
    id_institucion_grado INT AUTO_INCREMENT PRIMARY KEY,
    id_institucion INT NOT NULL,
    id_grado_base INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_institucion_grado_base UNIQUE (id_institucion, id_grado_base),
    CONSTRAINT fk_institucion_grados_institucion FOREIGN KEY (id_institucion) REFERENCES instituciones(id_institucion),
    CONSTRAINT fk_institucion_grados_grado_base FOREIGN KEY (id_grado_base) REFERENCES grados(id_grado)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS actualizar_modelo_institucional$$
CREATE PROCEDURE actualizar_modelo_institucional()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'perfiles_docente' AND COLUMN_NAME = 'id_institucion'
    ) THEN
        ALTER TABLE perfiles_docente ADD COLUMN id_institucion INT NULL AFTER id_usuario;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'perfiles_estudiante' AND COLUMN_NAME = 'id_institucion'
    ) THEN
        ALTER TABLE perfiles_estudiante ADD COLUMN id_institucion INT NULL AFTER id_grado;
        ALTER TABLE perfiles_estudiante ADD COLUMN id_institucion_grado INT NULL AFTER id_institucion;
        ALTER TABLE perfiles_estudiante ADD COLUMN id_seccion INT NULL AFTER id_institucion_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'docente_grados' AND COLUMN_NAME = 'id_institucion_grado'
    ) THEN
        ALTER TABLE docente_grados ADD COLUMN id_institucion_grado INT NULL AFTER id_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'docente_grados' AND COLUMN_NAME = 'estado'
    ) THEN
        ALTER TABLE docente_grados ADD COLUMN estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo' AFTER id_institucion_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'docente_grados' AND COLUMN_NAME = 'fecha_asignacion'
    ) THEN
        ALTER TABLE docente_grados ADD COLUMN fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER estado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'secciones' AND COLUMN_NAME = 'id_institucion_grado'
    ) THEN
        ALTER TABLE secciones ADD COLUMN id_institucion_grado INT NULL AFTER id_grado;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grupos' AND COLUMN_NAME = 'id_institucion_grado'
    ) THEN
        ALTER TABLE grupos ADD COLUMN id_institucion_grado INT NULL AFTER id_grado;
    END IF;
END$$

DELIMITER ;

CALL actualizar_modelo_institucional();
DROP PROCEDURE IF EXISTS actualizar_modelo_institucional;

UPDATE grados
SET nombre_grado = 'Cuarto', descripcion = 'Cuarto grado base', orden_visualizacion = 1, estado = 'activo'
WHERE codigo_grado = '4P';

UPDATE grados
SET nombre_grado = 'Quinto', descripcion = 'Quinto grado base', orden_visualizacion = 2, estado = 'activo'
WHERE codigo_grado = '5P';

UPDATE grados
SET nombre_grado = 'Sexto', descripcion = 'Sexto grado base', orden_visualizacion = 3, estado = 'activo'
WHERE codigo_grado = '6P';

INSERT INTO grados (codigo_grado, nombre_grado, descripcion, orden_visualizacion, estado)
SELECT '4P', 'Cuarto', 'Cuarto grado base', 1, 'activo'
WHERE NOT EXISTS (SELECT 1 FROM grados WHERE codigo_grado = '4P');

INSERT INTO grados (codigo_grado, nombre_grado, descripcion, orden_visualizacion, estado)
SELECT '5P', 'Quinto', 'Quinto grado base', 2, 'activo'
WHERE NOT EXISTS (SELECT 1 FROM grados WHERE codigo_grado = '5P');

INSERT INTO grados (codigo_grado, nombre_grado, descripcion, orden_visualizacion, estado)
SELECT '6P', 'Sexto', 'Sexto grado base', 3, 'activo'
WHERE NOT EXISTS (SELECT 1 FROM grados WHERE codigo_grado = '6P');

CREATE TABLE IF NOT EXISTS docente_secciones (
    id_docente_seccion INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_seccion INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_docente_seccion UNIQUE (id_docente, id_seccion),
    CONSTRAINT fk_docente_secciones_docente FOREIGN KEY (id_docente) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_docente_secciones_seccion FOREIGN KEY (id_seccion) REFERENCES secciones(id_seccion)
);

INSERT INTO instituciones (nombre, nombre_normalizado, descripcion, estado)
SELECT DISTINCT TRIM(pd.institucion),
       LOWER(REGEXP_REPLACE(TRIM(pd.institucion), '[[:space:]]+', ' ')),
       'Institucion migrada desde perfil docente',
       'activo'
FROM perfiles_docente pd
WHERE pd.institucion IS NOT NULL
  AND TRIM(pd.institucion) <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM instituciones i
      WHERE i.nombre_normalizado = LOWER(REGEXP_REPLACE(TRIM(pd.institucion), '[[:space:]]+', ' '))
  );

UPDATE perfiles_docente pd
INNER JOIN instituciones i
    ON i.nombre_normalizado = LOWER(REGEXP_REPLACE(TRIM(pd.institucion), '[[:space:]]+', ' '))
SET pd.id_institucion = i.id_institucion
WHERE pd.id_institucion IS NULL
  AND pd.institucion IS NOT NULL
  AND TRIM(pd.institucion) <> '';

INSERT INTO institucion_grados (id_institucion, id_grado_base, estado)
SELECT i.id_institucion, g.id_grado, 'activo'
FROM instituciones i
INNER JOIN grados g ON g.codigo_grado IN ('4P', '5P', '6P')
WHERE NOT EXISTS (
    SELECT 1
    FROM institucion_grados ig
    WHERE ig.id_institucion = i.id_institucion
      AND ig.id_grado_base = g.id_grado
);

UPDATE docente_grados dg
INNER JOIN perfiles_docente pd ON pd.id_usuario = dg.id_usuario_docente
INNER JOIN institucion_grados ig
    ON ig.id_institucion = pd.id_institucion
   AND ig.id_grado_base = dg.id_grado
SET dg.id_institucion_grado = ig.id_institucion_grado
WHERE dg.id_institucion_grado IS NULL;

INSERT INTO docente_secciones (id_docente, id_seccion, estado)
SELECT DISTINCT gr.id_docente, gs.id_seccion, 'activo'
FROM grupo_secciones gs
INNER JOIN grupos gr ON gr.id_grupo = gs.id_grupo
WHERE NOT EXISTS (
    SELECT 1
    FROM docente_secciones ds
    WHERE ds.id_docente = gr.id_docente
      AND ds.id_seccion = gs.id_seccion
);
