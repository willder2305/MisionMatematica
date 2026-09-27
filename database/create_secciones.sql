CREATE TABLE IF NOT EXISTS secciones (
    id_seccion INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT NOT NULL,
    id_institucion_grado INT NULL,
    nombre_seccion VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_secciones_grados
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_secciones_institucion_grados
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado),

    CONSTRAINT uk_grado_seccion
        UNIQUE (id_grado, id_institucion_grado, nombre_seccion),
    CONSTRAINT uk_institucion_grado_seccion
        UNIQUE (id_institucion_grado, nombre_seccion),
    CONSTRAINT chk_secciones_nombre_valido
        CHECK (nombre_seccion IN ('A', 'B', 'C', 'D', 'Única'))
);
