CREATE DATABASE IF NOT EXISTS tesis_matematica_app
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tesis_matematica_app;

-- Los scripts fuente y la sesión de importación usan UTF-8 de cuatro bytes.
SET NAMES utf8mb4;

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
SET nombre_grado = 'Cuarto',
    descripcion = 'Cuarto grado base',
    orden_visualizacion = 1,
    estado = 'activo'
WHERE codigo_grado = '4P';

UPDATE grados
SET nombre_grado = 'Quinto',
    descripcion = 'Quinto grado base',
    orden_visualizacion = 2,
    estado = 'activo'
WHERE codigo_grado = '5P';

UPDATE grados
SET nombre_grado = 'Sexto',
    descripcion = 'Sexto grado base',
    orden_visualizacion = 3,
    estado = 'activo'
WHERE codigo_grado = '6P';

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

CREATE TABLE IF NOT EXISTS bitacora_acciones (
    id_bitacora INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    accion VARCHAR(80) NOT NULL,
    entidad VARCHAR(80) NOT NULL,
    id_entidad VARCHAR(80) NULL,
    metodo VARCHAR(10) NOT NULL,
    ruta VARCHAR(255) NOT NULL,
    codigo_estado INT NOT NULL,
    resultado ENUM('exitoso', 'fallido') NOT NULL,
    ip_cliente VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    detalles_json JSON NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_bitacora_usuario_fecha (id_usuario, fecha_creacion),
    INDEX idx_bitacora_entidad_fecha (entidad, fecha_creacion),
    INDEX idx_bitacora_accion_fecha (accion, fecha_creacion),

    CONSTRAINT fk_bitacora_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE SET NULL
);

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
    id_seccion_activa INT GENERATED ALWAYS AS (CASE WHEN estado = 'activo' THEN id_seccion ELSE NULL END) STORED,
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_docente_seccion UNIQUE (id_docente, id_seccion),
    CONSTRAINT uk_docente_seccion_activa UNIQUE (id_seccion_activa),
    CONSTRAINT fk_docente_secciones_docente
        FOREIGN KEY (id_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_docente_secciones_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion)
);

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
    id_usuario_estudiante_activo INT GENERATED ALWAYS AS (CASE WHEN estado = 'activo' THEN id_usuario_estudiante ELSE NULL END) STORED,
    fecha_ingreso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_salida TIMESTAMP NULL DEFAULT NULL,

    CONSTRAINT uk_estudiante_matricula_activa UNIQUE (id_usuario_estudiante_activo),
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

CREATE TABLE IF NOT EXISTS partidas_juego (
    id_partida INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    id_asignacion INT NULL,
    id_grado INT NULL,
    id_tema INT NULL,
    request_id VARCHAR(80) NULL,
    id_nivel_inicial INT NULL,
    id_nivel_actual INT NULL,
    id_ejercicio_actual INT NULL,
    id_ejercicio_generado_actual INT NULL,
    personaje VARCHAR(50) NOT NULL,
    mapa VARCHAR(100) NOT NULL,
    casilla_actual INT NOT NULL DEFAULT 0,
    total_correctos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    vidas_iniciales INT NOT NULL DEFAULT 5,
    vidas_restantes INT NOT NULL DEFAULT 5,
    vidas_perdidas_total INT NOT NULL DEFAULT 0,
    continuaciones_compradas INT NOT NULL DEFAULT 0,
    recompensa_otorgada TINYINT(1) NOT NULL DEFAULT 0,
    preguntas_respondidas INT NOT NULL DEFAULT 0,
    estado ENUM('en_curso', 'completada', 'sin_vidas', 'abandonada') NOT NULL DEFAULT 'en_curso',
    motivo_finalizacion VARCHAR(80) NULL,
    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_ultima_actividad TIMESTAMP NULL DEFAULT NULL,

    CONSTRAINT fk_partidas_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),

    CONSTRAINT uk_partidas_request_id UNIQUE (request_id)
);

CREATE TABLE IF NOT EXISTS temas (
    id_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT NOT NULL,
    nombre_tema VARCHAR(120) NOT NULL,
    descripcion VARCHAR(255) NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_temas_grados
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),

    CONSTRAINT uk_temas_grado_nombre
        UNIQUE (id_grado, nombre_tema)
);

CREATE TABLE IF NOT EXISTS niveles_dificultad (
    id_nivel INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    orden_nivel INT NOT NULL,
    es_inicial TINYINT(1) NOT NULL DEFAULT 0,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_niveles_codigo UNIQUE (codigo),
    CONSTRAINT uk_niveles_orden UNIQUE (orden_nivel)
);

CREATE TABLE IF NOT EXISTS ejercicios (
    id_ejercicio INT AUTO_INCREMENT PRIMARY KEY,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    enunciado VARCHAR(500) NOT NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    respuesta_correcta VARCHAR(255) NOT NULL,
    explicacion VARCHAR(500) NULL,
    explicacion_pasos JSON NULL,
    pista VARCHAR(255) NULL,
    estado ENUM('borrador', 'publicado', 'desactivado') NOT NULL DEFAULT 'borrador',
    es_demo TINYINT(1) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ejercicios_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),

    CONSTRAINT fk_ejercicios_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS opciones_ejercicio (
    id_opcion INT AUTO_INCREMENT PRIMARY KEY,
    id_ejercicio INT NOT NULL,
    texto_opcion VARCHAR(255) NOT NULL,
    orden_visualizacion INT NOT NULL DEFAULT 1,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_opciones_ejercicio_orden UNIQUE (id_ejercicio, orden_visualizacion),
    CONSTRAINT fk_opciones_ejercicios
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio)
);

CREATE TABLE IF NOT EXISTS asignaciones (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_docente INT NOT NULL,
    id_institucion_grado INT NOT NULL,
    id_grupo INT NULL,
    id_seccion INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    instrucciones VARCHAR(500) NULL,
    tipo ENUM('generacion_automatica', 'ejercicios_especificos') NOT NULL DEFAULT 'generacion_automatica',
    id_nivel_inicial INT NOT NULL,
    cantidad_preguntas INT NOT NULL DEFAULT 10,
    fecha_inicio DATETIME NOT NULL,
    fecha_limite DATETIME NULL,
    obligatoria TINYINT(1) NOT NULL DEFAULT 1,
    estado ENUM('borrador', 'activa', 'pausada', 'finalizada', 'cancelada') NOT NULL DEFAULT 'activa',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_asignaciones_docente
        FOREIGN KEY (id_docente)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_asignaciones_grupo
        FOREIGN KEY (id_grupo)
        REFERENCES grupos(id_grupo),
    CONSTRAINT fk_asignaciones_institucion_grado
        FOREIGN KEY (id_institucion_grado)
        REFERENCES institucion_grados(id_institucion_grado),
    CONSTRAINT fk_asignaciones_seccion
        FOREIGN KEY (id_seccion)
        REFERENCES secciones(id_seccion),
    CONSTRAINT fk_asignaciones_nivel
        FOREIGN KEY (id_nivel_inicial)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS asignacion_temas (
    id_asignacion_tema INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_tema INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_asignacion_tema UNIQUE (id_asignacion, id_tema),
    CONSTRAINT fk_asignacion_temas_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_asignacion_temas_tema
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema)
);

CREATE TABLE IF NOT EXISTS asignacion_ejercicios (
    id_asignacion_ejercicio INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_ejercicio INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_asignacion_ejercicio UNIQUE (id_asignacion, id_ejercicio),
    CONSTRAINT fk_asignacion_ejercicios_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_asignacion_ejercicios_ejercicio
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio)
);

CREATE TABLE IF NOT EXISTS estudiante_asignaciones (
    id_estudiante_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT NOT NULL,
    id_estudiante INT NOT NULL,
    estado ENUM('pendiente','en_progreso','completada') NOT NULL DEFAULT 'pendiente',
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP NULL DEFAULT NULL,
    fecha_completada TIMESTAMP NULL DEFAULT NULL,
    cantidad_intentos INT NOT NULL DEFAULT 0,
    ultima_partida INT NULL,
    fecha_ultima_actividad TIMESTAMP NULL DEFAULT NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_estudiante_asignacion UNIQUE (id_asignacion, id_estudiante),
    CONSTRAINT fk_estudiante_asignaciones_asignacion
        FOREIGN KEY (id_asignacion)
        REFERENCES asignaciones(id_asignacion),
    CONSTRAINT fk_estudiante_asignaciones_estudiante
        FOREIGN KEY (id_estudiante)
        REFERENCES usuarios(id_usuario)
);

DELIMITER $$

DROP PROCEDURE IF EXISTS agregar_fk_partidas_asignaciones$$

CREATE PROCEDURE agregar_fk_partidas_asignaciones()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND COLUMN_NAME = 'id_asignacion'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN id_asignacion INT NULL AFTER id_usuario;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'partidas_juego'
          AND CONSTRAINT_NAME = 'fk_partidas_asignaciones'
    ) THEN
        ALTER TABLE partidas_juego
            ADD CONSTRAINT fk_partidas_asignaciones
                FOREIGN KEY (id_asignacion)
                REFERENCES asignaciones(id_asignacion);
    END IF;
END$$

DELIMITER ;

CALL agregar_fk_partidas_asignaciones();
DROP PROCEDURE IF EXISTS agregar_fk_partidas_asignaciones;

CREATE TABLE IF NOT EXISTS intentos_juego (
    id_intento INT AUTO_INCREMENT PRIMARY KEY,
    id_partida INT NOT NULL,
    id_ejercicio INT NULL,
    id_ejercicio_generado INT NULL,
    respuesta_estudiante VARCHAR(255) NOT NULL,
    es_correcta TINYINT(1) NOT NULL,
    nivel_al_responder INT NOT NULL,
    tiempo_respuesta_ms INT NOT NULL DEFAULT 0,
    casilla_antes INT NOT NULL,
    casilla_despues INT NOT NULL,
    vidas_antes INT NOT NULL,
    vidas_despues INT NOT NULL,
    fecha_respuesta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request_id VARCHAR(80) NOT NULL,
    respuesta_api_json JSON NULL,

    CONSTRAINT uk_intentos_request_id UNIQUE (request_id),
    CONSTRAINT fk_intentos_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_intentos_ejercicios
        FOREIGN KEY (id_ejercicio)
        REFERENCES ejercicios(id_ejercicio),
    CONSTRAINT fk_intentos_niveles
        FOREIGN KEY (nivel_al_responder)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS reglas_adaptativas (
    id_regla INT AUTO_INCREMENT PRIMARY KEY,
    codigo_regla VARCHAR(80) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500) NULL,
    prioridad INT NOT NULL,
    parametros_json JSON NOT NULL,
    accion ENUM('mantener', 'aumentar', 'reducir', 'reforzar') NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_reglas_codigo UNIQUE (codigo_regla)
);

CREATE TABLE IF NOT EXISTS decisiones_agente (
    id_decision INT AUTO_INCREMENT PRIMARY KEY,
    id_partida INT NOT NULL,
    id_intento INT NOT NULL,
    id_tema INT NOT NULL,
    nivel_anterior INT NOT NULL,
    nivel_nuevo INT NOT NULL,
    accion ENUM('mantener', 'aumentar', 'reducir', 'reforzar') NOT NULL,
    regla_aplicada VARCHAR(80) NOT NULL,
    motivo VARCHAR(500) NOT NULL,
    datos_entrada_json JSON NOT NULL,
    fecha_decision TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_decisiones_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_decisiones_intentos
        FOREIGN KEY (id_intento)
        REFERENCES intentos_juego(id_intento),
    CONSTRAINT fk_decisiones_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_decisiones_nivel_anterior
        FOREIGN KEY (nivel_anterior)
        REFERENCES niveles_dificultad(id_nivel),
    CONSTRAINT fk_decisiones_nivel_nuevo
        FOREIGN KEY (nivel_nuevo)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS progreso_estudiante (
    id_progreso_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    total_partidas INT NOT NULL DEFAULT 0,
    total_ejercicios INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    puntos INT NOT NULL DEFAULT 0,
    mejor_puntuacion INT NOT NULL DEFAULT 0,
    tiempo_total_ms BIGINT NOT NULL DEFAULT 0,
    ultima_actividad TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_progreso_estudiante_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_progreso_estudiante_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS progreso_tema_estudiante (
    id_progreso_tema_estudiante INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tema INT NOT NULL,
    id_grado_curricular_actual INT NULL,
    id_nivel_actual INT NULL,
    total_intentos INT NOT NULL DEFAULT 0,
    total_aciertos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    porcentaje_aciertos DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    racha_correctas INT NOT NULL DEFAULT 0,
    racha_incorrectas INT NOT NULL DEFAULT 0,
    estado_dominio ENUM('inicial', 'en_progreso', 'dominado') NOT NULL DEFAULT 'inicial',
    tiempo_promedio_ms INT NOT NULL DEFAULT 0,
    cambios_dificultad INT NOT NULL DEFAULT 0,
    ultima_practica TIMESTAMP NULL DEFAULT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_progreso_tema_usuario UNIQUE (id_usuario, id_tema),
    CONSTRAINT fk_progreso_tema_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_progreso_tema_tema
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_progreso_tema_grado_curricular
        FOREIGN KEY (id_grado_curricular_actual)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_progreso_tema_nivel
        FOREIGN KEY (id_nivel_actual)
        REFERENCES niveles_dificultad(id_nivel)
);

CREATE TABLE IF NOT EXISTS promociones_curriculares_tema (
    id_promocion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tema_anterior INT NOT NULL,
    id_tema_nuevo INT NOT NULL,
    id_grado_anterior INT NOT NULL,
    id_grado_nuevo INT NOT NULL,
    id_nivel_anterior INT NULL,
    id_nivel_nuevo INT NULL,
    tipo_movimiento ENUM('promocion', 'descenso') NOT NULL DEFAULT 'promocion',
    motivo VARCHAR(255) NOT NULL,
    metricas_json JSON NOT NULL,
    fecha_promocion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_promociones_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_promociones_tema_anterior
        FOREIGN KEY (id_tema_anterior)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_promociones_tema_nuevo
        FOREIGN KEY (id_tema_nuevo)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_promociones_grado_anterior
        FOREIGN KEY (id_grado_anterior)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_promociones_grado_nuevo
        FOREIGN KEY (id_grado_nuevo)
        REFERENCES grados(id_grado)
);

CREATE TABLE IF NOT EXISTS plantillas_ejercicios (
    id_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    id_grado INT NOT NULL,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500) NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    plantilla_enunciado VARCHAR(500) NOT NULL,
    configuracion_json JSON NOT NULL,
    plantilla_explicacion VARCHAR(500) NULL,
    plantilla_pista VARCHAR(255) NULL,
    estado ENUM('borrador', 'publicada', 'desactivada') NOT NULL DEFAULT 'borrador',
    es_demo TINYINT(1) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_plantillas_grados
        FOREIGN KEY (id_grado)
        REFERENCES grados(id_grado),
    CONSTRAINT fk_plantillas_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_plantillas_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel),
    CONSTRAINT uk_plantilla_nombre_nivel
        UNIQUE (id_grado, id_tema, id_nivel, nombre)
);

CREATE TABLE IF NOT EXISTS ejercicios_generados (
    id_ejercicio_generado INT AUTO_INCREMENT PRIMARY KEY,
    id_plantilla INT NOT NULL,
    id_partida INT NOT NULL,
    id_tema INT NOT NULL,
    id_nivel INT NOT NULL,
    enunciado VARCHAR(500) NOT NULL,
    tipo_respuesta ENUM('seleccion_multiple', 'numerica') NOT NULL,
    respuesta_correcta VARCHAR(255) NOT NULL,
    explicacion VARCHAR(500) NULL,
    explicacion_pasos JSON NULL,
    pista VARCHAR(255) NULL,
    opciones_json JSON NULL,
    parametros_json JSON NOT NULL,
    semilla_generacion INT NOT NULL,
    estado_validacion ENUM('valido', 'invalido') NOT NULL DEFAULT 'valido',
    fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_generados_plantillas
        FOREIGN KEY (id_plantilla)
        REFERENCES plantillas_ejercicios(id_plantilla),
    CONSTRAINT fk_generados_partidas
        FOREIGN KEY (id_partida)
        REFERENCES partidas_juego(id_partida),
    CONSTRAINT fk_generados_temas
        FOREIGN KEY (id_tema)
        REFERENCES temas(id_tema),
    CONSTRAINT fk_generados_niveles
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_dificultad(id_nivel)
);

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'facil', 'Facil', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'facil');

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'intermedio', 'Intermedio', 2, 0
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'intermedio');

INSERT INTO niveles_dificultad (codigo, nombre, orden_nivel, es_inicial)
SELECT 'dificil', 'Dificil', 3, 0
WHERE NOT EXISTS (SELECT 1 FROM niveles_dificultad WHERE codigo = 'dificil');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'dos_errores_consecutivos', 'Dos errores consecutivos', 'Reduce dificultad o recomienda refuerzo cuando hay dos errores consecutivos.', 1,
       JSON_OBJECT('incorrectas_consecutivas', 2, 'cooldown_intentos', 2), 'reducir'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'dos_errores_consecutivos');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'tres_aciertos_consecutivos', 'Tres aciertos consecutivos', 'Aumenta dificultad al alcanzar exactamente tres respuestas correctas consecutivas.', 2,
       JSON_OBJECT('correctas_consecutivas', 3, 'cooldown_intentos', 2), 'aumentar'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'tres_aciertos_consecutivos');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'porcentaje_bajo', 'Porcentaje bajo', 'Reduce dificultad o recomienda refuerzo cuando el porcentaje de aciertos es menor a 60.', 3,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_maximo', 60, 'cooldown_intentos', 3), 'reducir'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'porcentaje_bajo');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'porcentaje_alto', 'Porcentaje alto', 'Puede aumentar dificultad cuando el porcentaje supera 80 y no existe aumento reciente.', 4,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_minimo', 80, 'cooldown_intentos', 3), 'aumentar'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'porcentaje_alto');

INSERT INTO reglas_adaptativas (codigo_regla, nombre, descripcion, prioridad, parametros_json, accion)
SELECT 'rango_estable', 'Rango estable', 'Mantiene dificultad cuando el porcentaje esta entre 60 y 80.', 5,
       JSON_OBJECT('min_intentos', 5, 'porcentaje_minimo', 60, 'porcentaje_maximo', 80), 'mantener'
WHERE NOT EXISTS (SELECT 1 FROM reglas_adaptativas WHERE codigo_regla = 'rango_estable');

INSERT INTO temas (id_grado, nombre_tema, descripcion)
SELECT g.id_grado, 'Operaciones basicas', 'Ejercicios demo de suma, resta, multiplicacion y division.'
FROM grados g
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND NOT EXISTS (
      SELECT 1 FROM temas t
      WHERE t.id_grado = g.id_grado
        AND t.nombre_tema = 'Operaciones basicas'
  );

INSERT INTO ejercicios (id_tema, id_nivel, enunciado, tipo_respuesta, respuesta_correcta, explicacion, pista, estado, es_demo)
SELECT t.id_tema, n.id_nivel, datos.enunciado, datos.tipo_respuesta, datos.respuesta_correcta, datos.explicacion, datos.pista, 'publicado', 1
FROM temas t
INNER JOIN grados g ON g.id_grado = t.id_grado
CROSS JOIN (
    SELECT 'facil' AS codigo_nivel, '¿Cuánto es 2 + 3?' AS enunciado, 'seleccion_multiple' AS tipo_respuesta, '5' AS respuesta_correcta, '2 + 3 = 5.' AS explicacion, 'Suma primero las unidades.' AS pista
    UNION ALL SELECT 'facil', '¿Cuánto es 9 - 4?', 'seleccion_multiple', '5', '9 - 4 = 5.', 'Resta cuatro pasos desde nueve.'
    UNION ALL SELECT 'facil', '¿Cuánto es 6 + 7?', 'numerica', '13', '6 + 7 = 13.', 'Completa a diez y suma lo restante.'
    UNION ALL SELECT 'intermedio', '¿Cuánto es 8 x 4?', 'seleccion_multiple', '32', '8 x 4 = 32.', 'Piensa en cuatro grupos de ocho.'
    UNION ALL SELECT 'intermedio', 'Resuelve: 45 / 5', 'numerica', '9', '45 / 5 = 9.', 'Busca cuantas veces cabe 5 en 45.'
    UNION ALL SELECT 'dificil', '¿Cuánto es 12 x 7?', 'seleccion_multiple', '84', '12 x 7 = 84.', 'Multiplica 10 x 7 y 2 x 7.'
    UNION ALL SELECT 'dificil', 'Resuelve: 144 / 12', 'numerica', '12', '144 / 12 = 12.', '12 x 12 = 144.'
) datos
INNER JOIN niveles_dificultad n ON n.codigo = datos.codigo_nivel
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND t.nombre_tema = 'Operaciones basicas'
  AND NOT EXISTS (
      SELECT 1 FROM ejercicios e
      WHERE e.id_tema = t.id_tema
        AND e.enunciado = datos.enunciado
  );

INSERT INTO opciones_ejercicio (id_ejercicio, texto_opcion, orden_visualizacion)
SELECT e.id_ejercicio, opciones.texto, opciones.orden
FROM ejercicios e
JOIN (
    SELECT '¿Cuánto es 2 + 3?' AS enunciado, '4' AS texto, 1 AS orden
    UNION ALL SELECT '¿Cuánto es 2 + 3?', '5', 2
    UNION ALL SELECT '¿Cuánto es 2 + 3?', '6', 3
    UNION ALL SELECT '¿Cuánto es 2 + 3?', '7', 4
    UNION ALL SELECT '¿Cuánto es 9 - 4?', '3', 1
    UNION ALL SELECT '¿Cuánto es 9 - 4?', '4', 2
    UNION ALL SELECT '¿Cuánto es 9 - 4?', '5', 3
    UNION ALL SELECT '¿Cuánto es 9 - 4?', '6', 4
    UNION ALL SELECT '¿Cuánto es 8 x 4?', '24', 1
    UNION ALL SELECT '¿Cuánto es 8 x 4?', '32', 2
    UNION ALL SELECT '¿Cuánto es 8 x 4?', '36', 3
    UNION ALL SELECT '¿Cuánto es 8 x 4?', '40', 4
    UNION ALL SELECT '¿Cuánto es 12 x 7?', '72', 1
    UNION ALL SELECT '¿Cuánto es 12 x 7?', '84', 2
    UNION ALL SELECT '¿Cuánto es 12 x 7?', '92', 3
    UNION ALL SELECT '¿Cuánto es 12 x 7?', '96', 4
) opciones ON opciones.enunciado = e.enunciado
WHERE e.tipo_respuesta = 'seleccion_multiple'
  AND NOT EXISTS (
      SELECT 1 FROM opciones_ejercicio oe
      WHERE oe.id_ejercicio = e.id_ejercicio
        AND oe.texto_opcion = opciones.texto
  );

INSERT INTO temas (id_grado, nombre_tema, descripcion)
SELECT g.id_grado, tema.nombre_tema, tema.descripcion
FROM grados g
CROSS JOIN (
    SELECT 'Suma' AS nombre_tema, 'Plantillas demo de suma.' AS descripcion
    UNION ALL SELECT 'Resta', 'Plantillas demo de resta.'
    UNION ALL SELECT 'Multiplicacion', 'Plantillas demo de multiplicacion.'
    UNION ALL SELECT 'Division', 'Plantillas demo de division exacta.'
) tema
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND NOT EXISTS (
      SELECT 1 FROM temas t
      WHERE t.id_grado = g.id_grado
        AND t.nombre_tema = tema.nombre_tema
  );

INSERT INTO plantillas_ejercicios
    (id_grado, id_tema, id_nivel, nombre, descripcion, tipo_respuesta, plantilla_enunciado,
     configuracion_json, plantilla_explicacion, plantilla_pista, estado, es_demo)
SELECT g.id_grado, t.id_tema, n.id_nivel,
       CONCAT(t.nombre_tema, ' ', n.nombre),
       CONCAT('Plantilla demo para ', t.nombre_tema, ' en nivel ', n.nombre),
       CASE WHEN t.nombre_tema IN ('Suma', 'Multiplicacion') THEN 'seleccion_multiple' ELSE 'numerica' END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN '¿Cuánto es {a} + {b}?'
           WHEN 'Resta' THEN '¿Cuánto es {a} - {b}?'
           WHEN 'Multiplicacion' THEN '¿Cuánto es {a} x {b}?'
           ELSE '¿Cuánto es {a} / {b}?'
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN JSON_OBJECT('operacion', 'suma', 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 20 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 20 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END)
           ))
           WHEN 'Resta' THEN JSON_OBJECT('operacion', 'resta', 'permitir_negativos', false, 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 5 WHEN 'intermedio' THEN 30 ELSE 100 END, 'max', CASE n.codigo WHEN 'facil' THEN 30 WHEN 'intermedio' THEN 150 ELSE 800 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 1 WHEN 'intermedio' THEN 10 ELSE 50 END, 'max', CASE n.codigo WHEN 'facil' THEN 20 WHEN 'intermedio' THEN 100 ELSE 500 END)
           ))
           WHEN 'Multiplicacion' THEN JSON_OBJECT('operacion', 'multiplicacion', 'variables', JSON_OBJECT(
               'a', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 10 ELSE 20 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 99 ELSE 99 END),
               'b', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 2 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 9 ELSE 99 END)
           ))
           ELSE JSON_OBJECT('operacion', 'division', 'division_exacta', true, 'variables', JSON_OBJECT(
               'resultado', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 5 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 30 ELSE 99 END),
               'divisor', JSON_OBJECT('tipo', 'entero', 'min', CASE n.codigo WHEN 'facil' THEN 2 WHEN 'intermedio' THEN 2 ELSE 10 END, 'max', CASE n.codigo WHEN 'facil' THEN 9 WHEN 'intermedio' THEN 12 ELSE 25 END)
           ))
       END,
       CASE t.nombre_tema
           WHEN 'Suma' THEN '{a} + {b} = {respuesta}.'
           WHEN 'Resta' THEN '{a} - {b} = {respuesta}.'
           WHEN 'Multiplicacion' THEN '{a} x {b} = {respuesta}.'
           ELSE '{a} / {b} = {respuesta}.'
       END,
       'Usa la operacion indicada y revisa cada numero.',
       'publicada',
       1
FROM grados g
INNER JOIN temas t ON t.id_grado = g.id_grado
CROSS JOIN niveles_dificultad n
WHERE g.codigo_grado IN ('4P', '5P', '6P')
  AND t.nombre_tema IN ('Suma', 'Resta', 'Multiplicacion', 'Division')
  AND n.codigo IN ('facil', 'intermedio', 'dificil')
  AND NOT EXISTS (
      SELECT 1 FROM plantillas_ejercicios p
      WHERE p.id_grado = g.id_grado
        AND p.id_tema = t.id_tema
        AND p.id_nivel = n.id_nivel
        AND p.nombre = CONCAT(t.nombre_tema, ' ', n.nombre)
  );

SOURCE database/actualizar_catalogo_personal_temas.sql;
SOURCE database/actualizar_contextos_progresion_curricular.sql;
SOURCE database/actualizar_retroalimentacion_procedimiento.sql;
SOURCE database/actualizar_personalizacion_tienda.sql;
SOURCE database/actualizar_personajes_iniciales.sql;
SOURCE database/corregir_inventario_personajes.sql;
SOURCE database/actualizar_dificultad_facil.sql;
SOURCE database/actualizar_generacion_ortografia_y_progresion.sql;
SOURCE database/optimizar_indices_y_seed_qa.sql;
