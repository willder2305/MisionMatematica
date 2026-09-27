CREATE TABLE IF NOT EXISTS partidas_juego (
    id_partida INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    request_id VARCHAR(80) NULL,
    personaje VARCHAR(50) NOT NULL,
    mapa VARCHAR(100) NOT NULL,
    casilla_actual INT NOT NULL DEFAULT 0,
    total_correctos INT NOT NULL DEFAULT 0,
    total_errores INT NOT NULL DEFAULT 0,
    estado ENUM('en_curso', 'completada', 'abandonada') NOT NULL DEFAULT 'en_curso',
    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT uk_partidas_request_id UNIQUE (request_id)
);
