USE tesis_matematica_app;

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
