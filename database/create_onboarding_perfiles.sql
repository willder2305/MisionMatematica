USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS perfiles_estudiante (
    id_perfil_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_grado INT NULL,
    id_institucion INT NULL,
    id_institucion_grado INT NULL,
    id_seccion INT NULL,
    modalidad ENUM('cuenta_propia', 'grupo_educativo') NOT NULL,
    personaje VARCHAR(50) NOT NULL DEFAULT 'masculino',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_perfiles_estudiante_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_perfiles_estudiante_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_perfiles_estudiante_grado
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_perfiles_estudiante_institucion
        FOREIGN KEY (id_institucion)
        REFERENCES instituciones(id_institucion),
    CONSTRAINT fk_perfiles_estudiante_institucion_grado
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado),
    CONSTRAINT fk_perfiles_estudiante_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion)
);

CREATE TABLE IF NOT EXISTS perfiles_docente (
    id_perfil_docente INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_institucion INT NULL,
    institucion VARCHAR(180) NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_perfiles_docente_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_perfiles_docente_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_perfiles_docente_institucion
        FOREIGN KEY (id_institucion)
        REFERENCES instituciones(id_institucion)
);

CREATE TABLE IF NOT EXISTS docente_grados (
    id_docente_grado INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario_docente INT NOT NULL,
    id_grado INT NOT NULL,
    id_institucion_grado INT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_docente_grado UNIQUE (id_usuario_docente, id_grado),
    CONSTRAINT uk_docente_institucion_grado UNIQUE (id_usuario_docente, id_institucion_grado),
    CONSTRAINT fk_docente_grados_usuario
        FOREIGN KEY (id_usuario_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_docente_grados_grado
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_docente_grados_institucion_grado
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado)
);

CREATE TABLE IF NOT EXISTS docente_secciones (
    id_docente_seccion INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_seccion INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_docente_seccion UNIQUE (id_docente, id_seccion),
    CONSTRAINT fk_docente_secciones_docente
        FOREIGN KEY (id_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_docente_secciones_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion)
);
