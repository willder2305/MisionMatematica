USE tesis_matematica_app;

-- Conserva compras e inventario existentes y normaliza solo la clasificación del catálogo.
UPDATE tienda_items
SET precio_monedas = 0, es_inicial = 1, estado = 'activo'
WHERE tipo = 'personaje' AND item_key IN ('masculino', 'femenino');

UPDATE tienda_items
SET precio_monedas = 25, es_inicial = 0, estado = 'activo'
WHERE tipo = 'personaje' AND item_key NOT IN ('masculino', 'femenino');

UPDATE tienda_items
SET nombre = 'Ángel'
WHERE tipo = 'personaje' AND item_key = 'angel';

-- Garantiza los dos starters para cada estudiante sin conceder personajes premium.
INSERT INTO usuario_items (id_usuario, id_item, estado)
SELECT u.id_usuario, ti.id_item, 'activo'
FROM usuarios u
INNER JOIN roles r ON r.id_rol = u.id_rol AND r.nombre = 'estudiante'
INNER JOIN tienda_items ti ON ti.tipo = 'personaje' AND ti.es_inicial = 1 AND ti.estado = 'activo'
ON DUPLICATE KEY UPDATE estado = 'activo';

-- La cuenta QA parte sin premium para poder comprobar una compra real de 25 monedas.
UPDATE usuario_items ui
INNER JOIN usuarios u ON u.id_usuario = ui.id_usuario
INNER JOIN tienda_items ti ON ti.id_item = ui.id_item
SET ui.estado = 'inactivo'
WHERE u.correo = 'estudiante500@mision.test'
  AND ti.tipo = 'personaje'
  AND ti.es_inicial = 0;
