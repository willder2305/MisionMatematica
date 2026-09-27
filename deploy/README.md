# Archivos de despliegue

Los archivos de esta carpeta son plantillas para un VPS Linux con Nginx y systemd. No contienen credenciales, dominio, IP pública ni certificados reales.

1. Copiar el proyecto a `/opt/mision-matematica` y crear su entorno virtual en `backend/.venv`.
2. Crear `/etc/mision-matematica/mision-matematica.env` desde `.env.example`, con permisos `640` y propietario `root:www-data`.
3. Ajustar `server_name`, rutas de certificado y usuario de `deploy/nginx-mision-matematica.conf`; instalarlo en `/etc/nginx/sites-available/`.
4. Copiar `mision-matematica.service` a `/etc/systemd/system/`, ejecutar `systemctl daemon-reload` y habilitar el servicio.
5. Construir `frontend/dist` en el servidor o publicar el resultado del build. Validar primero `GET /api/health` desde el propio VPS.

`run-gunicorn.sh` toma `GUNICORN_BIND`, `GUNICORN_WORKERS`, `GUNICORN_THREADS` y `GUNICORN_TIMEOUT` del archivo de entorno. Los valores por defecto permiten un arranque conservador; se deben ajustar con métricas reales.
