# 🎨 ARTISAN — Tienda online con checkout por WhatsApp

Aplicación web de comercio electrónico construida con **Flask**. Permite publicar un catálogo de productos y categorías, gestionar un carrito de compras y cerrar el pedido mediante un mensaje preformateado de **WhatsApp**, dejando el registro de la orden en la base de datos.

> **Documentación completa:** empieza por [`docs/README.md`](docs/README.md).
> Documentación generada el **25 de octubre de 2026** sobre el commit `dfeec6d`.

---

## ✨ Características

- Registro e inicio de sesión con contraseñas hasheadas (`werkzeug.security`).
- Sesiones de Flask con cookies `HttpOnly` y `Secure` en producción.
- Catálogo público por categorías, con filtro por categoría y nombre.
- Ficha de producto con galería de hasta 3 imágenes, descripción y subproductos.
- Carrito de compras almacenado en sesión, con cantidades de 1 a 1000.
- Recalculo del total contra la base de datos al confirmar la compra (anti-manipulación).
- Checkout que registra el pedido y abre WhatsApp con el detalle.
- Panel de administración protegido por rol:
  - Pedidos recibidos y detalle en modal.
  - Alta y borrado de categorías.
  - Alta, edición y borrado de productos.
  - Productos principales y subproductos (`parent_id`).
  - Carga de imágenes con validación de extensión y firma binaria.
- Protección CSRF en todos los formularios `POST`.
- Rate limiting global con Flask-Limiter.
- Interfaz responsive con tema verde/dorado, tipografías de Google Fonts y animaciones de aparición.
- Soporte de **SQLite** (por defecto) y **PostgreSQL** (`DATABASE_URL`).
- Despliegue con Docker, Docker Compose, Gunicorn y WSGI.

---

## 🧱 Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, Flask 3.0 |
| Plantillas | Jinja2 (incluye parciales, sin herencia) |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de datos | SQLite 3 / PostgreSQL 15 |
| Autenticación | Sesiones Flask + hash scrypt de Werkzeug |
| Seguridad | CSRF propio, Flask-Limiter, validación de uploads |
| Servidor | Gunicorn + `wsgi.py` |
| Contenedores | Docker, Docker Compose |
| CI | GitHub Actions |

---

## 🚀 Inicio rápido (Windows / PowerShell)

```powershell
# 1. Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables mínimas (la app lee el entorno del proceso)
$env:SECRET_KEY = "cambia-esto-por-una-cadena-larga"
$env:WHATSAPP_PHONE = "573123580705"
$env:INITIAL_ADMIN_EMAIL = "admin@artisan.com"
$env:INITIAL_ADMIN_PASSWORD = "UnaClaveSegura123!"

# 4. Base de datos + administrador inicial
python database_setup.py

# 5. Servidor de desarrollo
python app.py
```

Abre <http://localhost:5000>.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="cambia-esto-por-una-cadena-larga"
export WHATSAPP_PHONE="573123580705"
export INITIAL_ADMIN_EMAIL="admin@artisan.com"
export INITIAL_ADMIN_PASSWORD="UnaClaveSegura123!"
python database_setup.py
python app.py
```

> ⚠️ **Importante:** el archivo `.env` **no se carga automáticamente** en esta versión. `python-dotenv` está en `requirements.txt`, pero `create_app()` no invoca `load_dotenv()`. Usa variables de entorno del proceso (como arriba), el `env_file` de Docker, o ejecuta `dotenv run -- python app.py`. Ver [Instalación](docs/02-instalacion.md#3-variables-de-entorno).

### Docker

```bash
# Desarrollo (SQLite)
docker compose up --build

# Producción (PostgreSQL + Gunicorn)
docker compose -f docker-compose.prod.yml up --build -d
```

---

## 🔑 Administrador inicial

No hay contraseña por defecto en el código. El administrador se crea **una sola vez** al ejecutar `database_setup.py` con estas variables definidas:

```env
INITIAL_ADMIN_EMAIL=admin@artisan.com
INITIAL_ADMIN_PASSWORD=UnaClaveSegura123!
```

Después del primer acceso, cambia la contraseña. En esta versión **no existe** una pantalla de cambio de contraseña; debe actualizarse directamente en la base de datos con un hash de Werkzeug.

> Los scripts `run.bat` y `run.sh` muestran un banner con `admin@artisan.com / admin123` que corresponde a versiones anteriores. Ese usuario **no se crea automáticamente**. Usa las variables `INITIAL_ADMIN_*`.

---

## ⚙️ Variables de entorno

| Variable | Obligatoria | Por defecto | Descripción |
|---|---|---|---|
| `SECRET_KEY` | Sí en producción | `artisan_key_2026` | Firma de sesiones y CSRF. |
| `SECRET` | No | — | Alternativa a `SECRET_KEY`. |
| `WHATSAPP_PHONE` | No | `573123580705` | Número destino, formato internacional sin `+`. |
| `DATABASE_URL` | No | — | Si empieza por `postgres`, usa PostgreSQL. |
| `SQLITE_PATH` | No | `database.db` | Ruta del archivo SQLite. |
| `FLASK_ENV` | No | — | `production` activa cookies seguras y exige `SECRET_KEY`. |
| `FLASK_DEBUG` | No | — | No lo lee la aplicación; solo herramientas de Flask. |
| `RATELIMIT_STORAGE_URI` | No | `memory://` | Backend de Flask-Limiter. |
| `INITIAL_ADMIN_EMAIL` | Solo setup | — | Correo del admin inicial. |
| `INITIAL_ADMIN_PASSWORD` | Solo setup | — | Contraseña del admin inicial. |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | No | — | Usadas por Compose; la app usa `DATABASE_URL`. |
| `MAIL_*` | No | — | Reservadas; no hay envío de correo implementado. |

Referencia ampliada: [docs/08-despliegue.md](docs/08-despliegue.md#2-variables-de-entorno).

---

## 📁 Estructura del proyecto

```text
Artisan Web/
├── app/                          # Paquete de la aplicación (application factory)
│   ├── __init__.py               # create_app(), CSRF global, filtros y contexto
│   ├── config.py                 # Configuración y validación de producción
│   ├── csrf.py                   # Validación de tokens CSRF
│   ├── db.py                     # Conexión por request (g) y cierre
│   ├── extensions.py             # Instancia de Flask-Limiter
│   └── routes/
│       ├── auth.py               # /login, /registro, /logout
│       ├── shop.py               # /, /index, /lineaproductos, /producto/<id>
│       ├── cart.py               # Carrito y checkout WhatsApp
│       └── admin.py              # Panel y CRUD de productos/categorías
├── templates/                    # Plantillas Jinja2
│   ├── header.html, footer.html  # Parciales reutilizables
│   ├── _flash.html               # Toasts de mensajes flash
│   ├── index.html, lineaproductos.html, producto.html
│   ├── carrito.html, login.html, registro.html
│   └── admin.html, edit_product.html
├── static/
│   ├── css/style.css             # Sistema de diseño completo
│   └── img/productos/            # Imágenes subidas por el admin
├── docs/                         # 📚 Documentación completa
├── .github/workflows/
│   ├── ci.yml                    # Compilación + build Docker
│   └── keep-alive.yml            # Ping a Render cada 14 minutos
├── app.py                        # Entrada de desarrollo
├── wsgi.py                       # Entrada para Gunicorn/uWSGI
├── database_setup.py             # Crea esquema, admin inicial y categorías base
├── db_utils.py                   # Abstracción SQLite/PostgreSQL y migraciones
├── database.db                   # BD SQLite local (generada; no versionada)
├── requirements.txt              # Dependencias de producción
├── dev-requirements.txt          # pytest + requests
├── e2e_test.py                   # Script E2E legado (ver limitaciones)
├── Dockerfile / Dockerfile.prod
├── docker-compose.yml / docker-compose.prod.yml
├── .env.example / .env.docker
├── run.bat / run.sh              # Scripts de conveniencia
├── README.md, CHANGELOG.md, CONTRIBUTING.md
├── PRODUCTION_CHECKLIST.md, RELEASE.md
└── LICENSE
```

---

## 🧭 Rutas principales

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| `GET` | `/` | Público | Redirige a `/index`. |
| `GET` | `/index` | Público | Categorías. |
| `GET` | `/lineaproductos` | Público | Catálogo con filtros. |
| `GET` | `/producto/<id>` | Público | Detalle y subproductos. |
| `GET/POST` | `/login` | Público | Inicio de sesión. |
| `GET/POST` | `/registro` | Público | Registro. |
| `GET` | `/logout` | Sesión | Cierra sesión. |
| `GET` | `/carrito` | Sesión | Carrito. |
| `POST` | `/carrito/add/<id>` | Sesión | Agrega producto. |
| `POST` | `/carrito/update/<id>` | Sesión | Cambia cantidad. |
| `POST` | `/carrito/remove/<id>` | Sesión | Quita producto. |
| `POST` | `/carrito/clear` | Sesión | Vacía carrito. |
| `POST` | `/carrito/checkout` | Sesión | Registra pedido y abre WhatsApp. |
| `GET` | `/admin/` | Admin | Panel. |
| `POST` | `/admin/add_prod` | Admin | Crea producto. |
| `POST` | `/admin/cat/add` | Admin | Crea categoría. |
| `POST` | `/admin/cat/del/<id>` | Admin | Borra categoría. |
| `POST` | `/admin/prod/del/<id>` | Admin | Borra producto. |
| `GET/POST` | `/admin/prod/edit/<id>` | Admin | Edita producto. |

Detalle de parámetros, validaciones y respuestas: [docs/04-rutas.md](docs/04-rutas.md).

---

## 🔐 Seguridad implementada

- Contraseñas con `generate_password_hash` / `check_password_hash` (scrypt).
- Token CSRF por sesión generado con `secrets.token_hex(32)`.
- Validación CSRF en todos los `POST`.
- Decoradores `@admin_required` y `@cart_required`.
- Consultas SQL parametrizadas.
- Validación de subida de imágenes: extensión + firma binaria + `secure_filename`.
- Límite de cuerpo de petición: 16 MB.
- Rate limiting global: 200/día y 50/hora por IP.
- `SECRET_KEY` obligatoria si `FLASK_ENV=production`.
- Cookies `Secure`, `HttpOnly`, `SameSite=Lax` en producción.
- Recalculo del total del carrito desde la BD en el checkout.

Riesgos conocidos y checklist de endurecimiento: [docs/07-seguridad.md](docs/07-seguridad.md).

---

## 🧪 Pruebas

```bash
pip install -r dev-requirements.txt
python -m py_compile app.py wsgi.py database_setup.py db_utils.py
# El repositorio no incluye una suite pytest; e2e_test.py es un script legado.
python e2e_test.py
```

> `e2e_test.py` fue escrito para una versión anterior (usa `GET` en `/carrito/add/1` y no envía CSRF), por lo que **fallará** contra la versión actual. Ver [Operación y mantenimiento](docs/09-operacion-mantenimiento.md#4-pruebas).

---

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [Índice](docs/README.md) | Mapa completo de la documentación. |
| [Arquitectura](docs/01-arquitectura.md) | Application factory, blueprints y ciclo de request. |
| [Instalación](docs/02-instalacion.md) | Entorno local, variables y ejecución. |
| [Base de datos](docs/03-base-de-datos.md) | Esquema, migraciones y respaldos. |
| [Rutas](docs/04-rutas.md) | Referencia de todos los endpoints. |
| [Flujos](docs/05-flujos.md) | Registro, carrito, checkout y administración. |
| [WhatsApp](docs/06-whatsapp.md) | Integración y formato de mensajes. |
| [Seguridad](docs/07-seguridad.md) | Controles, riesgos y endurecimiento. |
| [Despliegue](docs/08-despliegue.md) | Docker, Gunicorn, PostgreSQL, Render y CI. |
| [Operación](docs/09-operacion-mantenimiento.md) | Runbook, respaldos y troubleshooting. |
| [Referencia de código](docs/10-referencia-codigo.md) | Archivo por archivo y función por función. |
| [Interfaz](docs/11-interfaz-ui.md) | Sistema de diseño, plantillas y accesibilidad. |
| [Inventario](docs/12-inventario-archivos.md) | Lista de archivos del proyecto. |

---

## 📦 Empaquetado

El proyecto se entrega también como `artisan.zip`, generado con los archivos fuente, la documentación, las imágenes y los datos locales, excluyendo `.git`, `.venv`, `__pycache__`, `__MACOSX`, el proyecto de ejemplo `Flask_HTML_Sample` y el archivo `.vsix` de Copilot. Consulta el [inventario](docs/12-inventario-archivos.md#9-contenido-del-zip).

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).

**Artisan Web · 2026**
