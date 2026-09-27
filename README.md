# Mision Matematica

Sistema web educativo con React 18, Flask y MySQL. Incluye CRUD de grados/secciones, juego 2D, agente adaptativo por reglas, generador procedimental de ejercicios por plantillas, autenticacion JWT, onboarding, grupos con PIN, progreso de estudiante, asignaciones docentes, reportes del agente y panel administrador.

## Requisitos

- XAMPP o MySQL local.
- Python 3.12 compatible con el entorno `backend/.venv`.
- Node.js 20.19+ o 22.12+ y npm para Vite 8.

## Arquitectura

```text
Navegador -> React/Vite -> API REST Flask -> MySQL/MariaDB
```

React se compila como SPA y consume la API mediante Axios. Flask contiene autenticación JWT, reglas del agente, generación de ejercicios, juego y módulos académicos. MySQL/MariaDB conserva los datos funcionales y de auditoría. La navegación del frontend usa `history.pushState` y el evento interno `mm:navigation`; el proyecto no depende de React Router.

## Variables de entorno

Copiar `.env.example` como `.env` y ajustar valores locales:

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=tesis_matematica_app
JWT_SECRET_KEY=change-this-secret
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=10
RATE_LIMIT_API_PER_MINUTE=240
VITE_API_URL=http://127.0.0.1:5000/api
```

No colocar secretos reales en Git. SMTP requiere credenciales externas reales.

## Base de datos

Instalacion limpia:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\init_database.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

Actualizaciones incrementales principales:

```powershell
Get-Content database\create_auth_usuarios.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_onboarding_perfiles.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_grupos_pines.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_generador_plantillas.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_progreso_estudiante.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_asignaciones.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\create_auditoria_seguridad.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

## Ejecutar backend

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe app.py
```

API local:

```text
http://127.0.0.1:5000/api
```

## Ejecutar frontend

```powershell
cd "C:\dev\tesis 2\frontend"
npm.cmd run dev
```

Frontend local:

```text
http://127.0.0.1:5173
```

## Rutas principales

- `/`
- `/login`
- `/registro`
- `/recuperar-password`
- `/onboarding`
- `/panel-estudiante` (vista secundaria)
- `/actividades`
- `/secciones`
- `/grados`
- `/grupos`
- `/asignaciones`
- `/reportes`
- `/admin`
- `/plantillas`
- `/juego`

Flujo inicial:

- `/` muestra Login si no hay sesion.
- `/login` muestra Login si no hay sesion.
- Un usuario autenticado que entra a `/` o `/login` se redirige segun rol y onboarding.
- Rutas privadas sin sesion redirigen a `/login`.
- Rutas desconocidas no muestran Secciones por fallback.

Redireccion despues del login:

- Onboarding pendiente: `/onboarding`
- Estudiante: `/juego`
- Docente: `/reportes`
- Administrador: `/admin`

## Juego autenticado

El flujo normal de `/juego` requiere un estudiante autenticado con onboarding completado. React envia el token JWT mediante Axios y Flask asigna la partida al `id_usuario` del token; el frontend no decide el usuario de la partida.

Reglas aplicadas por backend:

- Estudiante de cuenta propia: solo puede iniciar partidas en el grado de su perfil.
- Estudiante de grupo educativo: solo puede iniciar partidas en grados de sus grupos activos.
- Consultar, responder, abandonar o usar rutas temporales de movimiento exige que la partida pertenezca al usuario autenticado.
- Cada intento queda conectado a `partidas_juego`, `intentos_juego`, `ejercicios_generados` y `decisiones_agente`.

## Panel estudiante

La ruta secundaria `/panel-estudiante` muestra:

- Bienvenida, personaje seleccionado, monedas reales y acceso a jugar.
- Estrellas por tema calculadas desde el progreso real.
- Accesos a `Mi personaje` y `Tienda`.

Endpoints:

- `GET /api/estudiante/panel`
- `GET /api/estudiante/progreso`
- `GET /api/estudiante/historial`
- `GET /api/estudiante/asignaciones`

Estas rutas no reciben `id_usuario`; toman el estudiante desde el token JWT para evitar acceso a datos de otros usuarios.

## Asignaciones

La ruta docente `/asignaciones` permite crear actividades para un grupo completo o una seccion especifica. La asignacion define temas, nivel inicial, cantidad de preguntas, fechas, estado y tipo de actividad.

Tipos soportados:

- `generacion_automatica`: el juego solicita ejercicios al agente/generador segun tema y dificultad.
- `ejercicios_especificos`: la asignacion guarda IDs de ejercicios existentes para control docente.

Endpoints:

- `GET /api/asignaciones`
- `POST /api/asignaciones`
- `PUT /api/asignaciones/<id_asignacion>`
- `PATCH /api/asignaciones/<id_asignacion>/estado`
- `GET /api/estudiante/asignaciones`

La ruta estudiante `/actividades` muestra solo asignaciones activas, vigentes y asociadas a sus grupos/secciones. Al iniciar una actividad, `/juego` registra `id_asignacion` en `partidas_juego`.

## Reportes docente

La ruta `/reportes` permite al docente consultar estudiantes de sus grupos, progreso general y decisiones del agente adaptativo.

Endpoints:

- `GET /api/docente/panel`
- `GET /api/docente/estudiantes`
- `GET /api/docente/reportes/agente`
- `GET /api/docente/reportes/agente/decisiones`

Filtros disponibles:

- `id_grupo`
- `id_seccion`
- `id_estudiante`
- `id_tema`
- `id_asignacion`
- `fecha_inicio`
- `fecha_fin`

## Panel administrador

La ruta `/admin` centraliza la gestion administrativa del sistema para usuarios con rol `administrador`.

Modulos disponibles:

- Usuarios: consulta, filtros por rol/estado/busqueda, cambio de rol y cambio de estado.
- Temas: creacion, edicion, filtros por grado/estado y activacion/desactivacion.
- Ejercicios: creacion manual, edicion, filtros por tema/nivel/estado y activacion/desactivacion.
- Reglas: consulta y actualizacion de reglas del agente adaptativo.
- Auditoria: consulta de acciones sensibles registradas en bitacora.
- Reportes: metricas globales y accesos directos a reportes, plantillas, grados y secciones.

Endpoints:

- `GET /api/admin/panel`
- `GET /api/admin/usuarios`
- `PATCH /api/admin/usuarios/<id_usuario>/estado`
- `PATCH /api/admin/usuarios/<id_usuario>/rol`
- `GET /api/admin/temas`
- `POST /api/admin/temas`
- `PUT /api/admin/temas/<id_tema>`
- `PATCH /api/admin/temas/<id_tema>/estado`
- `GET /api/admin/ejercicios`
- `POST /api/admin/ejercicios`
- `PUT /api/admin/ejercicios/<id_ejercicio>`
- `PATCH /api/admin/ejercicios/<id_ejercicio>/estado`
- `GET /api/admin/reglas`
- `PUT /api/admin/reglas/<id_regla>`
- `PATCH /api/admin/reglas/<id_regla>/estado`
- `GET /api/admin/auditoria`

## Seguridad y auditoria

El backend aplica controles transversales sobre `/api/*`:

- Headers basicos de seguridad: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y `Cache-Control` para JSON.
- Rate limit en memoria por IP y endpoint.
- Bitacora persistente de acciones sensibles `POST`, `PUT`, `PATCH` y `DELETE`.
- La bitacora guarda nombres de campos, metodo, ruta, estado HTTP, IP y usuario, pero omite contrasenas, tokens y refresh tokens.

Variables opcionales:

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_AUTH_PER_MINUTE`
- `RATE_LIMIT_API_PER_MINUTE`

## Optimizacion y QA

El frontend usa carga diferida por ruta con `React.lazy` y `Suspense`. Esto evita cargar modulos pesados, como `/juego`, desde el arranque de la aplicacion.

QA basico ejecutado:

- Build de produccion con Vite.
- Verificacion de chunks por pagina.
- Revision Playwright de `/login`, `/registro` y `/secciones`.
- Verificacion movil a 320 px sin scroll horizontal.
- Revision de consola sin errores en `/secciones` con backend activo.

## Produccion y despliegue

La configuración de referencia para Linux con Nginx, Gunicorn, systemd y HTTPS está en [DEPLOY.md](DEPLOY.md). Incluye el diagrama de red, variables de entorno, pasos de publicación, healthcheck `GET /api/health`, backups y reversión.

La evaluación de capacidad, almacenamiento y compatibilidad de proveedores está en [EVALUACION_HOSTING.md](EVALUACION_HOSTING.md). No subir `.env`, volúmenes de base de datos, `node_modules`, `.venv`, `dist` ni artefactos de pruebas.

## Docker

La arquitectura Docker separa Nginx/React, Gunicorn/Flask y MySQL 8.4. El frontend se compila con Node en una etapa de build y el contenedor final solo ejecuta Nginx; la API se consume en mismo origen mediante `/api`.

Prueba local de la arquitectura completa:

```powershell
Copy-Item .env.docker.example .env
docker compose -f docker-compose.local.yml up --build
```

El frontend queda en `http://localhost:8080`, backend en `http://localhost:8000` y MySQL en `localhost:3307`. Producción usa solo el puerto 80 y no publica MySQL:

```bash
cp .env.docker.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

La guía de VPS, HTTPS, backups, restauración, migraciones manuales y actualización está en [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md). No ejecutar `docker compose down -v` en producción porque elimina el volumen de MySQL.

## Pruebas

Backend:

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Demos reales con MySQL:

```powershell
.\.venv\Scripts\python.exe tests\demo_auth_flow.py
.\.venv\Scripts\python.exe tests\demo_onboarding_flow.py
.\.venv\Scripts\python.exe tests\demo_grupos_pines_flow.py
.\.venv\Scripts\python.exe tests\demo_adaptacion_generador.py
.\.venv\Scripts\python.exe tests\demo_asignaciones_flow.py
.\.venv\Scripts\python.exe tests\demo_reportes_docente_flow.py
.\.venv\Scripts\python.exe tests\demo_admin_flow.py
.\.venv\Scripts\python.exe tests\demo_auditoria_seguridad_flow.py
.\.venv\Scripts\python.exe tests\demo_rutas_autenticacion_flow.py
```

Build frontend:

```powershell
cd "C:\dev\tesis 2\frontend"
npm.cmd run build
```

Pruebas del frontend:

```powershell
cd "C:\dev\tesis 2\frontend"
npm.cmd run test:labels
```

## Ramas Git

- `main`: rama estable y desplegable.
- `local`: rama de trabajo local creada desde el mismo commit base que `main`.

La automatización de GitHub Actions valida backend con MySQL 8 y frontend en ambas ramas. No realiza despliegues ni administra secretos de producción.

## Errores comunes

- Si React muestra error de conexion, verificar que Flask este activo en `127.0.0.1:5000`.
- Si Flask no conecta a base de datos, verificar que MySQL/XAMPP este encendido y que `.env` coincida.
- Si el frontend no carga cambios, detener y volver a iniciar `npm.cmd run dev`.
