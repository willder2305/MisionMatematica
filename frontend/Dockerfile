FROM node:22.12-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# VITE_API_URL se incorpora al bundle; solo admite la ruta pública de la API.
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:1.31.5-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/docker/nginx/bootstrap.conf /etc/nginx/templates/bootstrap.conf
COPY deploy/docker/nginx/https.conf /etc/nginx/templates/https.conf
COPY deploy/docker/nginx/security-headers.conf /etc/nginx/includes/security-headers.conf
COPY --chmod=755 deploy/docker/nginx/40-select-config.sh /docker-entrypoint.d/40-select-config.sh

EXPOSE 80 443
