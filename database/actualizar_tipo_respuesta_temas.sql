-- Regla canónica de presentación por tema. La respuesta escrita es el valor seguro por defecto.
USE tesis_matematica_app;

DELIMITER $$
DROP PROCEDURE IF EXISTS actualizar_tipo_respuesta_temas$$
CREATE PROCEDURE actualizar_tipo_respuesta_temas()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'temas'
          AND COLUMN_NAME = 'tipo_respuesta'
    ) THEN
        ALTER TABLE temas
            ADD COLUMN tipo_respuesta ENUM('seleccion_multiple', 'numerica')
                NOT NULL DEFAULT 'numerica' AFTER estado;
    END IF;
END$$
DELIMITER ;

CALL actualizar_tipo_respuesta_temas();
DROP PROCEDURE IF EXISTS actualizar_tipo_respuesta_temas;

-- Solo estos temas conservan las cuatro opciones; cualquier tema futuro queda escrito por defecto.
UPDATE temas
SET tipo_respuesta = CASE
    WHEN nombre_tema IN (
        'Suma de fracciones', 'Resta de fracciones', 'Multiplicacion de fracciones',
        'Division de fracciones', 'Regla de tres directa', 'Regla de tres simple',
        'Regla de tres inversa', 'Operaciones combinadas de fracciones',
        'Conversiones de fracciones', 'Conversion de fracciones', 'Geometria'
    ) THEN 'seleccion_multiple'
    ELSE 'numerica'
END;

-- Las plantillas y ejercicios heredados no pueden contradecir la regla del tema.
UPDATE plantillas_ejercicios p
INNER JOIN temas t ON t.id_tema = p.id_tema
SET p.tipo_respuesta = t.tipo_respuesta;

UPDATE ejercicios e
INNER JOIN temas t ON t.id_tema = e.id_tema
SET e.tipo_respuesta = t.tipo_respuesta;
