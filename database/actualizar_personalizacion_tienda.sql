USE tesis_matematica_app;

CREATE TABLE IF NOT EXISTS tienda_items (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('personaje', 'mapa') NOT NULL,
    item_key VARCHAR(80) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    precio_monedas INT NOT NULL DEFAULT 0,
    es_inicial TINYINT(1) NOT NULL DEFAULT 0,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_tienda_items_tipo_key UNIQUE (tipo, item_key),
    CONSTRAINT ck_tienda_items_precio CHECK (precio_monedas >= 0)
);

CREATE TABLE IF NOT EXISTS monederos (
    id_usuario INT PRIMARY KEY,
    saldo_monedas INT NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_monederos_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT ck_monederos_saldo CHECK (saldo_monedas >= 0)
);

CREATE TABLE IF NOT EXISTS usuario_items (
    id_usuario_item INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_item INT NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_desbloqueo TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_usuario_items_usuario_item UNIQUE (id_usuario, id_item),
    CONSTRAINT fk_usuario_items_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_usuario_items_item FOREIGN KEY (id_item) REFERENCES tienda_items(id_item)
);

CREATE TABLE IF NOT EXISTS movimientos_monedas (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    tipo ENUM('compra', 'recompensa', 'ajuste') NOT NULL,
    cantidad INT NOT NULL,
    saldo_anterior INT NOT NULL,
    saldo_nuevo INT NOT NULL,
    referencia VARCHAR(160) NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimientos_monedas_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT ck_movimientos_monedas_saldo CHECK (saldo_nuevo >= 0)
);

CREATE TABLE IF NOT EXISTS preferencias_estudiante (
    id_usuario INT PRIMARY KEY,
    personaje_key VARCHAR(80) NULL,
    modo_mapa ENUM('aleatorio', 'fijo') NOT NULL DEFAULT 'aleatorio',
    mapa_key VARCHAR(80) NULL,
    ultimo_mapa_key VARCHAR(80) NULL,
    fecha_modificacion TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_preferencias_estudiante_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

INSERT INTO tienda_items (tipo, item_key, nombre, precio_monedas, es_inicial)
VALUES
    ('personaje', 'masculino', 'Explorador', 0, 1),
    ('personaje', 'femenino', 'Exploradora', 0, 1),
    ('mapa', 'bosque', 'Bosque inicial', 0, 1),
    ('mapa', 'mapa_2', 'Desierto de piramides', 0, 1),
    ('mapa', 'mapa_3', 'Montanas nevadas', 0, 1),
    ('personaje', 'angel', 'Ángel', 25, 0),
    ('personaje', 'astronauta', 'Astronauta', 25, 0),
    ('personaje', 'basketman', 'Basket Man', 25, 0),
    ('personaje', 'princesa', 'Princesa', 25, 0),
    ('personaje', 'rey_pulpo', 'Rey Pulpo', 25, 0),
    ('personaje', 'topo', 'Topo', 25, 0),
    ('mapa', 'mapa_4_espacio', 'Mision espacial', 20, 0),
    ('mapa', 'mapa_5_castillo_magico', 'Castillo magico', 20, 0),
    ('mapa', 'mapa_6_baloncesto', 'Cancha de baloncesto', 20, 0),
    ('mapa', 'mapa_7_fondo_marino', 'Fondo marino', 20, 0),
    ('mapa', 'mapa_8_cielo_atardecer', 'Cielo al atardecer', 20, 0),
    ('mapa', 'mapa_9_cueva_cristales', 'Cueva de cristales', 20, 0)
ON DUPLICATE KEY UPDATE
    nombre = VALUES(nombre),
    precio_monedas = VALUES(precio_monedas),
    es_inicial = VALUES(es_inicial),
    estado = 'activo';

INSERT INTO monederos (id_usuario, saldo_monedas)
SELECT u.id_usuario, 0
FROM usuarios u
INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'estudiante'
ON DUPLICATE KEY UPDATE id_usuario = VALUES(id_usuario);

INSERT INTO usuario_items (id_usuario, id_item)
SELECT u.id_usuario, ti.id_item
FROM usuarios u
INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'estudiante'
INNER JOIN tienda_items ti ON ti.es_inicial = 1 AND ti.estado = 'activo'
ON DUPLICATE KEY UPDATE estado = 'activo';

INSERT INTO preferencias_estudiante (id_usuario, personaje_key, modo_mapa)
SELECT u.id_usuario, 'masculino', 'aleatorio'
FROM usuarios u
INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'estudiante'
ON DUPLICATE KEY UPDATE personaje_key = COALESCE(preferencias_estudiante.personaje_key, VALUES(personaje_key));

-- Amplia la economia sin alterar saldos reales ni relaciones existentes.
DELIMITER $$
CREATE PROCEDURE actualizar_economia_recompensas()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'partidas_juego' AND COLUMN_NAME = 'vidas_perdidas_total'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN vidas_perdidas_total INT NOT NULL DEFAULT 0 AFTER vidas_restantes;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'partidas_juego' AND COLUMN_NAME = 'continuaciones_compradas'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN continuaciones_compradas INT NOT NULL DEFAULT 0 AFTER vidas_perdidas_total;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'partidas_juego' AND COLUMN_NAME = 'recompensa_otorgada'
    ) THEN
        ALTER TABLE partidas_juego ADD COLUMN recompensa_otorgada TINYINT(1) NOT NULL DEFAULT 0 AFTER continuaciones_compradas;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas' AND COLUMN_NAME = 'id_partida'
    ) THEN
        ALTER TABLE movimientos_monedas ADD COLUMN id_partida INT NULL AFTER id_usuario;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas' AND COLUMN_NAME = 'id_item_tienda'
    ) THEN
        ALTER TABLE movimientos_monedas ADD COLUMN id_item_tienda INT NULL AFTER id_partida;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas' AND COLUMN_NAME = 'descripcion'
    ) THEN
        ALTER TABLE movimientos_monedas ADD COLUMN descripcion VARCHAR(255) NULL AFTER referencia;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas' AND COLUMN_NAME = 'request_id'
    ) THEN
        ALTER TABLE movimientos_monedas ADD COLUMN request_id VARCHAR(80) NULL AFTER descripcion;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'movimientos_monedas' AND INDEX_NAME = 'uk_movimientos_request_id'
    ) THEN
        ALTER TABLE movimientos_monedas ADD CONSTRAINT uk_movimientos_request_id UNIQUE (request_id);
    END IF;
END$$
DELIMITER ;

CALL actualizar_economia_recompensas();
DROP PROCEDURE actualizar_economia_recompensas;

ALTER TABLE movimientos_monedas
    MODIFY COLUMN tipo ENUM(
        'compra', 'recompensa', 'ajuste',
        'recompensa_partida', 'recompensa_partida_perfecta',
        'continuar_partida', 'compra_personaje', 'compra_mapa', 'ajuste_pruebas'
    ) NOT NULL;
