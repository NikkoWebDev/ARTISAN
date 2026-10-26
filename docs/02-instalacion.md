# 02 · Instalación y ejecución local

## 1. Requisitos

| Requisito | Versión recomendada | Notas |
|---|---|---|
| Python | 3.11 (CI) o 3.13 (entorno local observado) | `requirements.txt` fija Flask 3.0. |
| pip | Incluido con Python | |
| SQLite | Incluido en Python | Motor por defecto. |
| PostgreSQL | 15 (opcional) | Solo si usas `DATABASE_URL` con prefijo `postgres`. |
| Docker + Compose | Opcional | Ver limitaciones en [08-despliegue](08-despliegue.md#9-problemas-conocidos-de-docker). |
| Gunicorn | Incluido en `requirements.txt` | Producción Linux. |

No se necesita Node.js: el frontend es HTML/CSS/JS estático.

---

## 2. Instalación paso a paso (Windows)

```powershell
cd "C:\Users\57312\Documents\Artisan Web"

# Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
cd artisan
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Los scripts `run.bat` y `run.sh` crean un entorno llamado `venv` (sin punto), no `.venv`. Ambos enfoques funcionan; no los mezcles.

---

## 3. Variables de entorno

### 3.1 El detalle importante: `.env` no se carga solo

`python-dotenv` figura en `requirements.txt`, pero **ningún módulo ejecuta `load_dotenv()`**. Por tanto:

- Copiar `.env.example` a `.env` **no** basta para `python app.py`.
- La aplicación lee variables del **entorno del proceso**.
- Docker sí las inyecta mediante `env_file`.
- Alternativa local: usar el CLI de python-dotenv.

```powershell
# Opción A: exportar en la sesión de PowerShell
$env:SECRET_KEY = "cadena-larga-aleatoria"
$env:WHATSAPP_PHONE = "573123580705"
$env:INITIAL_ADMIN_EMAIL = "admin@artisan.com"
$env:INITIAL_ADMIN_PASSWORD = "UnaClaveSegura123!"

# Opción B: usar .env con el CLI (python-dotenv instalado)
copy .env.example .env
# editar .env
dotenv run -- python app.py
```

```bash
# Linux / macOS
export SECRET_KEY="cadena-larga-aleatoria"
export WHATSAPP_PHONE="573123580705"
```

### 3.2 Variables leídas por la aplicación

| Variable | Dónde se lee | Efecto |
|---|---|---|
| `SECRET_KEY` / `SECRET` | `app/config.py` | Firma de sesión y CSRF. Si falta, usa `artisan_key_2026`. |
| `WHATSAPP_PHONE` | `app/__init__.py` | Número destino. Se limpia `+` y espacios. |
| `DATABASE_URL` | `db_utils.py` | Si empieza por `postgres`, usa PostgreSQL. |
| `SQLITE_PATH` | `db_utils.py` | Ruta del archivo SQLite (por defecto `database.db`). |
| `FLASK_ENV` | `app/config.py` | `production` activa cookies seguras y exige `SECRET_KEY`. |
| `RATELIMIT_STORAGE_URI` | `app/config.py` | Backend de límites (`memory://` por defecto). |
| `INITIAL_ADMIN_EMAIL` | `database_setup.py` | Crea admin inicial. |
| `INITIAL_ADMIN_PASSWORD` | `database_setup.py` | Contraseña del admin inicial. |

No se leen: `FLASK_DEBUG`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `MAIL_*`. Estas últimas aparecen en archivos de ejemplo o Compose, pero la app no las usa directamente.

### 3.3 Generar una `SECRET_KEY`

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 4. Inicializar la base de datos

```bash
python database_setup.py
```

El script:

1. Se conecta al motor configurado (`DATABASE_URL` o SQLite).
2. Ejecuta `ensure_schema()`: crea `usuarios`, `categorias`, `productos`, `pedidos` y aplica columnas nuevas si faltan.
3. Si existen `INITIAL_ADMIN_EMAIL` y `INITIAL_ADMIN_PASSWORD`, inserta un usuario con rol `admin`.
4. Inserta las categorías base `Bisutería` y `Marroquinería` con `INSERT OR IGNORE`.
5. Hace `commit()` e imprime `Base de datos lista.`.

Salida esperada:

```text
Base de datos lista.
```

Si ejecutas el script dos veces, no duplica categorías ni el admin en SQLite (`INSERT OR IGNORE`). En PostgreSQL el `INSERT OR IGNORE` se transforma en `INSERT`; el duplicado lanza una excepción que el script silencia con `except Exception: pass`.

> Para un entorno limpio: elimina `database.db` y vuelve a ejecutar el script.

---

## 5. Ejecutar la aplicación

### 5.1 Servidor de desarrollo

```bash
python app.py
```

- Escucha en `http://127.0.0.1:5000` (Flask por defecto).
- `debug=False`: no hay recarga automática.
- Para depurar con recarga, usa el CLI de Flask:

```bash
flask --app app run --debug --reload
```

> `flask --app app` importa `app.py` y busca `app`. Como `app.py` define `app = create_app()`, funciona.

### 5.2 Producción local con Gunicorn (Linux/macOS)

```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 wsgi:app
```

En Windows, Gunicorn no funciona de forma nativa; usa WSL, Docker o `waitress` (no incluido).

### 5.3 Cambiar el puerto

`app.py` llama `app.run(debug=False)` sin puerto. Para cambiarlo:

```python
# app.py
app.run(host="0.0.0.0", port=8000, debug=False)
```

En Gunicorn: `--bind 0.0.0.0:8000`.

---

## 6. Docker

### 6.1 Intento rápido

```bash
docker compose up --build
```

Antes de usarlo en serio, revisa [08-despliegue §9](08-despliegue.md#9-problemas-conocidos-de-docker): la configuración incluida tiene inconsistencias entre `.env.docker`, el compose de desarrollo y el de producción.

### 6.2 Construcción manual

```bash
docker build -t artisan .
docker run --rm -p 5000:5000 \
  -e SECRET_KEY="cadena-larga" \
  -e WHATSAPP_PHONE="573123580705" \
  -e SQLITE_PATH=/app/data/database.db \
  -v "$PWD/data:/app/data" \
  -v "$PWD/static/img/productos:/app/static/img/productos" \
  artisan
```

En PowerShell, sustituye `$PWD` por `${PWD}` y usa backticks para continuar líneas.

---

## 7. Verificación posterior a la instalación

```text
[ ] /index responde 200 y muestra categorías.
[ ] /lineaproductos responde 200.
[ ] /registro crea un usuario y redirige a /login.
[ ] /login inicia sesión y redirige a /index.
[ ] /admin/ redirige a /login si no eres admin.
[ ] /admin/ responde 200 con un usuario admin.
[ ] Se puede crear una categoría.
[ ] Se puede crear un producto con 1 imagen.
[ ] El producto aparece en /lineaproductos.
[ ] Se puede agregar al carrito y ver /carrito.
[ ] El checkout redirige a api.whatsapp.com y crea un registro en pedidos.
[ ] /logout cierra la sesión.
```

Consulta también la sección de [pruebas](09-operacion-mantenimiento.md#4-pruebas).

---

## 8. Estructura de archivos generada en tiempo de ejecución

| Archivo/carpeta | Origen | ¿Versionar? |
|---|---|---|
| `database.db` | SQLite | No (`.gitignore`). |
| `static/img/productos/*` | Subidas del admin | No (`.gitignore`). |
| `__pycache__/`, `*.pyc` | Python | No. |
| `.venv/`, `venv/` | Entorno virtual | No. |
| `logs/` | Docker (volumen) | No. |

---

## 9. Problemas frecuentes de instalación

| Síntoma | Causa probable | Solución |
|---|---|---|
| `RuntimeError: SECRET_KEY is required in production` | `FLASK_ENV=production` sin `SECRET_KEY`. | Define `SECRET_KEY` o usa `FLASK_ENV=development`. |
| El login no persiste en producción local | `SESSION_COOKIE_SECURE=True` exige HTTPS. | Usa HTTPS o `FLASK_ENV=development` en local. |
| No aparece el admin | No ejecutaste `database_setup.py` con `INITIAL_ADMIN_*`. | Exporta variables y vuelve a ejecutar el script. |
| `ModuleNotFoundError: No module named 'flask'` | Entorno virtual no activado. | Activa `.venv` o instala dependencias. |
| `sqlite3.OperationalError: no such table` | No se inicializó la BD y `ensure_schema` falló. | Ejecuta `python database_setup.py`; revisa permisos de escritura. |
| `psycopg2-binary is required` | `DATABASE_URL` postgres sin driver. | `pip install psycopg2-binary`. |
| La app no ve `.env` | No se llama `load_dotenv()`. | Exporta variables o usa `dotenv run`. |
| Imágenes no visibles | `imagen_url` relativa o ruta incorrecta. | Revisa la ruta en BD; debe empezar por `/static/...`. |

Más casos en [09-operacion-mantenimiento.md](09-operacion-mantenimiento.md#8-troubleshooting).

---

**Anterior:** [01 · Arquitectura](01-arquitectura.md) · **Siguiente:** [03 · Base de datos →](03-base-de-datos.md)
