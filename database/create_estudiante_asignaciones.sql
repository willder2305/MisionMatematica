USE tesis_matematica_app;

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

INSERT INTO estudiante_asignaciones
    (id_asignacion, id_estudiante, estado, fecha_asignacion, fecha_inicio,
     fecha_completada, cantidad_intentos, ultima_partida, fecha_ultima_actividad)
SELECT
    a.id_asignacion,
    pe.id_usuario,
    CASE
        WHEN completada.id_partida IS NOT NULL THEN 'completada'
        WHEN COUNT(p.id_partida) > 0 THEN 'en_progreso'
        ELSE 'pendiente'
    END AS estado,
    a.fecha_inicio,
    MIN(p.fecha_inicio),
    CASE WHEN completada.id_partida IS NOT NULL THEN completada.fecha_fin ELSE NULL END,
    COUNT(p.id_partida),
    MAX(p.id_partida),
    MAX(COALESCE(p.fecha_ultima_actividad, p.fecha_fin, p.fecha_inicio))
FROM asignaciones a
INNER JOIN perfiles_estudiante pe
    ON pe.id_institucion_grado = a.id_institucion_grado
   AND pe.id_seccion = a.id_seccion
   AND pe.modalidad = 'grupo_educativo'
LEFT JOIN partidas_juego p
    ON p.id_asignacion = a.id_asignacion
   AND p.id_usuario = pe.id_usuario
LEFT JOIN (
    SELECT p1.id_asignacion, p1.id_usuario, MAX(p1.id_partida) AS id_partida, MAX(p1.fecha_fin) AS fecha_fin
    FROM partidas_juego p1
    WHERE p1.estado = 'completada'
      AND p1.total_correctos >= 10
      AND p1.casilla_actual >= 10
    GROUP BY p1.id_asignacion, p1.id_usuario
) completada
    ON completada.id_asignacion = a.id_asignacion
   AND completada.id_usuario = pe.id_usuario
GROUP BY a.id_asignacion, pe.id_usuario, a.fecha_inicio, completada.id_partida, completada.fecha_fin
ON DUPLICATE KEY UPDATE
    estado = CASE
        WHEN estudiante_asignaciones.estado = 'completada' THEN estudiante_asignaciones.estado
        ELSE VALUES(estado)
    END,
    fecha_inicio = COALESCE(estudiante_asignaciones.fecha_inicio, VALUES(fecha_inicio)),
    fecha_completada = COALESCE(estudiante_asignaciones.fecha_completada, VALUES(fecha_completada)),
    cantidad_intentos = GREATEST(estudiante_asignaciones.cantidad_intentos, VALUES(cantidad_intentos)),
    ultima_partida = COALESCE(estudiante_asignaciones.ultima_partida, VALUES(ultima_partida)),
    fecha_ultima_actividad = COALESCE(estudiante_asignaciones.fecha_ultima_actividad, VALUES(fecha_ultima_actividad));
