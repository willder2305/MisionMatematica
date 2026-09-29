#!/usr/bin/env bash
set -euo pipefail

# Issues the first certificate only after the HTTP bootstrap container is healthy.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

compose() {
    docker compose --env-file .env -f docker-compose.prod.yml "$@"
}

env_value() {
    local key="$1"
    sed -n "s/^${key}=//p" .env | tail -n 1 | tr -d '\r'
}

if [[ ! -f .env ]]; then
    echo "Falta .env. Cree el archivo desde .env.docker.example antes de emitir el certificado." >&2
    exit 1
fi

primary_domain="${PRIMARY_DOMAIN:-$(env_value PRIMARY_DOMAIN)}"
www_domain="${WWW_DOMAIN:-$(env_value WWW_DOMAIN)}"
email="${LETSENCRYPT_EMAIL:-$(env_value LETSENCRYPT_EMAIL)}"

if [[ "$primary_domain" != "misionmatematica.com" || "$www_domain" != "www.misionmatematica.com" ]]; then
    echo "El certificado de producción debe incluir misionmatematica.com y www.misionmatematica.com." >&2
    exit 1
fi

if [[ -z "$email" || "$email" == "CAMBIAR_CORREO_ADMIN" ]]; then
    echo "Defina LETSENCRYPT_EMAIL con un correo real en .env." >&2
    exit 1
fi

compose config -q
compose up -d db backend frontend
compose exec -T frontend wget -q -O /dev/null http://127.0.0.1/__nginx_health

echo "Solicitando certificado para ${primary_domain} y ${www_domain}."
compose run --rm --no-deps certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email "$email" \
    --agree-tos \
    --no-eff-email \
    --keep-until-expiring \
    -d "$primary_domain" \
    -d "$www_domain"

# Recreate Nginx so its startup selector switches from HTTP bootstrap to TLS.
compose up -d --force-recreate frontend
compose exec -T frontend nginx -t
echo "Certificado instalado. Verifique https://${primary_domain} y https://${www_domain}."
