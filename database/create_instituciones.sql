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
    CONSTRAINT fk_institucion_grados_institucion
        FOREIGN KEY (id_institucion)
        REFERENCES instituciones(id_institucion),
    CONSTRAINT fk_institucion_grados_grado_base
        FOREIGN KEY (id_grado_base)
        REFERENCES grados(id_grado)
);
