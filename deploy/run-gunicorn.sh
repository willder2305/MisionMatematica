#!/usr/bin/env sh
# Inicia el servidor WSGI con límites configurables desde el EnvironmentFile.
set -eu

exec gunicorn \
  --bind "${GUNICORN_BIND:-127.0.0.1:8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
