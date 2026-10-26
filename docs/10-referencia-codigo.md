# 10 · Referencia de código

Guía archivo por archivo. Las líneas son aproximadas y pueden variar con cambios posteriores.

---

## 1. Punto de entrada

### `app.py`

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
```

- Crea la app al importar el módulo (necesario para `flask --app app`).
- `debug=False`: sin recarga automática ni depurador interactivo.
- No define host/puerto; Flask usa `127.0.0.1:5000`.

### `wsgi.py`

Idéntico a `app.py`, pero pensado para `gunicorn wsgi:app`. En producción no se ejecuta el bloque `__main__`.

---

## 2. Paquete `app/`

### 2.1 `app/__init__.py`

| Elemento | Descripción |
|---|---|
| `WHATSAPP_PHONE` | Constante de módulo leída del entorno; limpia `+` y espacios. |
| `_proj_root` | Ruta absoluta del proyecto (padre del paquete). |
| `create_app()` | Application factory. |
| `ensure_csrf()` | `before_request`: crea `session['csrf_token']` si falta. |
| `inject_globals()` | `context_processor`: inyecta `WHATSAPP_PHONE`, `csrf_token`, `cache_buster`. |
| `_cache_buster()` | Devuelve el `mtime` de `static/css/style.css` o `time.time()` si falla. |

Detalle de `create_app()`:

```python
app = Flask(
    __name__,
    template_folder=os.path.join(_proj_root, 'templates'),
    static_folder=os.path.join(_proj_root, 'static'),
)
app.config.from_object(Config)
Config.validate()
app.config['UPLOAD_FOLDER'] = os.path.join(_proj_root, app.config['UPLOAD_FOLDER'])
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
limiter.init_app(app)
app.jinja_env.filters['nl2br'] = lambda v: v.replace('\n', '<br>') if v else ''
...
app.teardown_appcontext(close_db)
# imports y register_blueprint
```

> El filtro `nl2br` devuelve un `str` con `<br>`; Jinja2 lo autoescapa y el resultado visible es `&lt;br&gt;`. Ver [09 §7](09-operacion-mantenimiento.md#7-problemas-conocidos-deuda-técnica).

### 2.2 `app/config.py`

| Atributo | Valor | Notas |
|---|---|---|
| `SECRET_KEY` | `SECRET_KEY` o `SECRET` o `artisan_key_2026` | Fallback inseguro. |
| `UPLOAD_FOLDER` | `static/img/productos` | Se hace absoluto en `create_app()`. |
| `MAX_CONTENT_LENGTH` | `16 * 1024 * 1024` | 16 MB. |
| `RATELIMIT_STORAGE_URI` | `memory://` | Configurable por entorno. |
| `SESSION_COOKIE_SECURE` | `True` si `FLASK_ENV=production` | Requiere HTTPS. |
| `SESSION_COOKIE_HTTPONLY` | `True` en producción | |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` en producción | |

`Config.validate()` lanza `RuntimeError` si `FLASK_ENV=production` y no hay `SECRET_KEY`.

### 2.3 `app/csrf.py`

| Función | Descripción |
|---|---|
| `validate_csrf()` | Si el método no es `POST`, devuelve `True`. Compara `request.form['csrf_token']` con `session['csrf_token']`. Si falla, hace flash y devuelve `False`. |
| `csrf_required(f)` | Decorador que redirige al `referrer` o a `shop.index` si la validación falla. **No se usa actualmente**; las rutas llaman `validate_csrf()` manualmente. |

### 2.4 `app/db.py`

| Función | Descripción |
|---|---|
| `get_db()` | Devuelve `g.db`; si no existe, conecta y ejecuta `ensure_schema()`. |
| `close_db(exception=None)` | Cierra y elimina `g.db` al finalizar el request. |

### 2.5 `app/extensions.py`

```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour']
)
```

No hay decoradores `@limiter.limit` en las rutas; solo se aplican los límites globales.

---

## 3. Rutas

### 3.1 `app/routes/auth.py`

| Función | Endpoint | Notas |
|---|---|---|
| `login()` | `/login` | GET renderiza; POST valida CSRF, busca usuario, verifica hash, actualiza sesión. |
| `registro()` | `/registro` | GET renderiza; POST valida, hashea, inserta `cliente`. |
| `logout()` | `/logout` | `session.clear()` y redirección. |

### 3.2 `app/routes/shop.py`

| Función | Endpoint | Notas |
|---|---|---|
| `home()` | `/` | `redirect(url_for('shop.index'))`. |
| `index()` | `/index` | Lista categorías. |
| `lineaproductos()` | `/lineaproductos` | Filtros `categoria` y `nombre`; construye SQL dinámico con condiciones fijas y parámetros. |
| `producto_detalle(id)` | `/producto/<int:id>` | Producto + subproductos; redirige si no existe. |

### 3.3 `app/routes/cart.py`

| Elemento | Descripción |
|---|---|
| `MAX_QTY = 1000` | Límite de cantidad. |
| `cart_required(f)` | Exige `session['user_id']`; si falta, flash + `/login`. |

| Función | Endpoint | Notas |
|---|---|---|
| `view_cart()` | `GET /carrito` | Total con precios de sesión. |
| `add_to_cart(id)` | `POST /carrito/add/<id>` | CSRF, clamp, solo productos principales, acumula. |
| `remove_from_cart(id)` | `POST /carrito/remove/<id>` | Filtra por id. |
| `update_cart(id)` | `POST /carrito/update/<id>` | Actualiza cantidad si el ítem existe. |
| `clear_cart()` | `POST /carrito/clear` | `session.pop('cart')`. |
| `checkout_whatsapp()` | `POST /carrito/checkout` | Recalcula desde BD, inserta pedido, limpia carrito y redirige a WhatsApp. |

Helpers internos: `cart_required`. No hay funciones auxiliares para el total ni para el mensaje; están inline.

### 3.4 `app/routes/admin.py`

| Elemento | Descripción |
|---|---|
| `ALLOWED_EXTENSIONS` | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`. |
| `ALLOWED_MIME_MAGIC` | Firmas: JPEG `FF D8`, PNG `89 50 4E 47`, WebP `RIFF`, GIF `GIF8`. |
| `admin_required(f)` | Exige `session['rol'] == 'admin'`. |
| `validate_image(file)` | Comprueba extensión + primeros 4 bytes; devuelve extensión o `None`. |
| `save_image(file, nombre, index)` | `secure_filename(f"{nombre}_{index}{ext}")`, guarda y devuelve `/static/img/productos/<fname>`. |

| Función | Endpoint | Notas |
|---|---|---|
| `panel()` | `GET /admin/` | Productos con nombre del padre, categorías y pedidos con JSON parseado. |
| `add_product()` | `POST /admin/add_prod` | Valida campos/precio, guarda 1–3 imágenes, inserta. |
| `add_category()` | `POST /admin/cat/add` | `INSERT OR IGNORE`. |
| `delete_category(id)` | `POST /admin/cat/del/<id>` | `DELETE`. |
| `delete_product(id)` | `POST /admin/prod/del/<id>` | `DELETE` sin borrar archivos ni hijos. |
| `edit_product(id)` | `GET/POST /admin/prod/edit/<id>` | GET carga formulario; POST valida, reemplaza/conserva imágenes y actualiza. |

---

## 4. Capa de datos

### `db_utils.py`

| Elemento | Descripción |
|---|---|
| `DATABASE_URL` | Leída al importar. |
| `using_postgres()` | `True` si `DATABASE_URL` empieza por `postgres`. |
| `DatabaseConnection.execute(query, params)` | Convierte `?`→`%s`, normaliza params, ejecuta y devuelve cursor. |
| `DatabaseConnection.commit()` | Commit. |
| `DatabaseConnection.close()` | Cierra conexión. |
| `connect_db()` | Devuelve `DatabaseConnection` SQLite o PostgreSQL. |
| `table_columns(connection, table)` | Lista columnas (PRAGMA o `information_schema`). |
| `ensure_schema(connection)` | Crea tablas y aplica migraciones; termina con `commit()`. |

Comportamiento de `execute` en PostgreSQL:

```python
query = query.replace('?', '%s')
if 'INSERT OR IGNORE' in query:
    query = query.replace('INSERT OR IGNORE', 'INSERT')
```

El bloque `if 'DELETE' in query and 'WHERE' in query: pass` no tiene efecto.

### `database_setup.py`

| Paso | Acción |
|---|---|
| 1 | `connect_db()` |
| 2 | `ensure_schema(db)` |
| 3 | Si hay `INITIAL_ADMIN_EMAIL` y `INITIAL_ADMIN_PASSWORD`: hash e `INSERT OR IGNORE` admin. |
| 4 | `INSERT OR IGNORE` de Bisutería y Marroquinería. |
| 5 | `commit()`, `close()`, imprime `Base de datos lista.` |

Los errores de inserción se silencian con `except Exception: pass`.

### `e2e_test.py`

Script de prueba de extremo a extremo legado. Usa `requests.Session`, registra un usuario, inicia sesión, agrega al carrito, hace checkout y consulta SQLite. **No funciona con la versión actual** por CSRF y por el método `GET` en `/carrito/add/1`.

---

## 5. Plantillas

| Archivo | Contexto | Responsabilidad |
|---|---|---|
| `header.html` | `session` | Cabecera, logo, menú responsive, enlace admin condicional, login/logout. Incluye `_flash.html` y JS del menú. |
| `footer.html` | `WHATSAPP_PHONE` | Pie con contacto, enlaces y JS `IntersectionObserver` para `.reveal`. |
| `_flash.html` | `get_flashed_messages` | Toasts por categoría (`success`, `error`, `info`, `warning`) con autocierre a 4 s. |
| `index.html` | `categorias` | Tarjetas de categorías. |
| `lineaproductos.html` | `productos`, `categorias`, `nombres`, `categoria_actual`, `nombre_actual` | Filtros y grilla; JS `applyFilters()`. |
| `producto.html` | `p`, `subproductos`, `WHATSAPP_PHONE`, `csrf_token`, `nl2br`, `cache_buster` | Galería, descripción, formulario de carrito, botón WhatsApp, subproductos. |
| `carrito.html` | `items`, `total`, `csrf_token` | Lista, edición de cantidades, eliminar, total, checkout y vaciar. |
| `login.html` | `csrf_token` | Formulario de acceso. |
| `registro.html` | `csrf_token` | Formulario de registro. |
| `admin.html` | `productos`, `categorias`, `pedidos`, `parent_prefill`, `csrf_token` | Pedidos, categorías, alta de producto y tabla de productos; JS de validación y modal. |
| `edit_product.html` | `p`, `categorias`, `productos`, `csrf_token` | Formulario de edición con imágenes actuales. |

No existe `templates/base.html`; la documentación antigua lo mencionaba por error.

### Variables globales disponibles

En todas las plantillas:

- `WHATSAPP_PHONE`
- `csrf_token()` → string
- `cache_buster()` → string

Y `session` de Flask.

---

## 6. CSS

`static/css/style.css` (~25 KB) contiene todo el diseño. Secciones delimitadas por comentarios:

```text
UTILITIES
TOAST NOTIFICATIONS
BUTTONS
HEADER
AUTH PAGES
FOOTER
PRODUCT GRID
FILTERS
PRODUCT DETAIL
CART
ADMIN
ORDER STATUS BADGES
ADMIN MODAL
ANIMATIONS
RESPONSIVE
```

Variables principales en `:root`:

| Grupo | Variables |
|---|---|
| Fondos | `--bg`, `--bg-elevated`, `--bg-surface`, `--bg-light`, `--bg-white` |
| Dorado | `--gold`, `--gold-light`, `--gold-dim` |
| Acento | `--accent`, `--accent-hover` |
| Estados | `--danger`, `--danger-hover`, `--success`, `--info` |
| Texto | `--text`, `--text-heading`, `--text-dark`, `--text-muted`, `--text-body` |
| Bordes | `--border`, `--border-light` |
| Tipografía | `--font-heading`, `--font-logo`, `--font-body` |
| Radios/sombras | `--radius`, `--radius-sm`, `--radius-lg`, `--shadow`, `--shadow-lg` |
| Transición | `--transition` |

Media queries: `1024px`, `850px`, `768px`, `480px`.

Detalle: [11-interfaz-ui.md](11-interfaz-ui.md).

---

## 7. Archivos de despliegue y configuración

| Archivo | Contenido |
|---|---|
| `requirements.txt` | Flask 3.0.0, Werkzeug 3.0.1, python-dotenv 1.0.0, gunicorn 21.0.0, Flask-Limiter 2.9.0, psycopg2-binary 2.9.10. |
| `dev-requirements.txt` | pytest 7.4.0, requests 2.31.0. |
| `Dockerfile` | Imagen de desarrollo; instala gcc, gunicorn; ejecuta setup + Gunicorn. |
| `Dockerfile.prod` | Imagen de producción; `build-essential`, `libpq-dev`, `FLASK_ENV=production`; sin setup. |
| `docker-compose.yml` | `web` + volúmenes + `.env.docker`. |
| `docker-compose.prod.yml` | `db` (postgres:15) + `web` (Dockerfile.prod). |
| `.env.example` | Plantilla de variables. |
| `.env.docker` | Variables para Compose (placeholders). |
| `.gitignore` | Excluye `.env`, `*.db`, imágenes y cachés. |
| `.dockerignore` | Excluye `.git`, `.venv`, `.env`, `*.db`, etc. |
| `run.bat` / `run.sh` | Crean `venv`, instalan dependencias, inicializan BD y ejecutan `app.py`; el banner de credenciales es legado. |
| `.github/workflows/ci.yml` | Compilación + build Docker. |
| `.github/workflows/keep-alive.yml` | Ping a Render cada 14 min. |

---

## 8. Convenciones del código

- Python sin type hints ni docstrings extensas; nombres en español para dominio y endpoints.
- SQL en mayúsculas; tablas en minúsculas y plural.
- Funciones de ruta pequeñas; validación inline.
- Mensajes flash en español.
- Plantillas con indentación de 4 espacios; CSS 2 espacios.
- Sin linter/formatter configurado (no hay `.flake8`, `ruff.toml`, `pyproject.toml`).

---

## 9. Puntos de extensión útiles

| Necesidad | Dónde tocar |
|---|---|
| Nuevo endpoint | `app/routes/*.py` + `create_app()` si es blueprint nuevo. |
| Nueva tabla | `ensure_schema()` + `database_setup.py`. |
| Nuevo filtro Jinja | `create_app()` → `app.jinja_env.filters`. |
| Nuevo global de plantilla | `create_app()` → `context_processor`. |
| Nuevo límite de rate | Decorar la ruta con `@limiter.limit(...)`. |
| Nuevo tipo de imagen | `ALLOWED_EXTENSIONS` + `ALLOWED_MIME_MAGIC`. |
| Nuevo estado de pedido | UI admin + endpoint + validación. |
| Cambiar tema | Variables `:root` en `style.css`. |

---

## 10. Trampas conocidas al modificar el código

1. Si añades un `POST`, **valida CSRF** (`validate_csrf()`); no hay protección automática.
2. Si añades una ruta de administración, usa `@admin_required`.
3. Si consultas PostgreSQL, recuerda que `?` se convierte a `%s` solo a través de `DatabaseConnection`.
4. `ensure_schema()` se ejecuta en cada request; no pongas operaciones costosas allí.
5. Las imágenes se guardan con el nombre del producto; dos productos con el mismo nombre se sobrescriben.
6. `request.referrer` puede ser `None`; usa fallback (ya se hace).
7. `session` no es un dict normal; los cambios en listas anidadas requieren reasignar (`session['cart'] = cart`).
8. Jinja autoescapa; cualquier HTML intencional debe marcarse explícitamente (y validarse).
9. El filtro `nl2br` actual no funciona como se espera.
10. En PostgreSQL, `fecha_creacion` es `datetime`, no `str`.

---

**Anterior:** [09 · Operación](09-operacion-mantenimiento.md) · **Siguiente:** [11 · Interfaz UI →](11-interfaz-ui.md)
