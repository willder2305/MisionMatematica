#!/usr/bin/env bash
set -euo pipefail

# La imagen oficial solo ejecuta este script al crear un volumen de MySQL vacío.
cd /docker-entrypoint-initdb.d
# El cliente debe leer los scripts UTF-8 como utf8mb4 antes de insertarlos.
mysql --protocol=socket --default-character-set=utf8mb4 -uroot -p"${MYSQL_ROOT_PASSWORD}" < database/init_database.sql
