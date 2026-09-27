#!/usr/bin/env sh
# Ejecuta manualmente un SQL revisado contra la base del stack Docker activo.
set -eu

if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
  echo "Uso: $0 database/archivo.sql" >&2
  exit 64
fi

case "$1" in
  database/*.sql) ;;
  *)
    echo "El SQL debe pertenecer al directorio database/." >&2
    exit 64
    ;;
esac

docker compose -f docker-compose.prod.yml exec -T db sh -c \
  'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < "$1"
