# Documentacion del sistema Mision Matematica

Fecha de documentacion: 2026-09-19

## Contextos de progresion academica

El sistema separa de forma persistente dos mundos que no comparten filas adaptativas ni reglas de promocion.

```text
JUEGO PERSONAL
Estudiante
  -> Tema
  -> progreso_personal_tema
  -> grado curricular personal
  -> dificultad
  -> generador

ACTIVIDAD ASIGNADA
Estudiante
  -> Asignacion
  -> grado base de la asignacion
  -> tema asignado
  -> progreso_asignacion_tema_estudiante
  -> dificultad dentro del mismo grado
  -> generador
```

### Juego personal

Todo estudiante, independiente o institucional, comienza cada tema compartido en `Cuarto` y `Facil`; el grado del PIN o del perfil no altera ese inicio. La ruta por tema es `Cuarto Facil -> Medio -> Dificil -> Quinto Facil -> Medio -> Dificil -> Sexto Facil -> Medio -> Dificil`.

La dificultad cambia con las reglas adaptativas existentes. La promocion curricular se evalua en `evaluar_progresion_personal()` y centraliza sus umbrales en `PROMOCION_GRADO_CONFIG`: 20 ejercicios, 85% de precision, tres partidas distintas y una racha de seis aciertos mientras el tema esta en dificil. Al promover, el nuevo grado reinicia su dificultad en facil; los intentos anteriores se conservan en partidas e intentos. Sexto es el limite curricular.

`progreso_personal_catalogo` evita que un solo tema abra contenido superior: Quinto y Sexto requieren evidencia de varios temas representativos. Por eso los temas exclusivos de Quinto y Geometria no aparecen hasta que el catalogo correspondiente se desbloquea; al aparecer comienzan en el grado que los introduce y en facil.

### Actividades asignadas

Una actividad toma grado y temas de `asignaciones` e `institucion_grados`. Su estado vive en `progreso_asignacion_tema_estudiante`, identificado por estudiante, asignacion y tema. El agente puede cambiar solo `Facil`, `Intermedio` y `Dificil` dentro del grado asignado; nunca promueve ni desciende el grado de una actividad.

`partidas_juego.tipo_contexto` y `decisiones_agente.tipo_contexto` registran `personal` o `asignacion`. La migracion `database/actualizar_contextos_progresion_curricular.sql` clasifica el historial por `id_asignacion`, conserva las tablas antiguas y registra en `incidencias_contexto_progresion` los agregados por tema donde los dos contextos estaban mezclados, sin inferir un estado nuevo. Se incluye desde `init_database.sql`.

Los reportes docentes usan solo partidas `asignacion`; el juego personal no se presenta como una nota. El administrador conserva acceso al historial de ambos contextos mediante la columna de contexto.

### Exportación de reportes y asignaciones

Los reportes filtrados del docente y del administrador pueden descargarse en PDF o XLSX. Las rutas vuelven a consultar los datos autorizados con los filtros recibidos antes de generar el archivo; `backend/services/report_export_service.py` crea los archivos en memoria, neutraliza fórmulas de Excel y entrega nombres de descarga sin rutas internas.

Las asignaciones creadas o editadas siempre guardan diez ejercicios. La interfaz ya no solicita esa cantidad y `backend/services/asignaciones_service.py` ignora cualquier valor que un cliente alterado intente enviar.

### Propiedad de personajes y compras

El catálogo usa `tienda_items.id_item` como identificador persistente y `item_key` como clave técnica estable. `usuario_items` mantiene una única relación por usuario e ítem mediante su restricción única; solo una relación con estado `activo` representa propiedad. Si una relación histórica está `inactivo`, una compra válida la reactiva en la misma transacción que descuenta el saldo y registra el movimiento de monedas, sin insertar una fila duplicada.

Las respuestas de Tienda e inventario proceden de la misma lectura del backend e incluyen los estados `adquirido` y `seleccionado`. Tienda y Mi personaje usan la misma función visual para decidir entre comprar, seleccionar o mostrar el personaje actual. Los precios se consultan desde el catálogo: los personajes premium cuestan 25 monedas y los mapas premium 20.

## Optimizacion y usuario QA local

La aplicacion conserva el enrutamiento SPA y carga diferida por pagina. `apiClient` es la unica instancia Axios, incluye un limite de espera de 15 segundos y coordina un unico refresh de sesion para solicitudes 401 concurrentes. Los errores 403, 404 y 500 no invalidan la sesion.

Las previews de mapas de la tienda usan carga diferida del navegador; los fondos completos y las animaciones no se convierten ni se reducen porque son assets pixel-art necesarios para el juego. Al iniciar una partida se usa solamente el mapa y el personaje resueltos para esa partida.

La migracion `database/optimizar_indices_y_seed_qa.sql` agrega de forma idempotente indices compuestos para partidas activas, intentos, decisiones del agente, movimientos de monedas, inventario y actividades del estudiante. No elimina historicos ni modifica reglas de negocio. La migracion se incluye en la instalacion limpia mediante `init_database.sql`.

### Usuario local de pruebas

El usuario siguiente existe solo para desarrollo local y QA; no se inserta desde `init_database.sql` ni debe ejecutarse con `APP_ENV=production`:

```text
Correo: estudiante500@mision.test
Contrasena: Mision500!
Rol: estudiante
Modalidad: cuenta propia (independiente)
Grado: Sexto (6P)
Onboarding: completado
Saldo inicial: 500 monedas
```

Para crearlo o verificarlo, desde `backend` ejecute:

```powershell
$env:APP_ENV = "development"
.\.venv\Scripts\python.exe .\scripts\seed_dev_student.py
```

El comando es idempotente y no cambia el saldo si el usuario ya fue sembrado. Para restaurar deliberadamente el saldo a 500 durante pruebas se usa `--reset-balance`; esa operacion deja un movimiento `ajuste_pruebas` auditable. La contrasena se guarda con `generate_password_hash`, el mismo mecanismo de autenticacion del sistema.

## 1. Resumen general

El sistema implementado es una aplicacion web para **Mision Matematica**, desarrollada con:

- **Frontend:** React 18 con Vite.
- **Backend:** Python Flask.
- **Base de datos:** MySQL compatible con XAMPP/MySQL local.
- **Comunicacion HTTP:** Axios desde React hacia API REST Flask.
- **Estilo visual:** interfaz pixel-art responsive.

El sistema contiene actualmente estos modulos principales:

- Administracion de **grados**.
- Administracion de **secciones**.
- Primera version funcional del **juego 2D** con personajes M1/F1.
- Autenticacion con JWT.
- Onboarding para estudiantes y docentes.
- Pantalla docente `Mi institucion` con institucion y grados/secciones asignados.
- PIN de acceso a secciones institucionales con compatibilidad tecnica legacy.
- Agente inteligente adaptativo con generacion procedimental de ejercicios.
- Asignaciones docentes por grado institucional y seccion.
- Reportes docentes del progreso y decisiones del agente.
- Panel administrador para usuarios, temas, ejercicios, reglas y reportes globales.
- Auditoria persistente, rate limit y headers basicos de seguridad.

## Modelo academico institucional

El modelo academico vigente separa tres casos:

- Estudiante independiente: juega sin institucion, sin grado institucional, sin seccion y sin PIN. No selecciona grado; el sistema inicia internamente en `Cuarto` y puede promover el grado curricular por tema.
- Estudiante institucional: ingresa con PIN; el backend resuelve institucion, grado institucional, grado base, seccion y docente. Su grado escolar no cambia por rendimiento, solo mediante un nuevo PIN.
- Docente: debe pertenecer a una institucion antes de completar su configuracion academica.

Los grados base son un catalogo global. Deben existir como registros principales:

- `4P` - `Cuarto`
- `5P` - `Quinto`
- `6P` - `Sexto`

Estos grados no pertenecen a una institucion y no deben duplicarse por colegio. Todo contenido matematico global depende del grado base: temas, ejercicios manuales, plantillas, generador y agente adaptativo.

Las instituciones se guardan en `instituciones` con `nombre_normalizado` para evitar duplicados por mayusculas o espacios. Cada institucion tiene automaticamente tres registros en `institucion_grados`, uno por cada grado base. La relacion es:

```text
instituciones
  -> institucion_grados
      -> grados.id_grado como grado base
```

Las secciones configurables permitidas son exactamente `A`, `B`, `C` y `D`. El frontend no muestra campo libre para nombres de seccion ni permite seleccionar `Única`. Si un docente selecciona un grado y no marca ninguna seccion A-D, el backend crea o reactiva automaticamente la seccion `Única` como fallback. `Única` no se muestra en Secciones; su PIN aparece desde Grados como `Seccion unica`.

Dentro de una misma institucion, una seccion activa solo puede tener un docente activo. La validacion se realiza en frontend, backend transaccional y base de datos cuando no existen conflictos historicos pendientes. Las relaciones retiradas se inactivan con `estado = 'inactivo'` y `fecha_fin`.

Los grupos quedan como entidad tecnica interna legacy para compatibilidad historica de PIN y estudiantes ya vinculados. No existe modulo visible de Grupos ni formulario para crear grupos manualmente. El runtime nuevo de asignaciones y reportes no usa `id_grupo` como eje funcional.

La ruta inicial del docente despues del login es `/mi-institucion`. Desde ahi puede ver su institucion y los grados/secciones vinculados. El cambio libre de institucion no se expone desde esta pantalla.

El PIN se genera solo desde backend, tiene seis digitos, se guarda como texto y puede iniciar con cero. Un PIN activo resuelve institucion, grado institucional, grado base y seccion sin que el estudiante conozca IDs internos.

Para estudiantes institucionales existe `/actualizar-grado`: valida un nuevo PIN, muestra confirmacion de institucion/grado/seccion/docente y solo al confirmar cierra la matricula activa anterior e inserta la nueva.

Ninguna entidad funcional debe eliminarse fisicamente desde la interfaz ni desde runtime productivo. Las acciones visibles usan activacion/desactivacion cuando corresponde. Las relaciones historicas de asignaciones, docente-secciones y opciones se inactivan con `estado`/`fecha_fin`; los `DELETE FROM` quedan reservados para tests/demo aislados o migraciones documentadas.

## 2. Estructura principal del proyecto

```text
C:\dev\tesis 2
├── backend
│   ├── app.py
│   ├── config.py
│   ├── db.py
│   ├── requirements.txt
│   ├── models
│   │   ├── grado.py
│   │   ├── seccion.py
│   │   └── partida_juego.py
│   └── routes
│       ├── grados_routes.py
│       ├── secciones_routes.py
│       └── juego_routes.py
├── database
│   ├── init_database.sql
│   ├── create_grados.sql
│   ├── create_secciones.sql
│   └── create_partidas_juego.sql
└── frontend
    ├── package.json
    └── src
        ├── main.jsx
        ├── styles.css
        ├── services
        ├── pages
        ├── components
        └── config
```

## 3. Base de datos

La base de datos configurada por defecto es:

```text
tesis_matematica_app
```

Se definieron los scripts SQL en la carpeta `database`.

### 3.1 Tabla `grados`

Tabla para administrar el catalogo global de grados base.

Campos principales:

- `id_grado`
- `codigo_grado`
- `nombre_grado`
- `descripcion`
- `orden_visualizacion`
- `estado`
- `fecha_creacion`
- `fecha_modificacion`

Restricciones:

- `codigo_grado` unico.
- `nombre_grado` unico.
- `estado` limitado a `activo` o `inactivo`.

Datos iniciales incluidos:

- `4P` - Cuarto.
- `5P` - Quinto.
- `6P` - Sexto.

### 3.1.1 Tabla `instituciones`

Tabla para instituciones educativas asociadas a docentes.

Campos principales:

- `id_institucion`
- `nombre`
- `nombre_normalizado`
- `descripcion`
- `estado`
- `fecha_creacion`
- `fecha_modificacion`

### 3.1.2 Tabla `institucion_grados`

Tabla que conecta cada institucion con los tres grados base sin duplicar registros en `grados`.

Campos principales:

- `id_institucion_grado`
- `id_institucion`
- `id_grado_base`
- `estado`
- `fecha_creacion`
- `fecha_modificacion`

### 3.2 Tabla `secciones`

Tabla para administrar secciones asociadas a grados institucionales.

Campos principales:

- `id_seccion`
- `id_grado`
- `id_institucion_grado`
- `nombre_seccion`
- `descripcion`
- `estado`
- `fecha_creacion`
- `fecha_modificacion`

Restricciones:

- Relacion compatible con `grados.id_grado` para historicos.
- Relacion nueva con `institucion_grados.id_institucion_grado`.
- Valores permitidos: `A`, `B`, `C`, `D` y `Única`.
- `Única` se genera solo desde backend como fallback.
- `estado` limitado a `activo` o `inactivo`.

### 3.3 Tabla `partidas_juego`

Tabla para almacenar partidas del juego.

Campos principales:

- `id_partida`
- `id_usuario`
- `id_asignacion`
- `personaje`
- `mapa`
- `casilla_actual`
- `total_correctos`
- `total_errores`
- `estado`
- `fecha_inicio`
- `fecha_fin`

Reglas actuales:

- La partida inicia en `casilla_actual = 0`.
- Cada respuesta correcta avanza una casilla.
- La casilla final es `10`.
- Un error incrementa `total_errores`, pero no cambia la casilla.
- El estado puede ser `en_curso`, `completada`, `sin_vidas` o `abandonada`.
- La base de datos no guarda coordenadas visuales del personaje; solo guarda `casilla_actual`.
- En el flujo actual, toda partida normal debe quedar asociada al `id_usuario` autenticado.
- Si la partida nace desde una actividad docente, queda asociada tambien a `id_asignacion`.

### 3.5 Tablas de asignaciones

`asignaciones` define actividades creadas por docentes para un grado institucional y una seccion:

- `id_asignacion`
- `id_docente`
- `id_institucion_grado`
- `id_grupo` presente solo por compatibilidad legacy; el runtime nuevo no lo usa para consultar y fuerza `NULL` al crear o actualizar asignaciones.
- `id_seccion`
- `nombre`
- `instrucciones`
- `tipo`
- `id_nivel_inicial`
- `cantidad_preguntas`
- `fecha_inicio`
- `fecha_limite`
- `obligatoria`
- `estado`

`asignacion_temas` conecta cada asignacion con uno o varios temas. Las relaciones retiradas se marcan `inactivo` y conservan historial.

`asignacion_ejercicios` conecta asignaciones manuales con ejercicios existentes. Las relaciones retiradas se marcan `inactivo`.

`secciones.id_grado` permanece solo por compatibilidad historica; las consultas nuevas usan `secciones.id_institucion_grado`.

### 3.4 Tablas de progreso

`progreso_estudiante` resume los datos generales del estudiante:

- `id_usuario`
- `total_partidas`
- `total_ejercicios`
- `total_aciertos`
- `total_errores`
- `porcentaje_aciertos`
- `puntos`
- `mejor_puntuacion`
- `tiempo_total_ms`
- `ultima_actividad`

`progreso_tema_estudiante` resume el avance por tema:

- `id_usuario`
- `id_tema`
- `id_grado_curricular_actual`
- `id_nivel_actual`
- `total_intentos`
- `total_aciertos`
- `total_errores`
- `porcentaje_aciertos`
- `racha_correctas`
- `racha_incorrectas`
- `estado_dominio`
- `tiempo_promedio_ms`
- `cambios_dificultad`
- `ultima_practica`

`promociones_curriculares_tema` audita promociones curriculares de cuenta propia:

- `id_usuario`
- `id_tema_anterior`
- `id_tema_nuevo`
- `id_grado_anterior`
- `id_grado_nuevo`
- `motivo`
- `metricas_json`
- `fecha_promocion`

## 4. Backend Flask

El backend esta en la carpeta `backend`.

Archivo principal:

```text
backend/app.py
```

Funciones principales:

- Crea la aplicacion Flask.
- Registra Blueprints de grados, secciones y juego.
- Configura CORS para permitir peticiones del frontend Vite.

### 4.1 Configuracion

Archivo:

```text
backend/config.py
```

Variables soportadas por `.env`:

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
FRONTEND_URLS
```

Valores por defecto relevantes:

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=tesis_matematica_app
```

Orígenes CORS permitidos por defecto:

```text
http://127.0.0.1:5173
http://127.0.0.1:5174
http://localhost:5173
http://localhost:5174
```

Esto corrige el problema anterior donde React no podia consumir la API por bloqueo CORS.

### 4.2 Conexion MySQL

Archivo:

```text
backend/db.py
```

Contiene `obtener_conexion()`, que abre conexiones a MySQL usando `mysql-connector-python`.

## 5. API REST implementada

Todas las respuestas siguen un formato JSON uniforme:

```json
{
  "success": true,
  "message": "Mensaje de resultado",
  "data": {},
  "errors": {}
}
```

### 5.0 Integracion estudiante-juego

El juego se ejecuta como flujo autenticado:

- `POST /api/juego/partidas` exige token JWT de estudiante.
- El backend toma `id_usuario` desde el token y lo guarda en `partidas_juego`.
- El frontend no envia ni decide el usuario propietario de la partida.
- Para cuenta propia, el grado de la partida debe coincidir con `perfiles_estudiante.id_grado`.
- Para estudiante institucional, el grado debe coincidir con `perfiles_estudiante.id_institucion_grado` y su seccion.
- `GET /api/juego/partidas/<id_partida>`, `POST /respuesta`, `POST /salir` y las rutas temporales de movimiento validan propiedad de partida.
- Cada respuesta crea un registro en `intentos_juego`, alimenta el motor de reglas y registra la decision en `decisiones_agente`.

### 5.1 Endpoints de grados

Prefijo:

```text
/api/grados
```

Endpoints:

| Metodo | Ruta | Funcion |
|---|---|---|
| GET | `/api/grados` | Lista grados, con filtro opcional por estado. |
| GET | `/api/grados/opciones` | Lista grados activos para selectores. |
| GET | `/api/grados/<id_grado>` | Consulta un grado por ID. |
| POST | `/api/grados` | Crea un grado. |
| PUT | `/api/grados/<id_grado>` | Actualiza un grado. |
| PATCH | `/api/grados/<id_grado>/estado` | Activa o desactiva un grado. |

Validaciones implementadas:

- Codigo obligatorio.
- Nombre obligatorio.
- Codigo maximo de 20 caracteres.
- Nombre maximo de 100 caracteres.
- Descripcion maxima de 255 caracteres.
- Orden de visualizacion mayor que cero.
- Estado solo `activo` o `inactivo`.
- Prevencion de duplicados por codigo y nombre.
- No existe endpoint publico de eliminacion; el cambio operativo se realiza por estado.

### 5.2 Endpoints de secciones

Prefijo:

```text
/api/secciones
```

Endpoints:

| Metodo | Ruta | Funcion |
|---|---|---|
| GET | `/api/secciones` | Lista secciones, con filtro opcional por estado. |
| GET | `/api/secciones/<id_seccion>` | Consulta una seccion por ID. |
| POST | `/api/secciones` | Crea una seccion. |
| PUT | `/api/secciones/<id_seccion>` | Actualiza una seccion. |
| PATCH | `/api/secciones/<id_seccion>/estado` | Activa o desactiva una seccion. |

Validaciones implementadas:

- Grado obligatorio.
- Seccion obligatoria con valor `A`, `B`, `C` o `D` desde frontend/API.
- Estado solo `activo` o `inactivo`.
- El grado asociado debe existir.
- No permite duplicar una seccion dentro del mismo grado institucional.
- No existe eliminacion fisica publica; se usa activacion/desactivacion.

### 5.3 Endpoints del juego

Prefijo:

```text
/api/juego
```

Endpoints:

| Metodo | Ruta | Funcion |
|---|---|---|
| GET | `/api/juego/contexto` | Devuelve modalidad y temas permitidos para juego sin exponer grado ni dificultad. |
| POST | `/api/juego/partidas` | Inicia una partida nueva. |
| GET | `/api/juego/partidas/<id_partida>` | Consulta el estado de una partida. |
| POST | `/api/juego/partidas/<id_partida>/correcto` | Registra acierto y avanza una casilla. |
| POST | `/api/juego/partidas/<id_partida>/error` | Registra error sin avanzar. |
| POST | `/api/juego/partidas/<id_partida>/salir` | Marca partida como abandonada. |

Reglas implementadas:

- El personaje y el mapa se validan contra el inventario del estudiante.
- Los personajes starter son `masculino` y `femenino`; los mapas base son `bosque`, `mapa_2` y `mapa_3`.
- Casilla final: `10`.
- El frontend no envia `id_grado` como autoridad; el backend resuelve grado por PIN/asignacion/perfil.
- El estudiante no selecciona dificultad; el backend usa progreso por tema y agente adaptativo.
- Desde actividades, la asignacion resuelve grado y tema. En juego libre solo se selecciona tema permitido.
- No permite movimientos si la partida ya esta completada o abandonada.
- Al llegar a casilla 10, la partida queda en estado `completada`.

## 6. Frontend React

El frontend esta en:

```text
frontend
```

Tecnologias:

- React 18.
- Vite.
- Axios.
- CSS propio en `src/styles.css`.

### 6.1 Rutas visuales

Archivo:

```text
frontend/src/main.jsx
```

No se usa React Router. La pantalla se selecciona leyendo `window.location.pathname`.

Rutas actuales:

| Ruta | Pantalla |
|---|---|
| `/` | Login si no hay sesion; redireccion por rol si hay sesion |
| `/login` | Login si no hay sesion; redireccion por rol si hay sesion |
| `/registro` | Registro |
| `/recuperar-password` | Recuperacion de contrasena |
| `/onboarding` | Onboarding para usuario autenticado pendiente |
| `/panel-estudiante` | Panel estudiante |
| `/actividades` | Actividades estudiante |
| `/actualizar-grado` | Cambio de grado por nuevo PIN para estudiante institucional |
| `/secciones` | Secciones para docente |
| `/grados` | Grados para docente |
| `/asignaciones` | Asignaciones para docente |
| `/reportes` | Panel/reportes docente |
| `/admin` | Panel administrador |
| `/admin/secciones` | Secciones para administrador |
| `/admin/grados` | Grados para administrador |
| `/admin/asignaciones` | Asignaciones para administrador |
| `/admin/reportes` | Reportes para administrador |
| `/admin/plantillas` | Plantillas para administrador |
| `/plantillas` | Alias legacy que redirige a `/admin/plantillas` |
| `/juego` | Juego para estudiante autenticado |

Reglas de ruteo:

- Una ruta privada sin sesion redirige a `/login`.
- Un usuario con onboarding pendiente redirige a `/onboarding`.
- Un estudiante autenticado no puede entrar a rutas de docente/admin.
- Un estudiante de cuenta propia no ve `Actividades` ni `Actualizar grado`; si intenta entrar a actividades por URL se redirige al panel y el backend devuelve 403.
- Un docente autenticado no puede entrar a rutas `/admin/*`.
- Una ruta desconocida ya no muestra Secciones como fallback.
- La sesion se verifica una vez al iniciar React; cambiar de modulo no ejecuta logout.
- Errores `403`, `404`, `429` o `500` de modulos no limpian credenciales.
- Un `401` intenta renovar sesion con refresh token; solo el fallo definitivo de refresh limpia credenciales.

### 6.2 Layout pixel-art

Archivo:

```text
frontend/src/components/layout/PixelAdminLayout.jsx
```

Incluye:

- Sidebar pixel-art.
- Logo principal de Mision Matematica.
- Navegacion filtrada por rol.
- Boton de menu para movil.
- Overlay para cerrar sidebar movil.
- Cierre del menu con tecla `Escape`.
- Sin sesion, el sidebar no se muestra en pantallas publicas y no expone rutas internas.

Se eliminaron elementos decorativos que no eran funcionales:

- Paisaje superior con castillo.
- Isla/arbol decorativo inferior del sidebar.
- Bloque superior de administrador con avatar, nombre y correo.

La interfaz conserva la identidad pixel-art funcional sin dejar espacios vacios innecesarios.

### 6.3 Servicios HTTP

Archivo base:

```text
frontend/src/services/apiClient.js
```

Define el cliente Axios con:

```text
VITE_API_URL
```

Si no existe `VITE_API_URL`, usa:

```text
http://127.0.0.1:5000/api
```

Servicios creados:

- `gradosService.js`
- `seccionesService.js`
- `juegoService.js`

Cada servicio convierte errores de Axios en mensajes legibles para la interfaz.

## 7. Modulo de grados

Pantalla:

```text
frontend/src/pages/GradosPage.jsx
```

Componentes:

```text
frontend/src/components/grados/GradoForm.jsx
frontend/src/components/grados/GradosTable.jsx
frontend/src/components/grados/ConfirmDeleteGradoModal.jsx
```

Funcionalidad implementada:

- Carga inicial de grados desde MySQL.
- Creacion de grado.
- Edicion de grado.
- Cambio de estado `activo` / `inactivo`.
- Eliminacion con modal de confirmacion.
- Mensajes de exito/error visibles.
- Errores por campo enviados por backend.
- Tabla con conteo de secciones relacionadas.

Campos manejados:

- Codigo del grado.
- Nombre del grado.
- Descripcion.
- Orden de visualizacion.
- Estado.

## 8. Modulo de secciones

Pantalla:

```text
frontend/src/pages/SeccionesPage.jsx
```

Componentes:

```text
frontend/src/components/secciones/SeccionForm.jsx
frontend/src/components/secciones/SeccionesTable.jsx
```

Funcionalidad implementada:

- Carga inicial de secciones.
- Carga de grados activos para el selector.
- Creacion de seccion.
- Edicion de seccion.
- Cambio de estado `activo` / `inactivo`.
- Mensajes visibles sin `alert()` ni `confirm()`.

Campos manejados:

- Grado.
- Seccion `A`, `B`, `C` o `D`.
- Descripcion.
- Estado.

## 9. Modulo de juego

Pantalla:

```text
frontend/src/pages/JuegoPage.jsx
```

Componentes:

```text
frontend/src/components/juego/GameBoard.jsx
frontend/src/components/juego/CharacterSprite.jsx
frontend/src/components/juego/QuestionPanel.jsx
frontend/src/components/juego/MultipleChoiceQuestion.jsx
frontend/src/components/juego/NumericQuestion.jsx
frontend/src/components/juego/LivesIndicator.jsx
frontend/src/components/juego/ExitGameModal.jsx
frontend/src/components/juego/GameFinishedModal.jsx
```

Funcionalidad implementada:

- Pantalla inicial para seleccionar grado y tema.
- Creacion de partida adaptativa en backend.
- Escenario 2D fullscreen con un mapa desbloqueado por el estudiante.
- Preguntas reales de seleccion multiple o respuesta numerica.
- Avance automatico al responder correctamente.
- Error visual y perdida de vida al responder incorrectamente.
- HUD de juego con 5 corazones, pregunta, respuestas y boton `Salir`.
- Boton `Salir` con modal de confirmacion.
- Modal final cuando se llega a la casilla 10.
- Modal de perdida de vidas con opcion de reintentar o volver a actividades.

Durante la partida no se muestran datos tecnicos al estudiante:

- correctas acumuladas;
- errores acumulados;
- precision;
- dificultad;
- nivel adaptativo;
- decisiones del agente;
- IDs o datos de asignacion.

Estos valores siguen existiendo internamente en backend, agente, historial y reportes.

### 9.0.1 Game Fullscreen Mode

Al iniciar una partida, `JuegoPage.jsx` solicita fullscreen usando el contenedor raiz del juego. El flujo es:

```text
confirmar tema
↓
mostrar "Preparando aventura..."
↓
requestFullscreen() sobre game-fullscreen-container
↓
POST /api/juego/partidas
↓
cargar mapa, pregunta y personaje resueltos por backend
```

Si falla la creacion de partida, el frontend ejecuta `exitFullscreen()`, vuelve al formulario de preparacion y muestra un error controlado.

El modo fullscreen oculta visualmente sidebar, header, navegacion, paneles externos y margenes del sistema. Dentro del juego solo quedan visibles:

- mapa;
- personaje;
- recorrido/casillas;
- 5 vidas;
- pregunta;
- respuestas;
- boton `Salir`;
- modales propios del juego.

El mapa y el personaje se renderizan dentro de un stage logico con la misma relacion de aspecto del mapa. El stage escala uniformemente para que `mapasConfig`, `feetAnchor`, `posicionBase`, `offsetAnimacion` y `snapACasilla()` sigan alineados.

### 9.0.2 HUD, vidas y respuestas

El HUD se organiza asi:

- Superior izquierda: etiqueta `VIDAS` y cinco corazones.
- Superior centro: pregunta actual.
- Inferior centro/izquierda: opciones o respuesta numerica.
- Inferior derecha: boton `Salir`.

Las vidas usan assets propios:

```text
frontend/src/assets/juego/ui/corazon_vida.png
frontend/src/assets/juego/ui/corazon_vida_perdida.png
```

Siempre se muestran cinco posiciones. Si quedan 3 vidas, el resultado visual es:

```text
rojo rojo rojo gris gris
```

La perdida ocurre de derecha a izquierda porque `LivesIndicator.jsx` marca como activos los indices menores que `vidas_restantes`.

Las respuestas de seleccion multiple usan botones grandes para mouse y touch. La respuesta numerica usa `inputMode="numeric"` y boton `Responder`.

### 9.0.3 Fullscreen, salida y orientacion

Al salir definitivamente del juego se restaura el layout normal:

- `exitFullscreen()`;
- `screen.orientation.unlock()` si existe;
- `document.body.style.overflow` vuelve a su valor anterior;
- se eliminan listeners de `fullscreenchange`, `orientationchange` y `resize`.

Si el estudiante presiona `Esc` y pierde fullscreen durante la partida, el juego no se completa ni se abandona automaticamente. Se muestra un overlay con:

```text
Has salido de pantalla completa.
[Volver a pantalla completa]
[Salir de la actividad]
```

En telefono/tablet el frontend intenta `screen.orientation.lock("landscape-primary")` y luego `landscape` como fallback. Si el navegador no lo permite o el dispositivo queda en vertical, se muestra:

```text
Gira tu dispositivo
Para jugar Mision Matematica coloca tu dispositivo horizontalmente.
```

Al rotar de vertical a horizontal no se reinicia la partida, no se genera otra pregunta y no cambia el mapa.

### 9.1 Personajes

Archivo:

```text
frontend/src/config/personajesConfig.js
```

Personajes configurados:

- `masculino`
- `femenino`

Cada personaje incluye:

- Imagen de seleccion.
- Frame idle.
- Frames de movimiento correcto.
- Frames de movimiento error.
- `feetAnchor`.
- `spriteBox`.

Se agrego normalizacion de frames para permitir ajustes por frame sin modificar coordenadas del mapa.

### 9.2 Mapa y casillas

Archivo:

```text
frontend/src/config/mapasConfig.js
```

Mapa actual:

```text
bosque
```

Las casillas 0 a 10 estan configuradas en porcentaje relativo al mapa.

Ejemplo:

```js
casillas: {
  0: { x: 4.4, y: 58.4 },
  1: { x: 7.5, y: 57.8 },
  ...
  10: { x: 92.45, y: 57.8 }
}
```

La funcion central para obtener coordenadas es:

```text
obtenerPosicionCasilla(mapaId, numeroCasilla)
```

Tambien existe:

```text
DEBUG_POSITIONS = false
```

Si se activa temporalmente, permite mostrar puntos de depuracion sobre cada casilla para calibrar posiciones. Debe quedar en `false` en uso normal.

### 9.3 Correccion del posicionamiento del personaje

Se corrigio el problema donde el personaje no terminaba bien colocado sobre la casilla.

Antes:

- El sprite PNG se posicionaba directamente con `left` y `top`.
- La referencia visual dependia de la esquina/transparencia del PNG.
- Los frames podian aparentar desplazamiento.
- Las coordenadas anteriores no correspondian al mapa real horizontal.

Ahora:

- `character-position` representa el punto logico del personaje.
- `character-sprite-box` mantiene un contenedor fijo.
- `character-sprite` solo cambia el frame visible.
- `feetAnchor` define el punto central de los pies.
- `posicionBase` representa la coordenada oficial de la casilla.
- `offsetAnimacion` representa un desplazamiento temporal durante salto/error.
- `snapACasilla()` fuerza la posicion exacta al terminar cualquier animacion.

Flujo correcto:

```text
casilla_actual
↓
mapasConfig
↓
obtenerPosicionCasilla()
↓
posicionBase
↓
offsetAnimacion temporal
↓
snapACasilla()
```

Regla importante:

```text
Al terminar cualquier animacion:
offsetAnimacion = { x: 0, y: 0 }
posicionBase = coordenada exacta de casilla_actual
```

## 10. Estilos y responsive

Archivo:

```text
frontend/src/styles.css
```

Se implemento:

- Estilo pixel-art general.
- Sidebar responsive.
- Layout adaptable para desktop, tablet y movil.
- Formularios y tablas con apariencia pixel-art.
- Modales personalizados.
- Alertas visuales.
- Estados vacios.
- Tablero del juego responsive.
- Contenedor fijo para sprites del personaje.
- Modo fullscreen del juego con stage proporcional al mapa.
- HUD de partida con corazones PNG, pregunta y respuestas tactiles.
- Overlay de orientacion horizontal para telefono/tablet.
- Restauracion de fullscreen, orientacion y scroll al salir o finalizar.

Se corrigieron problemas previos:

- Pantalla en blanco por errores de importacion React.
- Bloqueo CORS entre React y Flask.
- Espacios vacios por elementos decorativos eliminados.
- Posicionamiento incorrecto del personaje sobre el mapa.
- Evitar scroll horizontal en resoluciones pequenas.

## 11. Archivos principales modificados o creados

Backend:

```text
backend/app.py
backend/config.py
backend/db.py
backend/models/grado.py
backend/models/seccion.py
backend/models/partida_juego.py
backend/routes/grados_routes.py
backend/routes/secciones_routes.py
backend/routes/juego_routes.py
```

Base de datos:

```text
database/init_database.sql
database/create_grados.sql
database/create_secciones.sql
database/create_partidas_juego.sql
```

Frontend:

```text
frontend/src/main.jsx
frontend/src/styles.css
frontend/src/services/apiClient.js
frontend/src/services/gradosService.js
frontend/src/services/seccionesService.js
frontend/src/services/juegoService.js
frontend/src/config/mapasConfig.js
frontend/src/config/personajesConfig.js
frontend/src/components/layout/PixelAdminLayout.jsx
frontend/src/pages/SeccionesPage.jsx
frontend/src/pages/GradosPage.jsx
frontend/src/pages/JuegoPage.jsx
frontend/src/components/secciones/*
frontend/src/components/grados/*
frontend/src/components/juego/*
frontend/src/components/ui/*
```

## 12. Como ejecutar el sistema

### 12.1 Requisitos

- XAMPP o MySQL activo.
- Node.js y npm.
- Python.
- Entorno virtual de Python recomendado.

### 12.2 Crear base de datos

En MySQL/phpMyAdmin ejecutar:

```sql
SOURCE C:/dev/tesis 2/database/init_database.sql;
```

Si phpMyAdmin no permite `SOURCE`, abrir el archivo `database/init_database.sql`, copiar su contenido y ejecutarlo en SQL.

### 12.3 Ejecutar backend

Desde la raiz del proyecto:

```powershell
cd "C:\dev\tesis 2"
python -m venv backend\.venv
backend\.venv\Scripts\activate
pip install -r backend\requirements.txt
python backend\app.py
```

El backend queda en:

```text
http://127.0.0.1:5000
```

### 12.4 Ejecutar frontend

En otra terminal:

```powershell
cd "C:\dev\tesis 2\frontend"
npm install
npm run dev
```

El frontend queda normalmente en:

```text
http://127.0.0.1:5173
```

Si el puerto 5173 esta ocupado, Vite puede abrir 5174. El backend ya permite ambos puertos por CORS.

### 12.5 Rutas para probar

```text
http://127.0.0.1:5173/secciones
http://127.0.0.1:5173/grados
http://127.0.0.1:5173/juego
```

Si Vite usa 5174:

```text
http://127.0.0.1:5174/secciones
http://127.0.0.1:5174/grados
http://127.0.0.1:5174/juego
```

## 13. Verificaciones realizadas

Se ejecuto build del frontend:

```powershell
npm.cmd run build
```

Resultado:

```text
Build exitoso con Vite.
```

Tambien se verifico con navegador automatizado:

- Personaje masculino desde casilla 0 hasta 10.
- Personaje femenino desde casilla 0 hasta 10.
- Errores en casillas intermedias.
- Errores repetidos sin desplazamiento acumulado.
- Responsive en 1920, 1440, 1366, 1024, 768 y 320 px.
- Sin scroll horizontal en las resoluciones probadas.

## 14. Estado actual

El sistema tiene implementado:

- CRUD funcional de grados.
- CRUD funcional de secciones.
- Base de datos MySQL con tablas principales.
- API Flask separada por Blueprints.
- Frontend React pixel-art responsive.
- Integracion Axios con manejo de errores.
- Juego funcional con partida persistida en MySQL.
- Seleccion de personaje masculino/femenino.
- Movimiento correcto/error con sprites.
- Correccion del anclaje del personaje a las casillas.
- Agente adaptativo funcional basado en reglas.
- Preguntas reales por grado, tema y nivel de dificultad.
- Registro inmutable de intentos con `request_id`.
- Registro de decisiones del agente por cada respuesta.

## 15. Agente inteligente adaptativo

Se implemento un agente adaptativo basado en reglas, sin servicios externos de IA y sin machine learning.

### 15.1 Tablas agregadas

- `temas`
- `niveles_dificultad`
- `ejercicios`
- `opciones_ejercicio`
- `intentos_juego`
- `reglas_adaptativas`
- `decisiones_agente`

La tabla `partidas_juego` ahora incluye grado, tema, nivel inicial, nivel actual, ejercicio actual, vidas, preguntas respondidas, motivo de finalizacion y ultima actividad.

### 15.2 Endpoints agregados

```text
GET  /api/temas?grado=<id_grado>
POST /api/juego/partidas
POST /api/juego/partidas/<id_partida>/respuesta
```

El frontend ya no usa botones manuales `Correcto` y `Error`. React envia la respuesta del estudiante, `id_ejercicio`, `request_id` y `tiempo_respuesta_ms`; Flask evalua la respuesta, registra el intento, ejecuta el agente y devuelve la siguiente pregunta.

### 15.3 Reglas adaptativas

- Dos errores consecutivos: reduce dificultad o recomienda refuerzo si ya esta en el nivel minimo.
- Tres aciertos consecutivos exactos: aumenta dificultad si existe un nivel superior.
- Porcentaje menor a 60 con minimo de intentos: reduce o refuerza, respetando cooldown.
- Porcentaje mayor a 80 con minimo de intentos: puede aumentar, respetando cooldown.
- Porcentaje entre 60 y 80: mantiene dificultad.
- Fallback: mantiene dificultad.

El agente no modifica coordenadas ni casillas directamente. La casilla solo avanza con respuesta correcta y no cambia con respuesta incorrecta.

### 15.4 Archivos principales del agente

- `backend/agent/motor_reglas.py`
- `backend/services/juego_adaptativo_service.py`
- `backend/services/ejercicios_service.py`
- `backend/services/temas_service.py`
- `backend/routes/temas_routes.py`
- `backend/tests/test_motor_reglas.py`

### 15.5 Frontend del juego

Se agregaron componentes para el flujo real:

- `QuestionPanel.jsx`
- `MultipleChoiceQuestion.jsx`
- `NumericQuestion.jsx`
- `LivesIndicator.jsx`

`JuegoPage.jsx` permite seleccionar grado, cargar temas, seleccionar personaje, iniciar partida y responder preguntas reales. Durante la partida, la dificultad y las decisiones del agente permanecen internas y no se muestran en el HUD.

### 15.6 SQL

Para instalaciones nuevas:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\init_database.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

Para actualizar una base existente:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\create_agente_adaptativo.sql | & C:\xampp\mysql\bin\mysql.exe -u root tesis_matematica_app
```

### 15.7 Pruebas ejecutadas

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Resultado:

```text
Ran 5 tests in 0.000s
OK
```

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe -B -c "import ast, pathlib; files=[pathlib.Path(p) for p in ['app.py','agent/motor_reglas.py','routes/juego_routes.py','routes/temas_routes.py','services/ejercicios_service.py','services/juego_adaptativo_service.py','services/temas_service.py','tests/test_motor_reglas.py']]; [ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)) for p in files]; print('syntax ok', len(files))"
```

Resultado:

```text
syntax ok 8
```

```powershell
cd "C:\dev\tesis 2\frontend"
npm.cmd run build
```

Resultado: build exitoso con Vite.

Tambien se ejecuto una prueba API minima con Flask `test_client`: listar grados/temas, iniciar partida y registrar una respuesta correcta. Resultado: partida en curso, pregunta de seleccion multiple, respuesta correcta registrada y casilla actualizada a 1.

## 16. Generador procedimental de ejercicios

El agente adaptativo ya no depende solamente del banco estatico `ejercicios`. Ahora decide el nivel y el sistema genera una pregunta nueva desde una plantilla pedagogica publicada.

### 16.1 Diferencia entre plantilla y ejercicio

- Plantilla: molde reutilizable con enunciado, operacion, rangos y reglas. Ejemplo: `Cuanto es {a} x {b}?`.
- Ejercicio generado: pregunta concreta creada para una partida. Ejemplo: `Cuanto es 34 x 8?`.

La respuesta correcta se calcula en backend y no se envia a React antes de responder.

### 16.2 Tablas nuevas

- `plantillas_ejercicios`: guarda moldes por grado, tema y nivel.
- `ejercicios_generados`: guarda cada pregunta generada con plantilla, partida, nivel, parametros, seed y respuesta interna.

Tambien se agregaron:

- `partidas_juego.id_ejercicio_generado_actual`
- `intentos_juego.id_ejercicio_generado`

### 16.3 Operaciones soportadas

El generador soporta inicialmente:

- `suma`
- `resta`
- `multiplicacion`
- `division`

No usa `eval()` ni `exec()`. Cada operacion se ejecuta con funciones Python autorizadas.

### 16.4 Configuracion JSON

Ejemplo de plantilla de multiplicacion:

```json
{
  "operacion": "multiplicacion",
  "variables": {
    "a": { "tipo": "entero", "min": 2, "max": 9 },
    "b": { "tipo": "entero", "min": 2, "max": 9 }
  }
}
```

Para division exacta se genera `a = resultado * divisor`, asi se evita division decimal accidental.

### 16.5 Distractores

Para seleccion multiple se generan 4 opciones:

- 1 correcta.
- 3 distractores plausibles.
- Sin duplicados.
- La correcta siempre queda incluida.

Los distractores se calculan con errores frecuentes como sumar operandos o alterar el resultado por operandos cercanos.

### 16.6 Flujo nuevo

```text
respuesta estudiante
-> validar en backend
-> registrar intento
-> calcular metricas
-> agente decide nivel
-> seleccionar plantilla publicada
-> generar parametros nuevos
-> validar ejercicio
-> guardar en ejercicios_generados
-> enviar siguiente pregunta
```

Si una plantilla publicada compatible falla durante la generacion, el servicio intenta otra plantilla del mismo grado, tema y nivel. Si ninguna plantilla compatible produce un ejercicio valido, el juego cae al banco manual `ejercicios` como fallback seguro.

### 16.7 Archivos nuevos

- `backend/generators/generador_ejercicios.py`
- `backend/generators/generador_numerico.py`
- `backend/generators/generador_opciones.py`
- `backend/generators/validador_ejercicio.py`
- `backend/generators/restricciones_matematicas.py`
- `backend/services/plantillas_service.py`
- `backend/routes/plantillas_routes.py`
- `frontend/src/pages/PlantillasPage.jsx`
- `frontend/src/services/plantillasService.js`
- `backend/tests/test_generador_ejercicios.py`
- `backend/tests/test_plantillas_service.py`
- `database/create_generador_plantillas.sql`

### 16.8 Endpoints nuevos

```text
GET  /api/plantillas
GET  /api/plantillas/niveles
POST /api/plantillas
PUT  /api/plantillas/<id_plantilla>
PATCH /api/plantillas/<id_plantilla>/estado
POST /api/plantillas/<id_plantilla>/probar
```

La pantalla administrativa esta disponible en:

```text
http://127.0.0.1:5173/admin/plantillas
```

Alias legacy temporal:

```text
http://127.0.0.1:5173/plantillas -> /admin/plantillas
```

### 16.9 SQL de actualizacion

```powershell
cd "C:\dev\tesis 2"
Get-Content database\create_generador_plantillas.sql | & C:\xampp\mysql\bin\mysql.exe -u root tesis_matematica_app
```

### 16.10 Pruebas ejecutadas

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Resultado:

```text
Ran 12 tests
OK
```

```powershell
cd "C:\dev\tesis 2\frontend"
npm.cmd run build
```

Resultado: build correcto.

### 16.11 Demostracion real de adaptacion

La demostracion se puede ejecutar con:

```powershell
cd "C:\dev\tesis 2\backend"
.\.venv\Scripts\python.exe tests\demo_adaptacion_generador.py
```

Se ejecuto una partida automatizada con tema `Multiplicacion`:

```text
Pregunta 1: Multiplicacion Facil | facil | Cuanto es 3 x 7? = 21
Pregunta 2: Multiplicacion Facil | facil | Cuanto es 9 x 3? = 27
Pregunta 3: Multiplicacion Facil | facil | Cuanto es 8 x 8? = 64
AGENTE: facil -> intermedio
Pregunta 4: Multiplicacion Intermedio | intermedio | Cuanto es 39 x 3? != 118
Pregunta 5: Multiplicacion Intermedio | intermedio | Cuanto es 21 x 8? != 169
AGENTE: intermedio -> facil
Pregunta 6: Multiplicacion Facil | facil | Cuanto es 9 x 5?
intentos: 5
generados: 6
decisiones: 5
```

Resultado demostrado:

- 3 correctas consecutivas activaron `aumentar`.
- La siguiente pregunta fue realmente intermedia (`a` de dos digitos y `b` de un digito).
- 2 incorrectas consecutivas activaron `reducir`.
- La siguiente pregunta volvio a nivel facil.

## 17. Fase 0 - Auditoria del prompt maestro

Matriz fisica revisada contra codigo, SQL, tests y MySQL local:

| Modulo | Estado | Evidencia | Accion |
| --- | --- | --- | --- |
| Grados | COMPLETADO | CRUD backend/frontend y tabla `grados` | No rehacer |
| Secciones | COMPLETADO | CRUD backend/frontend y tabla `secciones` | No rehacer |
| Juego 2D | COMPLETADO | `JuegoPage.jsx`, sprites M1/F1, mapa bosque, casillas 0-10 | Conservar coordenadas |
| Agente adaptativo | COMPLETADO | `motor_reglas.py`, `decisiones_agente`, tests | No reemplazar |
| Generador por plantillas | COMPLETADO | `generators/*`, `plantillas_ejercicios`, `ejercicios_generados` | No reemplazar |
| Auth/usuarios | COMPLETADO | Login, registro, JWT, refresh revocable, roles y proteccion de rutas | Mantener |
| Grupos/PIN | COMPLETADO | Tablas, API, pantalla docente y acceso de estudiantes por PIN | Mantener |
| Asignaciones | COMPLETADO | Tablas, API, pantalla docente y vista estudiante | Mantener |
| Historial/progreso | COMPLETADO | Panel estudiante, progreso, historial y asignaciones | Mantener |
| Reportes docente/admin | COMPLETADO | UI docente de reportes y panel administrador global | Mantener |
| Auditoria | COMPLETADO | Tabla `bitacora_acciones`, servicio y pestaña admin | Mantener |
| Seguridad | COMPLETADO | JWT, hash password, refresh revocable, rate limit y headers basicos | Mantener |
| Documentacion | PARCIAL | Este archivo actualizado | Faltan manuales separados |

## 18. Fase 1 - Usuarios y autenticacion

Se implemento autenticacion real inicial:

- Tabla `roles`.
- Tabla `usuarios`.
- Tabla `refresh_tokens`.
- Tabla `recuperaciones_contrasena`.
- Tabla `verificaciones_correo`.
- Registro con `generate_password_hash()` de Werkzeug.
- Login con validacion de hash.
- JWT HS256 propio usando libreria estandar.
- Access token con expiracion.
- Refresh token persistido, hasheado y revocable.
- Logout revocando refresh token.
- Refresh con rotacion de token.
- Recuperacion de contrasena con token seguro de un solo uso.
- Verificacion de correo preparada con token seguro.
- Login definitivo con correo electronico y contrasena.

Endpoints:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
GET  /api/auth/me
POST /api/auth/forgot-password
POST /api/auth/reset-password
POST /api/auth/verify-email
```

Frontend agregado:

- `/login`
- `/registro`
- `/recuperar-password`
- `frontend/src/services/authService.js`
- Interceptor Authorization Bearer en `apiClient.js`.
- La pantalla `/login` usa una composicion visual responsive con logo, personajes, decoracion matematica animada y formulario de correo/contrasena.
- Accion `Salir` en el sidebar cuando existe sesion local.

Integracion critica con juego:

- Si una partida se inicia con token Bearer valido, `partidas_juego.id_usuario` se guarda desde el backend.
- React no envia ni decide `id_usuario`.
- Se mantiene compatibilidad con partidas demo anonimas.

SQL:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\create_auth_usuarios.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\init_database.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

Pruebas:

```text
Ran 18 tests
OK

demo_auth_flow.py: registro, me, login, refresh, logout, reset-password y login con nueva password OK
partida autenticada: id_usuario guardado correctamente desde token
```

Correccion posterior del flujo inicial:

- `/` deja de renderizar Secciones por defecto.
- `/` y `/login` muestran Login cuando no existe sesion.
- Login redirige por rol: estudiante a `/juego`, docente a `/mi-institucion`, administrador a `/admin`.
- `/api/auth/me` se usa para recuperar usuario, rol y `onboarding_completado` al refrescar.
- `GET /api/secciones`, `GET /api/grados`, `GET /api/temas` y rutas de plantillas quedan protegidas por backend.
- Se agrego demo `demo_rutas_autenticacion_flow.py` para validar 401, 403 y datos de `/api/auth/me`.

Correccion definitiva de persistencia de sesion:

- Tokens en frontend: `mm_access_token`, `mm_refresh_token` y `mm_usuario` en `localStorage`.
- `frontend/src/services/apiClient.js` centraliza `Authorization: Bearer <access_token>`.
- El interceptor solo actua sobre `401`: intenta `/api/auth/refresh` una vez y reintenta la solicitud original.
- `403`, `404`, `429`, `500`, errores de modulo lazy y errores de datos no ejecutan logout.
- `frontend/src/main.jsx` verifica sesion una vez durante bootstrap con `/api/auth/me`.
- `Cargando modulo...` queda reservado para `React.lazy`/`Suspense`; `Verificando sesion...` queda reservado para bootstrap de auth.
- `/admin/plantillas` es la ruta canonica de Plantillas; `/plantillas` queda como alias legacy.
- El boton `Volver al inicio` de 404 vuelve segun rol: admin a `/admin`, docente a `/mi-institucion`, estudiante a `/juego`.

## 19. Fase 2 - Onboarding y perfiles

Se implemento onboarding inicial por rol:

- Estudiante:
  - modalidad `cuenta_propia` o `grupo_educativo`;
  - grado para cuenta propia;
  - personaje `masculino` o `femenino`.
- Docente:
  - institucion obligatoria seleccionada o creada previamente;
  - grados que atendera;
  - secciones A-D por cada grado seleccionado, con `Única` automatica si no marca ninguna.
- Administrador:
  - puede marcar onboarding completado sin datos adicionales en esta fase.

Tablas creadas:

- `perfiles_estudiante`
- `perfiles_docente`
- `docente_grados`

Endpoints:

```text
GET  /api/onboarding
POST /api/onboarding
GET  /api/instituciones?q=texto
POST /api/instituciones
GET  /api/instituciones/<id_institucion>/secciones-disponibles
```

Contrato docente definitivo:

```json
{
  "id_institucion": 3,
  "grados": [1, 6, 3],
  "secciones_por_grado": {
    "1": ["A", "B"],
    "6": ["C"],
    "3": ["D"]
  }
}
```

El frontend no envia el nombre de institucion como autoridad de relacion. Primero busca o crea la institucion con `/api/instituciones`, recibe `id_institucion` y luego envia onboarding.

`GET /api/instituciones` sin `q` responde 200 con lista limitada de instituciones activas. `GET /api/instituciones?q=texto` busca por `nombre_normalizado`, sin distinguir mayusculas/minusculas ni espacios repetidos.

`POST /api/instituciones` normaliza nombre con `trim`, espacios simples y lowercase para comparacion; si ya existe, la reutiliza. Toda institucion nueva garantiza automaticamente tres filas en `institucion_grados`: Cuarto, Quinto y Sexto.

`POST /api/onboarding` para docente ejecuta una transaccion:

```text
validar rol docente
validar id_institucion activa
validar grados base activos
validar secciones A-D
garantizar grados institucionales
bloquear y validar secciones activas ocupadas por otro docente
crear/actualizar perfil docente
reactivar docente_grados seleccionados
crear/reactivar secciones A-D o Única
crear/reactivar docente_secciones
sincronizar PIN mediante grupo interno legacy
marcar onboarding_completado
commit
```

Si alguna validacion falla se devuelve 400, 404 o 409 segun corresponda y no se marca onboarding. Si ocurre una excepcion SQL se hace rollback. Repetir el mismo onboarding no duplica institucion, grado institucional, seccion, docente_grado, docente_seccion ni PIN activo.

Migracion relacionada:

```text
database/fix_onboarding_docente_institucional.sql
database/actualizar_exclusividad_progresion_estudiante.sql
```

Corrige el indice legacy de `secciones` que impedia tener, por ejemplo, `Cuarto A` en mas de una institucion. El indice real queda basado en `id_institucion_grado`.

La migracion `actualizar_exclusividad_progresion_estudiante.sql` agrega auditoria de conflictos, columnas generadas para exclusividad activa, progreso curricular por tema y tabla de promociones. En la base local se detectaron conflictos activos en `docente_secciones` para `id_seccion` 30 y 31; quedaron registrados en `incidencias_migracion` y bloquean la creacion del indice unico `uk_docente_seccion_activa` hasta que se cierre manualmente una de las relaciones activas.

Pantalla frontend:

```text
http://127.0.0.1:5173/onboarding
```

Archivos principales:

- `backend/services/onboarding_service.py`
- `backend/routes/onboarding_routes.py`
- `database/create_onboarding_perfiles.sql`
- `frontend/src/pages/OnboardingPage.jsx`
- `frontend/src/services/onboardingService.js`

SQL:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\create_onboarding_perfiles.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\init_database.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

Pruebas:

```text
demo_onboarding_flow.py: onboarding estudiante OK, onboarding docente OK
Ran 18 tests
OK
Frontend build correcto
```

Nota: el flujo `grupo_educativo` queda guardado como modalidad del estudiante, pero la validacion de PIN real pertenece a FASE 3.

## 20. Fase 3 - Grupos y PIN legacy

Se implemento la gestion inicial de grupos educativos. En el modelo actual esta capa queda como compatibilidad historica; no existe modulo visible de Grupos y los PIN se exponen desde Secciones o desde Grados cuando corresponde una seccion `Unica`.

- Docente crea grupos propios.
- Administrador puede consultar grupos.
- Grupo pertenece a un grado.
- Grupo puede asociarse a varias secciones opcionales mediante tabla puente.
- Docente puede generar PIN de seis digitos.
- PIN puede ser para grupo completo o para una seccion asociada al grupo.
- PIN se genera con `secrets.randbelow()` y conserva ceros iniciales.
- PIN tiene expiracion.
- PIN puede desactivarse o regenerarse.
- Regenerar invalida el PIN anterior.
- Estudiante autenticado puede validar PIN e ingresar al grupo.
- La relacion estudiante-grupo queda guardada en `estudiantes_grupos`.
- Las asignaciones y reportes actuales ya no dependen de `id_grupo`.

Tablas creadas:

- `grupos`
- `grupo_secciones`
- `pines_acceso`
- `estudiantes_grupos`

Endpoints:

```text
GET  /api/grupos
POST /api/grupos
GET  /api/grupos/<id_grupo>/secciones
PUT  /api/grupos/<id_grupo>/secciones
GET  /api/grupos/<id_grupo>/pines
POST /api/grupos/<id_grupo>/pines
PATCH /api/pines/<id_pin>/estado
POST /api/pines/<id_pin>/regenerar
POST /api/pines/validar
POST /api/pines/ingresar
```

Pantalla frontend historica retirada de navegacion:

```text
http://127.0.0.1:5173/grupos
```

Archivos principales:

- `database/create_grupos_pines.sql`
- `backend/services/grupos_service.py`
- `backend/routes/grupos_routes.py`
- `frontend/src/services/gruposService.js`
- `backend/tests/test_grupos_service.py`
- `backend/tests/demo_grupos_pines_flow.py`

SQL:

```powershell
cd "C:\dev\tesis 2"
Get-Content database\create_grupos_pines.sql | & C:\xampp\mysql\bin\mysql.exe -u root
Get-Content database\init_database.sql | & C:\xampp\mysql\bin\mysql.exe -u root
```

Pruebas:

```text
demo_grupos_pines_flow.py:
crear grupo OK
generar PIN OK
validar PIN OK
ingresar estudiante OK
regenerar PIN OK

Ran 20 tests
OK
Frontend build correcto
```

## 21. Fase 5 - Historial y progreso

Se implemento el panel inicial del estudiante con datos reales del juego:

- Progreso general del estudiante autenticado.
- Progreso por tema.
- Historial reciente de partidas.
- Redireccion de estudiante autenticado hacia `/juego`.
- Navegacion lateral filtrada para estudiante con Panel y Juego.
- Sincronizacion de progreso dentro del flujo transaccional de respuesta del juego.
- Proteccion IDOR: las rutas no reciben `id_usuario`; usan el usuario del token JWT.

Tablas creadas:

- `progreso_estudiante`
- `progreso_tema_estudiante`

Endpoints:

```text
GET /api/estudiante/panel
GET /api/estudiante/progreso
GET /api/estudiante/historial
```

Pantalla frontend:

```text
http://127.0.0.1:5173/panel-estudiante
```

Archivos principales:

- `database/create_progreso_estudiante.sql`
- `backend/services/progreso_service.py`
- `backend/routes/estudiante_routes.py`
- `frontend/src/services/estudianteService.js`
- `frontend/src/pages/PanelEstudiantePage.jsx`
- `backend/tests/test_progreso_service.py`

Metricas:

- Porcentaje de aciertos: `(aciertos / intentos) * 100`; si no hay intentos, devuelve `0`.
- Puntos: equivalen al total de aciertos registrados, sin bonificaciones inventadas.
- Tiempo total: suma de `tiempo_respuesta_ms` de los intentos.
- Cambios de dificultad: decisiones del agente donde `nivel_anterior <> nivel_nuevo`.

## 22. Fase 6 - Asignaciones

Se implemento el modulo de asignaciones docentes integrado al juego:

- Creacion y edicion de asignaciones por grado institucional y seccion.
- Seccion obligatoria dentro del grado institucional seleccionado.
- Seleccion de temas asociados a la actividad.
- Configuracion de nivel inicial, cantidad de preguntas, fechas y obligatoriedad.
- Estados `borrador`, `activa`, `pausada`, `finalizada` y `cancelada`.
- Actividades visibles para estudiante segun `id_institucion_grado`, `id_seccion`, estado y vigencia.
- Inicio de partida desde `/actividades` hacia `/juego`.
- Registro de `id_asignacion` en `partidas_juego`.
- Validacion backend para evitar que un estudiante inicie asignaciones ajenas o temas fuera de la asignacion.

Tablas creadas:

- `asignaciones`
- `asignacion_temas`
- `asignacion_ejercicios`

Endpoints:

```text
GET   /api/asignaciones/contexto
GET   /api/asignaciones
POST  /api/asignaciones
PUT   /api/asignaciones/<id_asignacion>
PATCH /api/asignaciones/<id_asignacion>/estado
GET   /api/estudiante/asignaciones
```

Pantallas frontend:

```text
http://127.0.0.1:5173/asignaciones
http://127.0.0.1:5173/actividades
```

Archivos principales:

- `database/create_asignaciones.sql`
- `backend/services/asignaciones_service.py`
- `backend/routes/asignaciones_routes.py`
- `backend/routes/estudiante_routes.py`
- `backend/services/juego_adaptativo_service.py`
- `frontend/src/services/asignacionesService.js`
- `frontend/src/pages/AsignacionesPage.jsx`
- `frontend/src/pages/ActividadesPage.jsx`
- `backend/tests/test_asignaciones_service.py`
- `backend/tests/demo_asignaciones_flow.py`

Pruebas:

```text
test_asignaciones_service.py:
contexto docente institucional: OK
crear asignacion: OK
actividad visible: OK
partida asignada: OK
runtime sin DELETE de relaciones: OK
frontend sin envio de id_grupo: OK

Suite actual:
Ran 69 tests
OK
Frontend build correcto
```

## 23. Fase 7 - Panel docente y reportes agente

Se implemento una pantalla docente para consultar progreso y decisiones del agente:

- Resumen docente con grados institucionales, estudiantes, asignaciones, partidas e intentos.
- Listado de estudiantes vinculados a secciones del docente.
- Progreso general por estudiante.
- Asignaciones pendientes e iniciadas por estudiante.
- Reporte agregado del agente por accion adaptativa.
- Reglas aplicadas por el agente.
- Alertas de bajo rendimiento, errores consecutivos y refuerzo recurrente.
- Cronologia de decisiones con pregunta, resultado, nivel anterior, accion, nivel nuevo, regla y motivo.
- Filtros por grado institucional, seccion, estudiante, tema, asignacion y rango de fechas.
- Proteccion backend: docente solo consulta estudiantes visibles de sus secciones y grados institucionales; administrador puede consultar globalmente.

Endpoints:

```text
GET /api/docente/panel
GET /api/docente/estudiantes
GET /api/docente/reportes/agente
GET /api/docente/reportes/agente/decisiones
```

Pantalla frontend:

```text
http://127.0.0.1:5173/reportes
```

Archivos principales:

- `backend/services/reportes_docente_service.py`
- `backend/routes/docente_routes.py`
- `backend/app.py`
- `frontend/src/services/reportesDocenteService.js`
- `frontend/src/pages/ReportesDocentePage.jsx`
- `frontend/src/components/layout/PixelAdminLayout.jsx`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/tests/test_reportes_docente_service.py`
- `backend/tests/demo_reportes_docente_flow.py`

Pruebas:

```text
demo_reportes_docente_flow.py:
panel docente: OK
estudiantes docente: OK
reporte agente: OK
decisiones agente: OK

Ran 33 tests
OK
Frontend build correcto
```

## 24. Fase 8 - Panel administrador

Se implemento un panel administrador central para completar la gestion interna del sistema:

- Panel global con conteos de usuarios, partidas, ejercicios generados, plantillas, temas, decisiones y reglas activas.
- Usuarios con filtros por rol, estado y busqueda por nombre/correo.
- Cambio controlado de estado de usuario: activo, inactivo o bloqueado.
- Cambio controlado de rol: administrador, docente o estudiante.
- Prevencion de cambios peligrosos sobre el propio administrador autenticado.
- Temas con creacion, edicion, filtros por grado/estado y activacion/desactivacion.
- Ejercicios manuales con creacion, edicion, filtros por tema/nivel/estado y activacion/desactivacion.
- Opciones de respuesta para ejercicios de seleccion_multiple.
- Reglas adaptativas con edicion de descripcion, accion, prioridad, estado y parametros JSON.
- Reportes administrativos institucionales con filtros por modalidad, institucion, grado base, grado institucional, seccion, docente, estudiante, tema, asignacion y periodo.
- Mejora de plantillas con filtros frontend por grado, tema y estado.

Endpoints:

```text
GET /api/admin/panel
GET /api/admin/usuarios
PATCH /api/admin/usuarios/<id_usuario>/estado
PATCH /api/admin/usuarios/<id_usuario>/rol
GET /api/admin/temas
POST /api/admin/temas
PUT /api/admin/temas/<id_tema>
PATCH /api/admin/temas/<id_tema>/estado
GET /api/admin/ejercicios
POST /api/admin/ejercicios
PUT /api/admin/ejercicios/<id_ejercicio>
PATCH /api/admin/ejercicios/<id_ejercicio>/estado
GET /api/admin/reglas
PUT /api/admin/reglas/<id_regla>
PATCH /api/admin/reglas/<id_regla>/estado
GET /api/admin/reportes/filtros
GET /api/admin/reportes/institucional
```

Pantalla frontend:

```text
http://127.0.0.1:5173/admin
```

Archivos principales:

- `backend/services/admin_service.py`
- `backend/routes/admin_routes.py`
- `backend/app.py`
- `frontend/src/services/adminService.js`
- `frontend/src/pages/AdminPage.jsx`
- `frontend/src/pages/PlantillasPage.jsx`
- `frontend/src/components/layout/PixelAdminLayout.jsx`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/tests/test_admin_service.py`
- `backend/tests/demo_admin_flow.py`

Base de datos:

- El panel usa tablas existentes: `usuarios`, `roles`, `refresh_tokens`, `grados`, `temas`, `niveles_dificultad`, `ejercicios`, `opciones_ejercicio`, `reglas_adaptativas`, `plantillas_ejercicios`, `partidas_juego`, `ejercicios_generados` y `decisiones_agente`.
- Los reportes institucionales cruzan `instituciones`, `institucion_grados`, `secciones`, `perfiles_docente`, `perfiles_estudiante`, `asignaciones`, `asignacion_temas`, `partidas_juego`, `intentos_juego` y `decisiones_agente`.
- La migracion de cierre usa `migration_report` y `migration_issues` para dejar evidencia de datos migrados o ambiguos.

Pruebas:

```text
demo_admin_flow.py:
panel admin: OK
usuarios admin: OK
estado usuario: OK
rol usuario: OK
crear tema: OK
listar temas: OK
crear ejercicio: OK
listar ejercicios: OK
listar reglas: OK
actualizar regla: OK
```

## 25. Fase 9 - Auditoria y seguridad

Se implemento una capa transversal de seguridad y trazabilidad para la API:

- Tabla persistente `bitacora_acciones`.
- Registro automatico de acciones sensibles con metodo `POST`, `PUT`, `PATCH` y `DELETE`.
- Registro de usuario autenticado, accion, entidad, ruta, codigo HTTP, resultado, IP, user-agent y detalles no sensibles.
- Omision explicita de campos sensibles como `password`, `token`, `access_token`, `refresh_token` y `password_hash`.
- Endpoint administrativo para consultar auditoria reciente.
- Pestaña `Auditoria` dentro de `/admin`.
- Rate limit en memoria por IP y endpoint.
- Limite especifico para rutas de autenticacion.
- Headers basicos de seguridad para respuestas API.

Base de datos:

```text
database/create_auditoria_seguridad.sql
```

Tabla nueva:

```text
bitacora_acciones
```

Variables de entorno agregadas:

```text
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=10
RATE_LIMIT_API_PER_MINUTE=240
```

Endpoint nuevo:

```text
GET /api/admin/auditoria
```

Archivos principales:

- `backend/services/security_service.py`
- `backend/services/auditoria_service.py`
- `backend/routes/admin_routes.py`
- `backend/app.py`
- `backend/config.py`
- `database/init_database.sql`
- `database/create_auditoria_seguridad.sql`
- `frontend/src/services/adminService.js`
- `frontend/src/pages/AdminPage.jsx`
- `backend/tests/test_security_service.py`
- `backend/tests/demo_auditoria_seguridad_flow.py`

Pruebas:

```text
demo_auditoria_seguridad_flow.py:
accion auditada: OK
consulta auditoria: OK
rate limit auth: OK

Suite actual:
Ran 69 tests
OK
Frontend build correcto
```

## 26. Fase 10 - Optimizacion y QA

Se realizo una fase de optimizacion y control de calidad sobre frontend y ejecucion local:

- Se reemplazaron imports directos de paginas en `frontend/src/main.jsx` por `React.lazy`.
- Se agrego `Suspense` con `PixelLoader` como fallback de carga.
- Se separo el bundle inicial de los modulos de paginas.
- El juego `/juego` queda cargado bajo demanda en su propio chunk.
- Se agrego listado central `RUTAS_PRINCIPALES` para mantener visible el mapa de rutas principales.
- Se agrego `decoding="async"` a imagenes principales.
- Se agrego `loading="lazy"` en imagenes no criticas.
- Se corrigieron atributos `autoComplete` en login y registro.
- Se ajusto el sidebar para que, sin sesion, no muestre rutas internas no correspondientes.

Resultado de optimizacion:

```text
Antes:
index JS aproximado: 295.95 kB

Despues:
index JS aproximado: 204.97 kB
paginas separadas en chunks:
- LoginPage
- RegisterPage
- OnboardingPage
- SeccionesPage
- GradosPage
- AsignacionesPage
- ReportesDocentePage
- AdminPage
- PlantillasPage
- JuegoPage
```

QA con Playwright:

```text
/login:
- carga correcta
- consola sin errores
- warning de autocomplete corregido
- viewport 320 px sin overflow horizontal

/registro:
- carga correcta
- consola sin errores

/secciones con backend activo:
- carga correcta
- consola sin errores
- viewport 320 px sin overflow horizontal
- sidebar sin sesion muestra solo acceso de ingreso
```

Archivos principales:

- `frontend/src/main.jsx`
- `frontend/src/components/layout/PixelAdminLayout.jsx`
- `frontend/src/components/ui/PixelEmptyState.jsx`
- `frontend/src/components/juego/CharacterSelector.jsx`
- `frontend/src/components/juego/CharacterSprite.jsx`
- `frontend/src/components/juego/GameBoard.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/RegisterPage.jsx`
- `frontend/src/pages/OnboardingPage.jsx`
- `README.md`
- `DOCUMENTACION_SISTEMA.md`

Pruebas:

```text
Ran 69 tests
OK
Frontend build correcto
Playwright QA correcto en login, registro y secciones
```

## 27. Cierre del modelo academico

Se cerro el modelo academico institucional sin depender funcionalmente de grupos para asignaciones, reportes ni validacion de partidas institucionales:

- Las asignaciones docentes se crean por `id_institucion_grado` y `id_seccion`.
- `id_grupo` queda como columna legacy nullable por compatibilidad historica.
- El frontend de asignaciones y reportes no envia ni filtra por `id_grupo`.
- Los reportes administrativos usan filtros institucionales y periodo.
- El estudiante institucional inicia juego segun `perfiles_estudiante.id_institucion_grado` y `perfiles_estudiante.id_seccion`.
- Las relaciones de asignaciones, docente-secciones y opciones se inactivan con `estado` y `fecha_fin`.
- No quedan `DELETE FROM` ni `ON DELETE CASCADE` en runtime backend ni scripts principales.

Script de cierre:

```text
database/actualizar_cierre_modelo_academico.sql
```

Tablas de evidencia:

```text
migration_report
migration_issues
```

Resultado aplicado en la base `tesis_matematica_app`:

```text
secciones_total: 5
secciones_migradas: 3
secciones_activas_sin_grado_institucional: 0
asignaciones_total: 1
asignaciones_migradas: 1
asignaciones_activas_sin_contexto: 0
```

Incidencia historica pendiente:

```text
seccion id 3: nombre historico invalido "A, B"; estado inactivo.
```

Archivos principales actualizados:

- `backend/services/asignaciones_service.py`
- `backend/routes/asignaciones_routes.py`
- `backend/services/reportes_docente_service.py`
- `backend/services/juego_adaptativo_service.py`
- `backend/services/admin_service.py`
- `backend/routes/admin_routes.py`
- `frontend/src/pages/AsignacionesPage.jsx`
- `frontend/src/pages/ReportesDocentePage.jsx`
- `frontend/src/pages/AdminPage.jsx`
- `frontend/src/services/asignacionesService.js`
- `frontend/src/services/adminService.js`
- `database/init_database.sql`
- `database/create_asignaciones.sql`
- `database/create_grupos_pines.sql`
- `database/create_auth_usuarios.sql`
- `database/create_onboarding_perfiles.sql`
- `database/create_progreso_estudiante.sql`
- `database/create_agente_adaptativo.sql`
- `database/actualizar_modelo_institucional.sql`
- `database/actualizar_cierre_modelo_academico.sql`

Pruebas de cierre:

```text
Backend unittest:
Ran 69 tests
OK

Frontend:
npm.cmd run build
OK
```

## 28. Pendientes recomendados

Pendientes tecnicos razonables para una siguiente fase:

- Agregar React Router si el sistema crece mas en rutas.

## 29. Correccion de inicio de partida

Se corrigio el error 500 al iniciar una partida desde `/juego?asignacion=6&grado=1&tema=7`.

Endpoint documentado:

```text
POST /api/juego/partidas
Authorization: Bearer <access_token>

Payload:
{
  "personaje": "femenino",
  "mapa": "mapa_resuelto_por_inventario",
  "id_asignacion": 6,
  "id_grado": 1,
  "id_tema": 7,
  "request_id": "<uuid>"
}
```

Reglas del flujo:

- `id_usuario` se toma del JWT/sesion autenticada; no se acepta como autoridad desde React.
- Si hay `id_asignacion`, la asignacion valida el contexto institucional del estudiante y el tema permitido.
- El grado recibido representa `grados.id_grado`, es decir grado base.
- En estudiantes institucionales, `perfiles_estudiante.id_institucion_grado` se resuelve contra `institucion_grados.id_grado_base`.
- Las plantillas se buscan por grado base y tema, no por institucion ni seccion.
- La partida y el primer ejercicio se crean en la misma transaccion.
- Si no existen plantillas ni ejercicios publicados, se hace rollback y se responde `409`.

## 30. Catalogo matematico adaptativo por grado

Se actualizo el catalogo matematico global para separar tres conceptos:

- `grado_registrado`: grado oficial del estudiante; define que temas ve en Juego.
- `nivel_curricular_adaptativo`: grado interno usado por el generador para el mismo tema cuando existe dominio sostenido.
- `dificultad`: nivel fino por tema (`facil`, `intermedio`, `dificil`) decidido por el agente.

El estudiante no selecciona grado, dificultad ni nivel curricular desde el frontend. React consulta `/api/juego/contexto` para iniciar partidas y tambien existe `GET /api/estudiante/temas` como endpoint directo de catalogo permitido. Ambos resuelven el grado desde `perfiles_estudiante`.

Matriz vigente:

| Tema | Cuarto | Quinto | Sexto |
| --- | --- | --- | --- |
| Suma | Si | Si | Si |
| Resta | Si | Si | Si |
| Multiplicacion | Si | Si | Si |
| Division | Si | Si | Si |
| Potencias | Si | Si | Si |
| Raiz cuadrada | Si | Si | Si |
| Operaciones combinadas | Si | Si | Si |
| Suma de fracciones | Si | Si | Si |
| Resta de fracciones | Si | Si | Si |
| Multiplicacion de fracciones | Si | Si | Si |
| Division de fracciones | Si | Si | Si |
| Suma de decimales | Si | Si | Si |
| Resta de decimales | Si | Si | Si |
| Multiplicacion de decimales | Si | Si | Si |
| Division de decimales | Si | Si | Si |
| Porcentajes | Si | Si | Si |
| Regla de tres directa | No | Si | Si |
| Regla de tres inversa | No | Si | Si |
| Operaciones combinadas de fracciones | No | Si | Si |
| Conversiones de fracciones | No | Si | Si |
| Geometria | No | No | Si |

La migracion `database/actualizar_catalogo_matematico_adaptativo.sql` es idempotente. Inserta los temas faltantes, desactiva `Operaciones basicas` como legacy sin borrarlo, agrega indices y amplia `promociones_curriculares_tema` con `id_nivel_anterior`, `id_nivel_nuevo` y `tipo_movimiento`.

Plantillas creadas:

- Una plantilla procedimental por combinacion activa de grado, tema y dificultad.
- Cuarto: 16 temas x 3 niveles = 48 plantillas.
- Quinto: 20 temas x 3 niveles = 60 plantillas.
- Sexto: 21 temas x 3 niveles = 63 plantillas.
- Total local verificado: 171 plantillas publicadas de catalogo.

Generadores y validadores:

- `backend/generators/generador_numerico.py` ahora cubre enteros, potencias, raices, operaciones combinadas, fracciones, decimales, porcentajes, regla de tres, conversiones y geometria.
- Fracciones usan `fractions.Fraction`; no usan float y se simplifican para la respuesta.
- Decimales usan `decimal.Decimal`; no dependen de aritmetica binaria.
- Operaciones combinadas se construyen como estructuras controladas; no se usa `eval()` ni `exec()`.
- Regla de tres guarda `tipo_proporcion` como `directa` o `inversa` y calcula desde esa estructura.
- Geometria guarda `figura` y `calculo`; circulo usa `pi = 3.14` en la configuracion.
- `backend/generators/generador_opciones.py` genera distractores para enteros, decimales, fracciones y mixtos evitando equivalentes duplicados.
- `backend/generators/validador_ejercicio.py` valida operaciones permitidas, division exacta, denominadores, tipo de proporcionalidad y figura/calculo geometrico.

Progresion adaptativa:

- La promocion curricular por tema requiere evidencia sostenida: minimo 20 intentos, 85% de aciertos y estado `dominado`.
- La dificultad puede subir o bajar por reglas existentes del agente sin cambiar grado registrado.
- El descenso curricular solo se considera para cuenta propia con dificultad sostenida: minimo 15 intentos, 45% o menos de aciertos y 8 errores consecutivos.
- El descenso no baja por debajo del grado registrado.
- Los movimientos curriculares se registran en `promociones_curriculares_tema` con grado anterior/nuevo, dificultad anterior/nueva, tipo de movimiento, motivo, metricas y fecha.
- La lista visible de temas nunca usa el nivel curricular adaptativo; usa solo el grado registrado.

Pruebas ejecutadas en esta actualizacion:

```powershell
Get-Content database\actualizar_catalogo_matematico_adaptativo.sql | & "C:\xampp\mysql\bin\mysql.exe" -u root
& "C:\xampp\mysql\bin\mysql.exe" -u root -D tesis_matematica_app -e "SELECT g.codigo_grado, COUNT(*) AS temas_activos FROM temas t INNER JOIN grados g ON g.id_grado=t.id_grado WHERE t.estado='activo' AND g.codigo_grado IN ('4P','5P','6P') GROUP BY g.codigo_grado ORDER BY g.codigo_grado;"
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe tests\demo_generacion_catalogo_masiva.py
cd ..\\frontend
npm.cmd run build
```

Resultados verificados:

- Catalogo local activo: `4P = 16`, `5P = 20`, `6P = 21`.
- Prueba masiva: 171 plantillas, 17,100 ejercicios generados, 0 errores.
- `unittest`: 91 pruebas OK.
- `npm run build`: OK.
- `request_id` hace idempotente el inicio: la misma solicitud no crea partidas duplicadas.

Errores HTTP esperados:

```text
201: partida creada
200: solicitud repetida con request_id ya procesado
400: payload, grado o tema invalido
401: token ausente o invalido
403: usuario sin permiso o asignacion no disponible
404: recurso inexistente
409: configuracion academica incompleta o estado incompatible
500: error inesperado con logger.exception en backend
```

Causa corregida:

```text
backend/services/juego_adaptativo_service.py

La validacion institucional consultaba columnas inexistentes:
- pe.id_perfil
- ig.id_grado

El esquema real contiene:
- pe.id_perfil_estudiante
- ig.id_grado_base
```

Migracion aplicada:

```text
database/actualizar_idempotencia_partidas.sql
```

Agrega:

```text
partidas_juego.request_id VARCHAR(80) NULL
uk_partidas_request_id UNIQUE (request_id)
```

## 30. Actividades, reintentos y mapas

Se separo la asignacion academica de la partida del juego.

Modelo actual:

- `asignaciones`: actividad global creada por el docente.
- `partidas_juego`: intento individual de un estudiante.
- `estudiante_asignaciones`: progreso de cada estudiante dentro de cada asignacion.

Estados por estudiante:

```text
pendiente
en_progreso
completada
```

Reglas funcionales:

- Una actividad empieza como `pendiente` cuando aparece para el estudiante.
- Al iniciar una partida asignada cambia a `en_progreso`.
- Cada nueva partida incrementa `cantidad_intentos`.
- Si el estudiante pierde las 5 vidas, la partida queda `sin_vidas` y la actividad sigue `en_progreso`.
- Si el estudiante sale, la partida queda `abandonada` y la actividad sigue `en_progreso`.
- Al reintentar se crea una nueva partida con casilla `0`, `5` vidas, `0` correctas y `0` errores.
- La actividad solo cambia a `completada` cuando una partida llega a `total_correctos >= 10` y `casilla_actual >= 10`.
- La actividad completada desaparece de pendientes filtrando `estudiante_asignaciones.estado <> 'completada'`.
- No se elimina la asignacion, la fila de progreso, las partidas, los intentos ni los ejercicios generados.
- Otro estudiante conserva su propio estado aunque un companero ya haya completado la misma asignacion.

Tabla agregada:

```text
database/create_estudiante_asignaciones.sql
```

Campos principales:

```text
id_estudiante_asignacion
id_asignacion
id_estudiante
estado
fecha_asignacion
fecha_inicio
fecha_completada
cantidad_intentos
ultima_partida
fecha_ultima_actividad
```

Backfill:

- Partidas historicas `completada` con `total_correctos >= 10` y `casilla_actual >= 10` marcan al estudiante como `completada`.
- Partidas `abandonada`, `sin_vidas` o `en_curso` no completan la actividad.

Endpoints afectados:

```text
GET /api/estudiante/asignaciones
POST /api/juego/partidas
POST /api/juego/partidas/<id_partida>/respuesta
POST /api/juego/partidas/<id_partida>/salir
```

Mapas:

- El frontend conserva tres escenarios base y agrega seis escenarios desbloqueables:
  - `bosque` -> `frontend/src/assets/juego/escenarios/1.png`
  - `mapa_2` -> `frontend/src/assets/juego/escenarios/2.png`
  - `mapa_3` -> `frontend/src/assets/juego/escenarios/3.png`
  - `mapa_4_espacio` a `mapa_9_cueva_cristales` -> `frontend/src/assets/juego/recompensas/escenarios/`
- Cada mapa define casillas logicas `0` a `10` en `frontend/src/config/mapasConfig.js`.
- Las coordenadas son porcentuales y se consumen por `obtenerPosicionCasilla(mapa, casilla_actual)`.
- El backend elige el mapa al crear una nueva partida y lo guarda en `partidas_juego.mapa`.
- React ya no envia `mapa` como autoridad para estudiantes.
- Se evita repetir inmediatamente el mapa anterior de la misma asignacion y estudiante cuando hay alternativas.
- Durante una partida el mapa permanece fijo; al refrescar debe usarse el valor persistido en `partidas_juego.mapa`.
- No se modifico la logica de `snapACasilla`, `posicionBase`, `offsetAnimacion` ni el anclaje del sprite.

## Personalizacion, tienda y experiencia del estudiante

- Al completar onboarding, un estudiante entra a `/juego`; el panel permanece como vista secundaria y usa estrellas derivadas de progreso real en vez de porcentajes, niveles adaptativos o tiempos tecnicos.
- El menu de estudiante muestra `Juego`, `Actividades` solo para modalidad institucional, `Mi personaje`, `Tienda` y `Panel`. La actualizacion de grado se mantiene dentro de `Configuracion escolar` y solo para grupos educativos.
- `preferencias_estudiante` guarda el personaje actual, el modo de mapa (`aleatorio` o `fijo`), el mapa fijo y el ultimo mapa usado. El backend valida la propiedad antes de cambiar una preferencia.
- `tienda_items`, `usuario_items`, `monederos` y `movimientos_monedas` separan la economia de los puntos historicos. Los personajes starter `masculino` y `femenino`, junto con los mapas base, se desbloquean al crear o consultar la personalizacion.
- Los personajes nuevos cuestan 25 monedas y los mapas nuevos 20. Una compra bloquea monedero e inventario dentro de una transaccion, toma el precio del catalogo y registra el movimiento; no acepta precio ni usuario del frontend.
- Los nuevos assets estan en `frontend/src/assets/juego/recompensas`. Cada personaje usa tres vistas estaticas en tienda, alternadas cada dos segundos, y doce frames separados para acierto/error solo en el juego. Los seis escenarios nuevos conservan configuraciones propias de casillas 0 a 10.
- El juego no recibe personaje o mapa desde React al iniciar: resuelve inventario y preferencias en backend. El modo aleatorio elige entre mapas desbloqueados e intenta evitar el ultimo; el modo fijo conserva el mapa seleccionado durante toda la partida.
- La pregunta inicial nunca incluye respuesta ni explicacion. Tras una respuesta incorrecta, la API devuelve respuesta correcta y explicacion determinista; React pausa los controles, muestra el panel `Vamos a revisarlo` y habilita la siguiente pregunta solo despues de `Entendido`.

### Personajes iniciales

- El onboarding consulta `GET /api/onboarding/personajes-iniciales`, que entrega únicamente personajes de `tienda_items` con `tipo = personaje`, `es_inicial = 1` y estado activo. Actualmente son Explorador (`masculino`) y Exploradora (`femenino`); no se carga ni se oculta el catálogo premium en esa vista.
- Al finalizar onboarding se garantizan ambos starters en `usuario_items` y se guarda la elección como `personaje_key` en `preferencias_estudiante`, además del valor de compatibilidad en `perfiles_estudiante.personaje`.
- Los demás personajes son premium y conservan precio de 25 monedas. `puede_usar_personaje` centraliza la autorización: permite un starter o un personaje realmente desbloqueado; cambio de personaje e inicio de partida usan esa misma regla.
- La migración `database/actualizar_personajes_iniciales.sql` normaliza la clasificación y asegura solo los dos starters. No borra inventario, no modifica preferencias premium existentes y no concede personajes premium a usuarios históricos ni al usuario QA.
- La excepción controlada es `estudiante500@mision.test`: la migración marca como inactivos únicamente sus personajes premium previos para que sus 500 monedas permitan probar una compra desde el estado bloqueado. El historial se conserva y no se elimina ningún registro.

Endpoints de estudiante:

```text
GET  /api/estudiante/tienda
GET  /api/estudiante/inventario
POST /api/estudiante/tienda/comprar
GET  /api/estudiante/personalizacion
PUT  /api/estudiante/personalizacion/personaje
PUT  /api/estudiante/personalizacion/mapa
```

## Recompensas, monedas y continuaciones

### Monedero e historial

- `monederos` mantiene un unico saldo entero no negativo por estudiante (`id_usuario` es la clave unica). Estudiantes nuevos y existentes sin monedero se inicializan con `0`; no se convierten puntos historicos en monedas.
- `movimientos_monedas` es el historial inmutable de cada cambio. Conserva cantidad con signo, saldo anterior/nuevo, partida, item de tienda, descripcion y `request_id` cuando la operacion requiere idempotencia.
- La misma tabla y el mismo monedero se usan en recompensas, continuaciones y tienda. Los personajes mantienen precio `25` y los mapas `20`.
- La migracion incremental `database/actualizar_personalizacion_tienda.sql` agrega los campos de economia a instalaciones existentes. `database/init_database.sql` tambien la incluye para instalaciones limpias.

### Recompensa de partida

- El backend acredita la recompensa en la misma transaccion que registra la decima respuesta correcta y marca la partida como `completada`.
- Una partida ganada requiere `total_correctos >= 10`, `casilla_actual = 10` y estado `completada`.
- Una victoria normal acredita exactamente `+1` con movimiento `recompensa_partida`.
- Una victoria perfecta acredita exactamente `+2` con `recompensa_partida_perfecta`; no suma una recompensa normal adicional.
- La perfeccion exige cero errores, `vidas_perdidas_total = 0` y `continuaciones_compradas = 0`. Se auditan estos valores en `partidas_juego`, por lo que recuperar vidas no restablece elegibilidad.
- `recompensa_otorgada` se bloquea y se marca en la misma transaccion. El `request_id` de la respuesta evita repetir el intento; juntos impiden una doble recompensa.

### Continuar partida

- `POST /api/juego/partidas/<id_partida>/continuar` recibe solo `request_id`. Nunca acepta precio, saldo ni recompensa desde React.
- Solo el propietario estudiante puede continuar una partida `sin_vidas` con saldo suficiente. El monedero se bloquea con `FOR UPDATE`, se registra `continuar_partida` por `-1`, se restauran cinco vidas y se reactiva la misma partida.
- Se mantienen id de partida, asignacion, tema, nivel adaptativo, personaje, mapa, casilla, aciertos, errores e historial. Solo se genera la siguiente pregunta disponible.
- La unicidad de `movimientos_monedas.request_id` y la consulta idempotente evitan doble cobro por doble clic. Saldo insuficiente responde `409` y nunca deja el saldo negativo.

### API y experiencia visual

- `GET /api/estudiante/monedas` devuelve el saldo autenticado en `{ "saldo": n }`.
- El panel, tienda y personalizacion reutilizan `CoinBalance`, que usa `frontend/src/assets/juego/ui/moneda.png`, la imagen pixel-art oficial, con `alt="Moneda"` e `image-rendering: pixelated`.
- El contador se alimenta de respuestas del backend. El modal final muestra `+1` o `+2` y el saldo actualizado; al quedarse sin vidas muestra el saldo y deshabilita la continuacion si es menor que una moneda.
- La pequena animacion de recompensa se omite cuando el usuario solicita movimiento reducido mediante `prefers-reduced-motion`.

### Verificacion

- `backend/tests/test_recompensas_monedas.py` cubre saldo inicial, victoria normal, victoria perfecta sin `+3`, perdida sin recompensa y perdida de elegibilidad perfecta.
- La bateria `unittest` y `npm run build` se ejecutan antes de entregar cambios.

## Etiquetas visibles y español

### Convenciones de texto de interfaz

- El idioma de la interfaz es español en UTF-8 y el nombre oficial siempre es `Misión Matemática`.
- Los slugs, enums, columnas y claves JSON pueden conservar `snake_case`; nunca se muestran directamente al usuario.
- `formatLabel` traduce etiquetas conocidas con un diccionario explícito y aplica un respaldo legible solo a valores técnicos no registrados. No se usa sobre nombres, correos, instituciones ni enunciados escritos por usuarios.
- Las fechas de API se presentan mediante `formatDateTime`, no como timestamps. Los mensajes para estudiantes usan lenguaje sencillo; los de docencia y administración mantienen lenguaje claro y profesional.

- `frontend/src/constants/uiLabels.js` centraliza las etiquetas visibles de roles, estados, tipos de actividad, tipos de respuesta, dificultades, acciones y temas matemáticos.
- `formatLabel(valor)` conserva el valor técnico recibido de la API y devuelve una etiqueta en español; las claves conocidas tienen una traducción explícita y las desconocidas usan un reemplazo seguro de guiones bajos seguido de capitalización.
- Las vistas de actividades, asignaciones, administración, plantillas, reportes, grados y secciones usan esta utilidad para impedir que estados como `en_progreso` o temas como `regla_tres_directa` lleguen directamente a la interfaz.
- Los mensajes que Flask devuelve al usuario se revisaron en autenticación, asignaciones, juego, personalización e instituciones para usar ortografía, tildes y puntuación correctas.
- La identidad visual y los textos oficiales usan el nombre `Misión Matemática`; no se modificaron rutas, claves JSON, columnas de base de datos ni identificadores internos.

## Generación procedimental y agente adaptativo

El flujo de una partida nueva es estrictamente: contexto autenticado, objetivo académico resuelto por el agente, plantilla procedimental exacta, parámetros matemáticos, validación y ejercicio generado. El frontend no decide contexto, grado ni dificultad.

- El juego personal usa `progreso_personal_tema`: cada tema compartido inicia en Cuarto Fácil y puede avanzar secuencialmente hasta Sexto Difícil con evidencia sostenida. Las actividades usan `progreso_asignacion_tema_estudiante`, bloqueadas al grado de su asignación.
- `MotorReglasAdaptativo` ajusta solo la dificultad dentro del objetivo resuelto. `progreso_service` aplica la promoción curricular personal o mantiene el grado de una asignación; el generador no cambia progreso ni reglas académicas.
- Las partidas nuevas no usan el banco histórico `ejercicios` como respaldo. `plantillas_ejercicios` se consulta por la combinación exacta de `id_grado`, `id_tema` e `id_nivel`; si no existe una plantilla válida, se revierte la transacción y la API responde `configuracion_incompleta`.
- Las divisiones enteras y decimales se construyen exactas. Las fracciones usan `Fraction`, los decimales usan `Decimal`, y las figuras geométricas se generan con datos coherentes con el cálculo solicitado.

Verificación del catálogo local: las 171 combinaciones curriculares activas de Cuarto, Quinto y Sexto tienen al menos una plantilla procedimental publicada. La prueba masiva `backend/tests/demo_generacion_catalogo_masiva.py` genera 100 ejercicios por plantilla de catálogo y detiene el proceso ante cualquier error matemático o de configuración.

### Matriz de dificultad curricular

La migración `database/actualizar_dificultad_facil.sql` define únicamente las plantillas procedimentales publicadas cuyo nombre termina en `catalogo` y cuyo nivel es `facil`. No altera las plantillas creadas manualmente, el agente adaptativo, la progresión curricular ni las configuraciones de Intermedio y Difícil.

| Nivel | Propósito | Complejidad de los ejercicios |
| --- | --- | --- |
| Fácil | Introducción y refuerzo. | Cantidades pequeñas, resultados comprobables, una o dos operaciones y explicaciones de uno a tres pasos. |
| Intermedio | Consolidación. | Conserva los rangos, estructuras y explicaciones ya configurados en el catálogo. |
| Difícil | Dominio. | Conserva los rangos, estructuras y explicaciones ya configurados en el catálogo. |

| Grado | Temas en Fácil | Límites principales |
| --- | --- | --- |
| Cuarto | Suma, resta, multiplicación, división, potencias, raíz cuadrada y operaciones combinadas. | Sumas y restas de hasta tres cifras; multiplicación de hasta dos cifras por una cifra; divisiones exactas pequeñas; cuadrados; raíces hasta 10; combinadas sin paréntesis y con dos operaciones. |
| Cuarto | Fracciones, decimales y porcentajes. | Fracciones propias con denominadores de 3 a 6; decimales con dos cifras; porcentajes de 10%, 25%, 50% o 100% con resultado entero. |
| Quinto | Operaciones, fracciones, decimales, porcentajes, conversiones y regla de tres. | Cantidades moderadas; productos por factores de hasta 12; fracciones propias pequeñas; conversiones con denominadores 2, 4 y 5; regla de tres directa o inversa con relación y resultado enteros. |
| Sexto | Operaciones, fracciones, decimales, porcentajes, conversiones, regla de tres y geometría. | Valores introductorios; hasta tres decimales cuando corresponde; regla de tres con resultados enteros; áreas de cuadrado, rectángulo o triángulo con medidas de 2 a 8 y resultado entero. |

La fracción de una suma o resta fácil comparte denominador y es propia. La división decimal fácil usa divisor entero y un resultado decimal exacto de una cifra. Estas restricciones son parámetros del generador, por lo que cada ejercicio sigue siendo variable sin reintroducir resultados complejos.

## Auditoría de optimización y documentación

### Línea base medida

La auditoría estática y de build del 26 de septiembre de 2026 revisó 84 archivos Python ejecutables y 58 módulos JavaScript/JSX. Antes de los cambios, el build de producción contenía 171 archivos y ocupaba `155,700,902` bytes en disco; este total incluye todas las imágenes emitidas, no el tráfico inicial de una pantalla. Los assets más pesados son los escenarios pixel-art: `escenario_1_base_1983x793.png` (3.51 MB), `escenario_9_cueva_cristales_1983x793.png` (3.03 MB) y `escenario_7_fondo_marino_1983x793.png` (2.94 MB).

Después de los cambios, el build contiene los mismos 171 archivos y ocupa `155,701,132` bytes (`+230` bytes). El aumento mínimo corresponde al código de coordinación y documentación añadido, no a recursos visuales. El chunk inicial JavaScript mide 206,956 bytes (69.09 kB gzip); Juego y Tienda siguen cargando en chunks diferidos de 17,678 y 6,572 bytes respectivamente.

El tamaño de transferencias por ruta, la cantidad de solicitudes iniciales desde un navegador autenticado y los tiempos de consultas de producción no se midieron en esta auditoría. No se atribuyen porcentajes de mejora sin esas mediciones.

### Optimizaciones verificadas

- El arranque carga páginas con `React.lazy` y `Suspense`; administración, reportes, plantillas, juego, tienda y personalización permanecen en chunks de ruta separados. No se añadió React Router porque el proyecto ya usa navegación SPA basada en `history` y eventos internos, sin recargar la página, y reemplazarla cambiaría la arquitectura funcional sin una ganancia medida.
- `apiClient.js` es la única instancia HTTP del frontend. El refresh de sesión usa una promesa compartida para impedir renovaciones concurrentes; errores 403, 404 y 500 no fuerzan cierre de sesión. Las mutaciones no se reintentan automáticamente.
- El sprite del juego conserva sus coordenadas y anclaje de pies, pero se desplaza con `translate3d` en lugar de actualizar `left` y `top` en cada frame. El `ResizeObserver` del tablero agrupa sus notificaciones con `requestAnimationFrame` y se cancela al desmontar.
- El catálogo de temas del juego se agrupa con `useMemo`, por lo que no se vuelve a calcular durante una animación. `CoinBalance` se memoriza y no se vuelve a dibujar por estados ajenos al saldo.
- Las consultas internas más frecuentes de `partidas_juego` dejaron de usar `SELECT *`; `juego_adaptativo_service` selecciona las columnas que serializa y mantiene los bloqueos e idempotencia existentes.
- No se agregaron índices nuevos a ciegas. `optimizar_indices_y_seed_qa.sql` ya protege de duplicados y cubre partidas por usuario/estado, intentos por partida, decisiones, movimientos de monedas, inventario y actividades. La revisión no detectó un índice adicional justificable sin métricas de producción.
- No se eliminó código ni assets: no se confirmó código muerto. Las animaciones completas permanecen fuera del DOM de la tienda; la tienda solo muestra las tres vistas estáticas configuradas y las previsualizaciones de mapas usan carga diferida.

### Convenciones de documentación del código

- **Python:** los servicios, rutas y algoritmos de negocio relevantes usan docstrings en español. Las transacciones, validaciones de propiedad y reglas académicas se explican cerca de la función que las protege.
- **React:** componentes y páginas explican su responsabilidad; los efectos no evidentes describen la sincronización y limpieza de listeners, observadores o temporizadores.
- **SQL:** las migraciones nuevas o modificadas incluyen encabezado con objetivo y compatibilidad. Los índices se documentan por la consulta que aceleran.
- **CSS:** los estilos se agrupan por pantalla o componente; los ajustes de posicionamiento del juego explican cuando protegen el rendimiento o el anclaje visual.
- **Pruebas:** cada prueba relevante deja claro qué regla de negocio, restricción matemática o garantía de seguridad verifica.

### Verificación de la auditoría

| Verificación | Resultado |
| --- | --- |
| Sintaxis Python | Correcta con `python -m compileall`; el bytecode de la auditoría se dirigió a una carpeta temporal para no interferir con procesos de desarrollo que bloquean `__pycache__`. |
| Suite backend | `146` pruebas `unittest` correctas. |
| Etiquetas frontend | `5` pruebas Node correctas. |
| Build frontend | Correcto: Vite transformó 264 módulos. |
| Lint | No medido: `package.json` no define un script de lint. |
| Índices MySQL | `EXPLAIN` usa `idx_partidas_usuario_estado_actividad` para partidas activas e `idx_intentos_partida_fecha` para intentos por partida. La consulta idempotente se apoya en la unicidad de `request_id`. |
| Migraciones | No se agregó una migración de índices: las existentes son idempotentes y los índices requeridos ya están presentes. |

La cobertura de comentarios se prioriza por responsabilidad y riesgo: servicios de juego, transacciones de monedas, generador, progreso, rutas y componentes de interacción. No se agregan docstrings automáticos a funciones triviales, datos estáticos, assets ni archivos generados, porque esos textos no mejorarían la mantenibilidad y tenderían a quedar obsoletos.

## Retroalimentación ante errores

Cada ejercicio procedimental guarda `respuesta_correcta` y `explicacion_pasos` en `ejercicios_generados`. Los pasos se derivan de los mismos parámetros matemáticos validados, no usan servicios de IA y se limitan a uno a cuatro mensajes breves.

- Las preguntas nuevas no envían respuesta correcta ni procedimiento a React.
- Solo una respuesta incorrecta devuelve `respuesta_correcta` y `explicacion_pasos`; una respuesta correcta conserva el avance normal sin revelar información adicional.
- El panel del juego muestra una única línea de respuesta correcta, la sección `¿Cómo se resuelve?`, los pasos y el botón `Entendido`. Hasta pulsarlo, la siguiente pregunta queda bloqueada.
- Los ejercicios importados reutilizan sus pasos persistidos cuando existen; si no, se muestra solo un procedimiento mínimo derivado de una operación reconocible.

## Catálogo de temas del juego personal

En el juego personal todos los estudiantes ven los 21 temas activos, sin filtrar el selector por grado institucional ni por el grado desbloqueado del progreso global. El estudiante elige solamente el tema; grado curricular y dificultad siguen siendo resueltos internamente por el backend y el agente adaptativo.

| Tema | Grado mínimo personal |
| --- | --- |
| Suma, Resta, Multiplicación, División, Potencias, Raíz cuadrada, Operaciones combinadas | Cuarto |
| Suma, Resta, Multiplicación y División de fracciones | Cuarto |
| Suma, Resta, Multiplicación y División de decimales; Porcentajes | Cuarto |
| Operaciones combinadas de fracciones, Conversiones de fracciones, Regla de tres directa e inversa | Quinto |
| Geometría | Sexto |

- El progreso personal se inicializa bajo demanda y por tema: un tema sin historial inicia en su grado mínimo con dificultad Fácil. Practicar Geometría no modifica el progreso de Suma ni la matrícula del estudiante.
- Las actividades docentes permanecen restringidas por el grado institucional: Cuarto no incluye regla de tres ni Geometría; Quinto puede incluir regla de tres pero no Geometría; Sexto puede incluir Geometría.
- `database/actualizar_catalogo_personal_temas.sql` reejecuta de forma idempotente el seed de catálogo para completar los temas y sus plantillas publicadas en instalaciones existentes.

## Auditoría integral de seguridad

La revisión local del 26 de septiembre de 2026 quedó documentada en [SECURITY_AUDIT.md](SECURITY_AUDIT.md). Se revisaron 91 operaciones API, autenticación, roles, sesiones JWT, acceso por propiedad, consultas SQL, CORS, cabeceras, economía del juego, configuración y dependencias.

Se corrigió el registro público de administradores, el arranque de producción con secreto JWT de ejemplo, la confianza implícita en `X-Forwarded-For`, la validación del encabezado JWT y una ruta de error del juego. El frontend actualiza Vite a `8.3.1` y su plugin de React a `6.1.1`; el `npm audit` final reporta cero vulnerabilidades conocidas. El uso actual de `localStorage` para tokens queda documentado como riesgo residual a considerar si se implementa una migración futura a cookies `HttpOnly` con CSRF.

Verificación posterior: sintaxis Python correcta con AST, `146` pruebas backend correctas, `5` pruebas frontend correctas y build de producción correcto. `pip check` no encontró dependencias incompatibles; el análisis de vulnerabilidades Python con `pip-audit` permanece pendiente porque esa herramienta no está instalada en el entorno local.

## Corrección de renderizado del personaje

El personaje del juego se obtiene de `partida.personaje`, valor que el backend resuelve desde las preferencias protegidas del estudiante. `personajesConfig.js` transforma esa clave técnica en el frame inicial `idle`, los seis frames de acierto y los seis de error; al cargar el módulo valida que todos los personajes activos tengan esas rutas disponibles.

`GameBoard` escala las coordenadas lógicas del mapa base `1983 x 793` y entrega el punto de apoyo a `CharacterSprite`. La regla `.character-position` debe iniciar en `left: 0` y `top: 0` dentro de `.game-board-inner`; desde ese origen, `translate3d` aplica la coordenada escalada y `.character-sprite-box` resta `feetAnchor`. Omitir ese origen deja al elemento absoluto en su posición estática posterior a la imagen del mapa y lo desplaza fuera del stage.

La corrección conserva `spriteBox`, `feetAnchor`, `offsetAnimacion` y `snapACasilla()`. La prueba local de pantalla completa mostró el Explorador en casilla lógica `0`, luego en casilla `1` tras un acierto y de vuelta en la misma coordenada después de un error, sin errores de consola. El build de frontend y las cinco pruebas Node finalizaron correctamente.

## Preparación de producción y despliegue

La aplicación mantiene su arquitectura `React/Vite -> API Flask -> MySQL/MariaDB`. El frontend se publica como SPA estática desde `frontend/dist`; Nginx reenvía únicamente `/api/` a Gunicorn y conserva las rutas cliente mediante `try_files ... /index.html`.

- `backend/wsgi.py` expone la aplicación Flask para Gunicorn. El servidor local de desarrollo continúa usando `python app.py`.
- `GET /api/health` verifica que Flask está disponible sin consultar base de datos ni revelar configuración. Se usa para comprobar la API detrás de Nginx o systemd, no como diagnóstico de dependencias.
- `deploy/run-gunicorn.sh`, `deploy/mision-matematica.service` y `deploy/nginx-mision-matematica.conf` son plantillas Linux; requieren sustituir rutas, dominio y certificados antes de usarse.
- `DEPLOY.md` describe variables de entorno, HTTPS, firewall, backups, rollback y los elementos externos que no están definidos en el repositorio.
- `GUNICORN_WORKERS`, `GUNICORN_THREADS` y `GUNICORN_TIMEOUT` son variables configurables. No se añadió un pool de MySQL porque el backend usa conexiones cortas cerradas por servicio y no se dispone de una medición de concurrencia que justifique cambiar esa semántica transaccional.
- `.github/workflows/ci.yml` prepara una validación sin despliegue: MySQL 8, esquema SQL, pruebas `unittest`, pruebas Node y build Vite.

## Dockerización

El despliegue Docker conserva la separación de responsabilidades: `frontend` compila React con Node y sirve solo `dist/` mediante Nginx; `backend` ejecuta `wsgi:app` con Gunicorn y usuario no-root; `db` usa MySQL 8.4 en el volumen nombrado `mysql_data`.

- En producción, Nginx publica únicamente `80:80`; el navegador usa `/api` en mismo origen y Nginx reenvía ese prefijo completo a `backend:8000`. MySQL no expone el puerto 3306.
- `docker-compose.local.yml` publica `8080`, `8000` y `3307` para pruebas sin chocar con la configuración local de XAMPP. No ejecuta Vite ni `python app.py`.
- El directorio `database/` se monta de solo lectura durante el primer arranque. `database/docker-init/00-init.sh` cambia al directorio de inicialización para que los `SOURCE database/...` de `init_database.sql` se resuelvan correctamente. La imagen oficial solo lo ejecuta en un volumen vacío.
- Las migraciones incrementales siguen siendo explícitas y manuales mediante `scripts/docker-run-sql.sh`; no se aplican automáticamente al actualizar contenedores.
- No se detectaron uploads, PDF, exports ni archivos generados que exijan otro volumen persistente. Los assets del juego forman parte del build estático.
- `DOCKER_DEPLOY.md` concentra comandos de VPS, variables, HTTPS, backup, restauración, actualización y diagnóstico. Docker no estaba instalado en el equipo durante la preparación, por lo que `docker compose config`, construcción de imágenes, persistencia del volumen y pruebas funcionales dentro de contenedores deben ejecutarse en un host con Docker antes del primer despliegue.

