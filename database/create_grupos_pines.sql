USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS grupos (
    id_grupo INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_grado INT NOT NULL,
    id_institucion_grado INT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_grupos_docente
        FOREIGN KEY (id_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_grupos_grado
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_grupos_institucion_grado
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado),
    CONSTRAINT uk_grupo_docente_nombre
        UNIQUE (id_docente, nombre)
);

CREATE TABLE IF NOT EXISTS grupo_secciones (
    id_grupo_seccion INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo INT NOT NULL,
    id_seccion INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_grupo_seccion UNIQUE (id_grupo, id_seccion),
    CONSTRAINT fk_grupo_secciones_grupo
        FOREIGN KEY (id_grupo)
        REFERENCES grupos(id_grupo),
    CONSTRAINT fk_grupo_secciones_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion)
);

CREATE TABLE IF NOT EXISTS pines_acceso (
    id_pin INT AUTO_INCREMENT PRIMARY KEY,
    pin VARCHAR(6) NOT NULL,
    id_grupo INT NOT NULL,
    id_seccion INT NULL,
    estado ENUM('activo', 'inactivo', 'expirado') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    creado_por INT NOT NULL,

    CONSTRAINT uk_pin_activo UNIQUE (pin, estado),
    CONSTRAINT fk_pines_grupo
        FOREIGN KEY (id_grupo)
        REFERENCES grupos(id_grupo),
    CONSTRAINT fk_pines_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion),
    CONSTRAINT fk_pines_creador
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS estudiantes_grupos (
    id_estudiante_grupo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario_estudiante INT NOT NULL,
    id_grupo INT NOT NULL,
    id_seccion INT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_ingreso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_salida TIMESTAMP NULL DEFAULT NULL,

    CONSTRAINT uk_estudiante_grupo_activo UNIQUE (id_usuario_estudiante, id_grupo, estado),
    CONSTRAINT fk_estudiantes_grupos_usuario
        FOREIGN KEY (id_usuario_estudiante)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_estudiantes_grupos_grupo
        FOREIGN KEY (id_grupo)
        REFERENCES grupos(id_grupo),
    CONSTRAINT fk_estudiantes_grupos_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion)
);
