USE tesis_matematica_app;

-- Normaliza el texto visible sin cambiar la clave técnica angel ni relaciones de inventario.
UPDATE tienda_items
SET nombre = CONVERT(0xC3816E67656C USING utf8mb4)
WHERE tipo = 'personaje' AND item_key = 'angel';
