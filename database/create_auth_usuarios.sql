USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_roles_nombre UNIQUE (nombre)
);

INSERT INTO roles (nombre, descripcion)
SELECT 'administrador', 'Gestion general del sistema'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'administrador');

INSERT INTO roles (nombre, descripcion)
SELECT 'docente', 'Gestion de grupos, asignaciones y reportes'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'docente');

INSERT INTO roles (nombre, descripcion)
SELECT 'estudiante', 'Acceso a juego, historial y progreso'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'estudiante');

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120) NOT NULL,
    correo VARCHAR(180) NOT NULL,
    password_hash VARCHAR(255) NULL,
    id_rol INT NOT NULL,
    estado ENUM('activo', 'inactivo', 'bloqueado') NOT NULL DEFAULT 'activo',
    correo_verificado TINYINT(1) NOT NULL DEFAULT 0,
    onboarding_completado TINYINT(1) NOT NULL DEFAULT 0,
    ultimo_acceso TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_usuarios_correo UNIQUE (correo),
    CONSTRAINT fk_usuarios_roles
        FOREIGN KEY (id_rol)
        REFERENCES roles(id_rol)
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id_refresh_token INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    jti VARCHAR(80) NOT NULL,
    estado ENUM('activo', 'revocado') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    fecha_revocacion DATETIME NULL DEFAULT NULL,

    CONSTRAINT uk_refresh_token_hash UNIQUE (token_hash),
    CONSTRAINT uk_refresh_jti UNIQUE (jti),
    CONSTRAINT fk_refresh_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS recuperaciones_contrasena (
    id_recuperacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    estado ENUM('pendiente', 'usado', 'expirado') NOT NULL DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    fecha_uso DATETIME NULL DEFAULT NULL,

    CONSTRAINT uk_recuperaciones_token UNIQUE (token_hash),
    CONSTRAINT fk_recuperaciones_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS verificaciones_correo (
    id_verificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    estado ENUM('pendiente', 'usado', 'expirado') NOT NULL DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    fecha_uso DATETIME NULL DEFAULT NULL,

    CONSTRAINT uk_verificaciones_token UNIQUE (token_hash),
    CONSTRAINT fk_verificaciones_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS agregar_fk_partidas_usuarios$$

CREATE PROCEDURE agregar_fk_partidas_usuarios()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_usuarios'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_usuarios
                FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id_usuario);
    END IF;
END$$

DELIMITER ;

CALL agregar_fk_partidas_usuarios();
DROP PROCEDURE IF EXISTS agregar_fk_partidas_usuarios;
