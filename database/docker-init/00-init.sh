#!/usr/bin/env bash
set -euo pipefail

# La imagen oficial solo ejecuta este script al crear un volumen de MySQL vacío.
cd /docker-entrypoint-initdb.d
mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" < database/init_database.sql
