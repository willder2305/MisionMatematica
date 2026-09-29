#!/bin/sh
set -eu

primary_domain="${PRIMARY_DOMAIN:-misionmatematica.com}"
certificate_dir="/etc/letsencrypt/live/${primary_domain}"

if [ "${primary_domain}" != "misionmatematica.com" ]; then
    echo "PRIMARY_DOMAIN debe ser misionmatematica.com para esta configuración de producción." >&2
    exit 1
fi

if [ -f "${certificate_dir}/fullchain.pem" ] && [ -f "${certificate_dir}/privkey.pem" ]; then
    cp /etc/nginx/templates/https.conf /etc/nginx/conf.d/default.conf
    echo "Nginx iniciado con HTTPS para ${primary_domain}."
else
    cp /etc/nginx/templates/bootstrap.conf /etc/nginx/conf.d/default.conf
    echo "Nginx iniciado en modo HTTP temporal para emitir el certificado TLS."
fi
