# 01 · Arquitectura

## 1. Visión general

Artisan es una aplicación **Flask monolítica** con renderizado del lado del servidor (SSR). No usa ORM ni API REST: las rutas consultan la base de datos con SQL parametrizado y devuelven HTML de Jinja2. La única integración externa es **WhatsApp** mediante un enlace `https://api.whatsapp.com/send`.

```text
Navegador
   │  HTTP
   ▼
Gunicorn / servidor de desarrollo
   │  WSGI
   ▼
Flask (create_app)
   ├── before_request: asegura csrf_token en sesión
   ├── Blueprint auth   → /login, /registro, /logout
   ├── Blueprint shop   → /, /index, /lineaproductos, /producto/<id>
   ├── Blueprint cart   → /carrito...
   └── Blueprint admin  → /admin...
   │
   ├── get_db() ──► db_utils.connect_db() ──► SQLite o PostgreSQL
   │                                  └─────► ensure_schema()
   ▼
Jinja2 (templates/) ──► HTML + CSS (static/css/style.css)
   │
   └── Redirect a api.whatsapp.com (checkout y ficha de producto)
```

---

## 2. Stack y responsabilidades

| Componente | Archivo(s) | Responsabilidad |
|---|---|---|
| Entrada desarrollo | `app.py` | Crea la app y ejecuta `app.run(debug=False)`. |
| Entrada producción | `wsgi.py` | Expone `app` para Gunicorn/uWSGI. |
| Application factory | `app/__init__.py` | Configura Flask, filtros, CSRF global, blueprints. |
| Configuración | `app/config.py` | Variables de configuración y validación de producción. |
| CSRF | `app/csrf.py` | Genera/valida el token de formularios. |
| Acceso a datos | `app/db.py` | Conexión por request y cierre al terminar. |
| Driver/abstracción | `db_utils.py` | Conexión SQLite/PostgreSQL, esquema y migraciones. |
| Rate limiting | `app/extensions.py` | Instancia única de `Limiter`. |
| Vistas | `app/routes/*.py` | Lógica de negocio y consultas SQL. |
| Presentación | `templates/` | HTML Jinja2. |
| Estilos | `static/css/style.css` | Sistema de diseño y responsive. |
| Medios | `static/img/productos/` | Imágenes subidas por el administrador. |

**No hay** capa de servicios, repositorios, ORM, API JSON, tareas en segundo plano ni cola de mensajes. Toda la lógica vive en las funciones de ruta.

---

## 3. Application factory (`app/__init__.py`)

`create_app()` se ejecuta una vez por proceso y sigue este orden:

1. Crea `Flask(__name__)` indicando rutas absolutas de `templates/` y `static/` (un nivel arriba del paquete `app/`).
2. Carga `Config` con `app.config.from_object(Config)`.
3. Ejecuta `Config.validate()`: si `FLASK_ENV=production` y no hay `SECRET_KEY`, lanza `RuntimeError`.
4. Convierte `UPLOAD_FOLDER` en ruta absoluta y crea la carpeta si no existe.
5. Inicializa Flask-Limiter.
6. Registra el filtro Jinja `nl2br`.
7. Define `before_request` que crea `session['csrf_token']` si no existe.
8. Define un `context_processor` que inyecta en todas las plantillas:
   - `WHATSAPP_PHONE`
   - `csrf_token()` (callable que lee el token de sesión)
   - `cache_buster()` (timestamp `mtime` de `style.css`)
9. Registra `teardown_appcontext(close_db)`.
10. Importa y registra los blueprints `auth`, `shop`, `cart`, `admin`.

> El número de WhatsApp se resuelve **al importar** `app/__init__.py`:
> `WHATSAPP_PHONE = os.environ.get('WHATSAPP_PHONE', '573123580705').lstrip('+').strip()`.
> Cambiarlo requiere reiniciar el proceso.

### Por qué los blueprints se importan dentro de `create_app`

Evita importaciones circulares: los módulos de rutas importan `app.db` y `app.csrf`, que a su vez forman parte del paquete `app`. Al registrarlos después de configurar la app, se garantiza que `Flask-Limiter` y la configuración ya estén listos.

---

## 4. Blueprints

| Blueprint | Prefijo | Archivo | Endpoints |
|---|---|---|---|
| `auth` | — | `app/routes/auth.py` | `login`, `registro`, `logout` |
| `shop` | — | `app/routes/shop.py` | `home`, `index`, `lineaproductos`, `producto_detalle` |
| `cart` | — | `app/routes/cart.py` | `view_cart`, `add_to_cart`, `remove_from_cart`, `update_cart`, `clear_cart`, `checkout_whatsapp` |
| `admin` | `/admin` | `app/routes/admin.py` | `panel`, `add_product`, `add_category`, `delete_category`, `delete_product`, `edit_product` |

Nombres de endpoint completos: `auth.login`, `shop.index`, `cart.checkout_whatsapp`, `admin.panel`, etc. Las plantillas usan `url_for()` en la mayoría de casos; algunas rutas están escritas a mano (`/index`, `/carrito`, `/login`, `/lineaproductos`).

---

## 5. Ciclo de vida de una petición

Ejemplo: `GET /producto/5`.

```text
1. Gunicorn recibe la petición y llama a wsgi:app.
2. Flask resuelve la regla /producto/<int:id> → shop.producto_detalle.
3. before_request: si no hay csrf_token en sesión, lo crea.
4. shop.producto_detalle(id=5):
   a. get_db() → connect_db() + ensure_schema() (solo la primera vez del request).
   b. SELECT del producto por id.
   c. SELECT de subproductos WHERE parent_id = 5.
   d. render_template('producto.html', p=..., subproductos=...).
5. Jinja2 evalúa la plantilla e incluye header/footer/_flash.
6. context_processor entrega WHATSAPP_PHONE, csrf_token y cache_buster.
7. Se devuelve HTML (200) o redirección si el producto no existe.
8. teardown_appcontext: close_db() cierra la conexión.
```

Puntos clave:

- La conexión se guarda en `flask.g` y se reutiliza durante todo el request.
- `ensure_schema()` se ejecuta cada vez que se abre una conexión nueva: crea tablas si faltan y añade columnas por migración. Es idempotente.
- No hay transacciones explícitas por request; cada vista hace `commit()` cuando escribe.
- Si una vista lanza una excepción no controlada, Flask devuelve 500 y `close_db` se ejecuta igualmente.

---

## 6. Capas y dependencias

```text
templates/  ──depende de──►  contexto de vistas + url_for + filtros
    ▲
    │ render_template
app/routes/*.py  ──►  app/db.py  ──►  db_utils.py  ──►  SQLite / PostgreSQL
    │                    │
    ├──► app/csrf.py     └──► flask.g
    ├──► app/__init__.py (WHATSAPP_PHONE)
    └──► werkzeug.security, werkzeug.utils
```

Reglas implícitas:

- `db_utils.py` **no** importa Flask; es reutilizable fuera de la app (por eso `database_setup.py` lo usa).
- Las rutas no comparten funciones de negocio; cada una valida y consulta lo suyo.
- Las plantillas no ejecutan SQL; solo reciben objetos `sqlite3.Row` / `RealDictRow` o diccionarios.

---

## 7. Frontend

- Cada página es un documento HTML completo (`<!DOCTYPE html>`), no hay herencia `{% extends %}`.
- Se reutilizan parciales con `{% include %}`:
  - `header.html`: cabecera, menú responsive y flash messages.
  - `footer.html`: pie, enlaces de contacto y animación `reveal`.
  - `_flash.html`: toasts con autocierre a los 4 segundos.
- El CSS es un único archivo con variables CSS, componentes y media queries.
- El JavaScript es **vanilla** y está embebido en las plantillas:
  - menú móvil (`header.html`)
  - animación de entrada (`footer.html`)
  - filtros de catálogo (`lineaproductos.html`)
  - enlace dinámico de WhatsApp (`producto.html`)
  - validación y modal de pedidos (`admin.html`)
- No hay bundler, npm, SPA ni llamadas `fetch`. Todo es navegación completa.

Detalle: [11-interfaz-ui.md](11-interfaz-ui.md).

---

## 8. Estructura de directorios

```text
Artisan Web/
├── app/
│   ├── __init__.py          # create_app, CSRF global, filtros, contexto
│   ├── config.py            # Config y validate()
│   ├── csrf.py              # validate_csrf, csrf_required
│   ├── db.py                # get_db, close_db
│   ├── extensions.py        # limiter
│   └── routes/
│       ├── __init__.py      # vacío
│       ├── admin.py
│       ├── auth.py
│       ├── cart.py
│       └── shop.py
├── templates/
├── static/
├── docs/                    # esta documentación
├── .github/workflows/
├── database_setup.py
├── db_utils.py
├── app.py
├── wsgi.py
├── e2e_test.py
├── Dockerfile / Dockerfile.prod
├── docker-compose.yml / docker-compose.prod.yml
└── ...
```

---

## 9. Decisiones de diseño y compromisos

| Decisión | Ventaja | Coste / riesgo |
|---|---|---|
| SQL plano con `?` / `%s` | Simple, sin ORM, portable. | Duplicación de SQL y migraciones manuales. |
| Carrito en sesión | Sin tabla ni limpieza; rápido. | No persiste entre dispositivos; límite de cookie; se pierde al cerrar sesión. |
| Categoría como texto en `productos` | Consultas simples. | Renombrar/borrar categoría deja datos huérfanos. |
| CSRF manual | Sin dependencia extra. | Hay que recordar validar en cada `POST`; no cubre otros verbos. |
| Imágenes en disco | Sin servicio externo. | No hay borrado, optimización ni CDN; crecen sin control. |
| Todo en las rutas | Fácil de seguir. | Difícil de testear y reutilizar; lógica repetida. |
| Sin API REST | Menos superficie de ataque. | Integraciones futuras requieren reescribir. |
| Plantillas completas | Control total del HTML. | Duplicación de `<head>`, header y scripts. |
| Aplicación monolítica | Despliegue sencillo. | Escalado horizontal exige sesiones compartidas/almacenamiento compartido. |

---

## 10. Cómo extender

### Añadir una ruta pública

1. Crea o usa un blueprint en `app/routes/`.
2. Define la función con `@bp.route(...)`.
3. Si escribe en BD: valida CSRF y llama `db.commit()`.
4. Añade la plantilla en `templates/`.
5. Regístralo en `create_app()` si es un blueprint nuevo.
6. Documenta en [04-rutas.md](04-rutas.md).

### Añadir una tabla o columna

1. Añade el `CREATE TABLE` en `ensure_schema()` para SQLite y PostgreSQL.
2. Añade la migración con `table_columns()` + `ALTER TABLE` para instalaciones existentes.
3. Ejecuta `python database_setup.py`.
4. Actualiza [03-base-de-datos.md](03-base-de-datos.md).

### Añadir un filtro o global de Jinja

Usa `app.jinja_env.filters[...]` o el `context_processor` en `create_app()`.

### Añadir un servicio externo

Crea un módulo en `app/services/` (no existe todavía), inicialízalo en `create_app()` y evita llamarlo desde las plantillas.

---

## 11. Diagrama de despliegue

```text
                 Internet
                    │ HTTPS
             ┌──────▼──────┐
             │ Nginx /     │  (opcional, no incluido)
             │ proxy TLS   │
             └──────┬──────┘
                    │ HTTP :5000
        ┌───────────▼───────────┐
        │ Gunicorn (4 workers)  │
        │ wsgi:app              │
        └─────┬──────────┬──────┘
              │          │
      ┌───────▼───┐  ┌───▼──────────────┐
      │ SQLite    │  │ PostgreSQL 15    │
      │ archivo   │  │ (Compose prod)   │
      └───────────┘  └──────────────────┘
              │
      static/img/productos (volumen)
```

En Render (workflow `keep-alive.yml`) se asume un servicio web público en `https://artisan-web-52a0.onrender.com`, sin configuración de infraestructura en el repositorio.

---

**Siguiente:** [02 · Instalación →](02-instalacion.md)
