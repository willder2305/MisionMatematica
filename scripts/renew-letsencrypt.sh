#!/usr/bin/env bash
set -euo pipefail

# One-shot renewal command suitable for cron or a systemd timer.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

compose() {
    docker compose --env-file .env -f docker-compose.prod.yml "$@"
}

if [[ ! -f .env ]]; then
    echo "Falta .env; no se puede renovar el certificado." >&2
    exit 1
fi

compose run --rm --no-deps certbot renew --quiet
compose exec -T frontend nginx -t
compose exec -T frontend nginx -s reload
