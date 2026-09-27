# Auditoría integral de seguridad - Misión Matemática

**Fecha:** 26 de septiembre de 2026  
**Alcance:** revisión estática, pruebas automatizadas y ejecución local del backend Flask, frontend React/Vite y base MySQL de desarrollo. No se evaluaron servicios externos, infraestructura remota ni datos de producción.

## Resumen ejecutivo

Se revisaron 91 operaciones declaradas por los blueprints de la API. Siete son públicas (`register`, `login`, `logout`, `refresh`, recuperación, restablecimiento y verificación de correo); las demás requieren autenticación por decorador o una comprobación de rol/propiedad en el servicio que las atiende.

Se corrigieron cinco hallazgos de código o configuración y se actualizó la cadena de desarrollo del frontend. No quedaron vulnerabilidades conocidas en `npm audit --omit=dev`. La auditoría no encontró usos de interpolación directa de entrada de usuario en SQL, ejecución de código dinámico, HTML peligroso en React ni manejadores de carga de archivos JSON/PDF.

## Arquitectura y controles revisados

| Área | Implementación revisada | Resultado |
| --- | --- | --- |
| Autenticación | Passwords con `werkzeug.security`; JWT HMAC-SHA256 de acceso y refresh; refresh tokens almacenados por hash, rotados y revocados. | Conforme, con endurecimiento aplicado al encabezado JWT. |
| Autorización | `login_requerido`, `roles_requeridos`, consultas de rol vigentes en MySQL y validaciones de propiedad en juego, grupos, actividades, tienda y reportes. | Conforme en las rutas y flujos revisados. |
| Datos | Consultas parametrizadas con `%s`; transacciones y bloqueos `FOR UPDATE` en monedero, inventario, recompensas y continuaciones. | No se confirmó SQL injection. |
| Frontend | React escapa el contenido interpolado; no hay `dangerouslySetInnerHTML`, `innerHTML`, `eval` ni ejecución dinámica localizada. | No se confirmó XSS de código. |
| Red | CORS con lista explícita de orígenes locales; API en `127.0.0.1`; cabeceras `nosniff`, `DENY`, política de referencias, permisos y no caché para JSON. | Conforme para el despliegue local actual. |
| Auditoría | Bitácora persistente de mutaciones sin contraseñas ni tokens; rate limiting por IP y endpoint. | Conforme, con control de proxy endurecido. |

## Hallazgos y correcciones

| ID | Severidad | Hallazgo | Corrección aplicada | Evidencia |
| --- | --- | --- | --- | --- |
| SEC-01 | Alta | El endpoint público de registro aceptaba el valor `administrador` enviado por el cliente. | El registro público solo permite `estudiante` y `docente`; los administradores se crean por un flujo administrativo/controlado. | `backend/services/auth_service.py`, pruebas de registro público. |
| SEC-02 | Alta | Una instancia marcada como producción podía iniciar con el secreto JWT de desarrollo. | Se detiene el arranque si `APP_ENV=production` y el secreto es vacío o conocido como inseguro. | `backend/config.py`, `backend/app.py`, `test_config_security.py`. |
| SEC-03 | Media | Cualquier cliente podía enviar `X-Forwarded-For` para alterar la clave de rate limiting y auditoría en un despliegue directo. | La cabecera solo se usa cuando `TRUST_PROXY_HEADERS=true`; por defecto se usa `REMOTE_ADDR`. | `backend/services/security_service.py`, pruebas de IP. |
| SEC-04 | Media | El decodificador JWT no verificaba explícitamente el algoritmo declarado en el encabezado. | Solo admite encabezados `HS256` y `JWT`, incluso si otra variante tuviera firma válida. | `backend/services/jwt_service.py`, `test_jwt_service.py`. |
| SEC-05 | Baja | La ruta de error de contexto de juego referenciaba una variable inexistente al registrar una excepción. | Se reemplazó por un contexto de log seguro y definido. | `backend/routes/juego_routes.py`. |
| SEC-06 | Alta | `npm audit` detectó vulnerabilidades en Vite, esbuild y nanoid mientras Vite figuraba como dependencia de producción. | Vite se actualizó a `8.3.1`, el plugin React a `6.1.1` y ambos quedaron en `devDependencies`; se generó `package-lock.json`. | `frontend/package.json`, `frontend/package-lock.json`, auditoría final sin vulnerabilidades. |
| SEC-07 | Media (residual) | Los tokens de acceso y refresh se conservan en `localStorage`, por lo que un futuro XSS podría leerlos. | No se cambió el contrato de sesión durante esta auditoría; no se detectó XSS en el código revisado. | `frontend/src/services/sessionService.js`. |

## Autenticación, sesiones y permisos

- El inicio de sesión entrega tokens de acceso y refresh; el refresh se rota y el token anterior se revoca. El cierre de sesión revoca el refresh recibido sin exponer su valor en la bitácora.
- Las credenciales se comparan con hashes de Werkzeug. El mensaje de fallo de login es genérico y la prueba de inyección `"' OR 1=1 -- "` devuelve `401` sin autenticar.
- El payload JWT conserva el rol para contexto, pero las comprobaciones de permisos consultan al usuario y su rol actuales desde la base. Un token no puede elevar privilegios modificando ese campo.
- Se verificaron respuestas `401` sin token y `403` para estudiante contra una ruta de administración, conservando la sesión válida del usuario.

## Datos, juego y economía

- Las búsquedas y mutaciones revisadas usan parámetros MySQL. Las interpolaciones SQL encontradas corresponden a fragmentos estáticos o metadatos internos, no a valores de petición sin parametrizar.
- El juego verifica usuario, sección/asignación y pertenencia antes de iniciar o resolver una partida. Los endpoints de compatibilidad de respuesta correcta/incorrecta no mutan el juego.
- Las monedas, inventario y continuaciones se calculan y validan en el backend dentro de transacciones con bloqueo. El cliente envía identificadores, no precios, saldos ni recompensas confiables.
- No se localizaron endpoints de carga o importación JSON/PDF. Si se incorporan, deberán limitar tipo, tamaño, contenido, nombres, almacenamiento y autorización antes de habilitarlos.

## CORS, CSRF y cabeceras

- CORS no usa comodines: acepta únicamente `FRONTEND_URLS`. Una prueba de integración confirma que `http://127.0.0.1:5173` recibe la cabecera permitida y un origen ajeno no.
- La API usa tokens enviados en `Authorization`, no sesiones basadas en cookies; por ello no hay una superficie CSRF de cookie revisada. Si se migran refresh tokens a cookies, deberá añadirse protección CSRF y atributos `HttpOnly`, `Secure` y `SameSite` adecuados.
- La API aplica `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` y `Cache-Control: no-store` en JSON.

## Dependencias y configuración

- `npm audit --omit=dev --json`: 0 críticas, 0 altas, 0 medias, 0 bajas.
- `pip-audit` no está instalado en el entorno local, por lo que no se emitió un resultado de vulnerabilidades Python. Se recomienda integrarlo en CI o instalarlo en un entorno aislado de auditoría antes de un despliegue público.
- `.gitignore` excluye `.env`, entornos virtuales, `node_modules` y `dist`. No se mostraron ni copiaron secretos durante la auditoría.
- Para producción se requiere un `JWT_SECRET_KEY` único y fuerte mediante variable de entorno. El servidor local permanece enlazado a `127.0.0.1`.

## Pruebas y evidencia

| Verificación | Resultado |
| --- | --- |
| Compilación Python | Correcta con `python -m compileall`. |
| Suite backend | `146` pruebas correctas. |
| Flujo manual local de auditoría | Cambio auditado, consulta de bitácora y rate limit: correctos. |
| Pruebas frontend de etiquetas | `3` correctas. |
| Build frontend | Correcto con Vite `8.3.1`; 264 módulos transformados. |
| Pruebas nuevas de seguridad | Registro admin rechazado, SQL injection de login rechazada, JWT con algoritmo no permitido rechazado, CORS restrictivo y cabeceras defensivas correctos. |

## Riesgo residual y recomendaciones

1. El rate limit actual vive en memoria de un proceso. Para varias instancias se debe usar un almacenamiento compartido, por ejemplo Redis, y configurar correctamente el proxy de confianza.
2. Para un despliegue web público, evaluar refresh tokens en cookies `HttpOnly`, `Secure` y `SameSite` con protección CSRF; no migrarlos parcialmente porque cambiaría el contrato actual de autenticación.
3. Añadir un proceso de CI que ejecute `unittest`, `npm audit`, build y un escáner de dependencias Python.
4. Mantener los secretos fuera del repositorio y rotar el secreto JWT antes de cualquier despliegue no local.
5. Ejecutar una revisión autenticada de caja negra y pruebas de concurrencia contra un entorno de staging antes de exponer la API a internet.
