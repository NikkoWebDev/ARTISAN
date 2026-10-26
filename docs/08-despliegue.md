# 08 · Despliegue

## 1. Entornos y archivos

| Entorno | Entrada | Servidor | BD | Archivos |
|---|---|---|---|---|
| Desarrollo | `app.py` | Flask dev (`debug=False`) | SQLite | `.env` (no autoload) o variables del proceso |
| Producción Linux | `wsgi.py` | Gunicorn 4 workers | PostgreSQL o SQLite | Variables del entorno |
| Docker dev | `Dockerfile` | Gunicorn 4 workers | Según `DATABASE_URL` | `docker-compose.yml` + `.env.docker` |
| Docker prod | `Dockerfile.prod` | Gunicorn 4 workers | PostgreSQL 15 | `docker-compose.prod.yml` + `.env.docker` |
| Render | `wsgi.py` (buildpack) | Gunicorn | PostgreSQL (recomendado) | `keep-alive.yml` |

---

## 2. Variables de entorno

### 2.1 Requeridas en producción

| Variable | Ejemplo | Obligatoria | Secreto |
|---|---|---|---|
| `FLASK_ENV` | `production` | Sí (para activar cookies seguras) | No |
| `SECRET_KEY` | `64+ caracteres aleatorios` | Sí | **Sí** |
| `WHATSAPP_PHONE` | `573123580705` | Recomendada | No |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` | Sí si usas PostgreSQL | **Sí** |
| `RATELIMIT_STORAGE_URI` | `redis://...` | Recomendada en multi-worker | **Sí** (si incluye password) |

### 2.2 Solo inicialización

| Variable | Uso |
|---|---|
| `INITIAL_ADMIN_EMAIL` | Crear admin en `database_setup.py`. |
| `INITIAL_ADMIN_PASSWORD` | Contraseña inicial del admin. |

Después de crear el admin, elimínalas del entorno.

### 2.3 Opcionales / reservadas

| Variable | Estado |
|---|---|
| `SECRET` | Alternativa a `SECRET_KEY`. |
| `SQLITE_PATH` | Ruta del archivo SQLite. |
| `FLASK_DEBUG` | No leída por la app. |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Usadas por Compose actual; el contenedor Postgres **no** las interpreta. |
| `MAIL_*` | Sin implementación de correo. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Necesarias para la imagen oficial de PostgreSQL (ver §9). |

### 2.4 Generar secretos

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. Despliegue manual con Gunicorn

```bash
# 1. Código y entorno
git clone https://github.com/InmaWebDev/Artisan-Web.git
cd Artisan-Web
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Variables
export FLASK_ENV=production
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export WHATSAPP_PHONE="573123580705"
export DATABASE_URL="postgresql://artisan:clave@localhost:5432/artisan_db"
export INITIAL_ADMIN_EMAIL="admin@tudominio.com"
export INITIAL_ADMIN_PASSWORD="UnaClaveLargaYUnica!"

# 3. Esquema + admin (una sola vez)
python database_setup.py

# 4. Servir
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 wsgi:app
```

Reglas prácticas:

- `--workers`: `(2 × núcleos) + 1`, con mínimo 2.
- `--timeout 120`: margen para subidas de imágenes y conexiones lentas.
- No uses `app.py` en producción (servidor de desarrollo).
- No ejecutes Gunicorn como root.
- Usa un usuario con permisos de escritura solo en `static/img/productos/` y, si aplica, en `database.db`.

### 3.1 Systemd (ejemplo)

```ini
[Unit]
Description=Artisan Web
After=network.target

[Service]
User=artisan
Group=www-data
WorkingDirectory=/srv/artisan
EnvironmentFile=/etc/artisan.env
ExecStart=/srv/artisan/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now artisan
```

---

## 4. Nginx como reverse proxy

```nginx
server {
    listen 80;
    server_name artisan.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name artisan.example.com;

    ssl_certificate     /etc/letsencrypt/live/artisan.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/artisan.example.com/privkey.pem;

    client_max_body_size 16M;

    location /static/ {
        alias /srv/artisan/static/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

> La aplicación **no** usa `ProxyFix`. Sin él, `request.remote_addr` será `127.0.0.1` y el rate limiting se aplicará a todos los usuarios como si fueran uno. Añade:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

Solo activa `x_for=1` si Nginx es el único proxy delante.

---

## 5. Docker: desarrollo

### 5.1 Archivos

```text
Dockerfile              # python:3.11-slim + gcc + requirements + gunicorn
docker-compose.yml      # servicio web, puerto 5000, env_file .env.docker, volúmenes
.env.docker             # variables (incluye DATABASE_URL a Postgres)
```

`Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn
COPY . .
RUN mkdir -p static/img/productos logs
EXPOSE 5000
CMD ["sh", "-lc", "python database_setup.py && gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 wsgi:app"]
```

### 5.2 Comportamiento esperado

1. Construye la imagen.
2. Al arrancar, ejecuta `database_setup.py`.
3. Arranca Gunicorn en `:5000`.
4. Monta `static/img/productos` y `logs` desde el host.

### 5.3 ⚠️ Inconsistencia actual

`docker-compose.yml` no define un servicio `db`, pero `.env.docker` establece:

```env
DATABASE_URL=postgresql://artisan_user:...@db:5432/artisan_db
FLASK_ENV=production
```

Resultado: `database_setup.py` intenta conectar a `db:5432`, falla y el contenedor termina. **El comando `docker compose up --build` no funciona tal cual.**

### 5.4 Workaround para desarrollo con SQLite

Opción A — sobrescribir variables al vuelo:

```bash
docker compose run --rm \
  -e DATABASE_URL= \
  -e FLASK_ENV=development \
  -e SQLITE_PATH=/app/data/database.db \
  -v "$PWD/data:/app/data" \
  web python database_setup.py

docker compose run --rm \
  -e DATABASE_URL= \
  -e FLASK_ENV=development \
  -e SQLITE_PATH=/app/data/database.db \
  -v "$PWD/data:/app/data" \
  -p 5000:5000 web
```

Opción B — crear un compose de desarrollo propio:

```yaml
# docker-compose.dev.yml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: development
      SECRET_KEY: dev-secret-no-usar-en-produccion
      WHATSAPP_PHONE: "573123580705"
      SQLITE_PATH: /app/data/database.db
      INITIAL_ADMIN_EMAIL: admin@artisan.com
      INITIAL_ADMIN_PASSWORD: AdminDev123!
    volumes:
      - ./data:/app/data
      - ./static/img/productos:/app/static/img/productos
    restart: unless-stopped
```

```bash
docker compose -f docker-compose.dev.yml up --build
```

No se incluye en el repo; créalo si lo necesitas.

---

## 6. Docker: producción con PostgreSQL

### 6.1 Archivos

```text
Dockerfile.prod          # python:3.11-slim + build-essential + libpq-dev
docker-compose.prod.yml  # db (postgres:15) + web (Dockerfile.prod)
.env.docker              # variables compartidas
```

`Dockerfile.prod`:

- `ENV FLASK_ENV=production` y `PYTHONUNBUFFERED=1`.
- No ejecuta `database_setup.py`; el esquema se crea en la primera petición (`ensure_schema`).
- No crea el admin inicial.
- Gunicorn 4 workers en `:5000`.

### 6.2 Procedimiento recomendado

```bash
# 1. Configurar credenciales reales en .env.docker (ver §6.3)
# 2. Levantar
docker compose -f docker-compose.prod.yml up --build -d

# 3. Crear esquema y admin dentro del contenedor
docker compose -f docker-compose.prod.yml exec web python database_setup.py

# 4. Verificar
docker compose -f docker-compose.prod.yml ps
curl -I http://localhost:5000/index
docker compose -f docker-compose.prod.yml logs -f web
```

### 6.3 ⚠️ Inconsistencias actuales

1. **Credenciales de PostgreSQL:** la imagen oficial lee `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`. El compose pasa `DB_USER`, `DB_PASSWORD` y `DB_NAME`, que **ignora**. Si no defines `POSTGRES_PASSWORD`, el contenedor `db` falla al iniciar.
2. **`DATABASE_URL`:** usa `artisan_user`; debe coincidir con `POSTGRES_USER`.
3. **Sin healthcheck:** `depends_on: db` solo espera el arranque, no que Postgres acepte conexiones.
4. **Sin persistencia de uploads en Postgres:** las imágenes van a un volumen del host (`./static/img/productos`), correcto en un solo host; en clústeres necesita almacenamiento compartido.
5. **Admin no creado:** `Dockerfile.prod` no ejecuta `database_setup.py`.
6. **`SECRET_KEY` de ejemplo:** cámbiala.

Ejemplo corregido de `.env.docker`:

```env
# PostgreSQL
POSTGRES_USER=artisan_user
POSTGRES_PASSWORD=UnaClaveLargaYUnica!
POSTGRES_DB=artisan_db
DATABASE_URL=postgresql://artisan_user:UnaClaveLargaYUnica!@db:5432/artisan_db

# Flask
FLASK_ENV=production
SECRET_KEY=otra-cadena-aleatoria-de-64-caracteres
WHATSAPP_PHONE=573123580705
RATELIMIT_STORAGE_URI=memory://

# Solo para el primer setup
INITIAL_ADMIN_EMAIL=admin@tudominio.com
INITIAL_ADMIN_PASSWORD=OtraClaveLargaYUnica!
```

Y en `docker-compose.prod.yml` añadir healthcheck:

```yaml
  db:
    image: postgres:15
    env_file:
      - .env.docker
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    depends_on:
      db:
        condition: service_healthy
```

> `$${...}` evita que Compose interpole la variable en el archivo YAML.

### 6.4 Consideraciones de producción

- **No** uses `restart: unless-stopped` como única estrategia de alta disponibilidad.
- Configura un proxy TLS (Nginx/Traefik/Caddy) delante de `:5000`.
- Limita el acceso al puerto de Postgres (no lo publiques).
- Usa contraseñas fuertes y rotación.
- Programa backups de `postgres_data`.
- Si usas varios hosts, mueve uploads a S3/objeto y sesiones a un backend compartido.

---

## 7. Render

### 7.1 Workflow incluido

`.github/workflows/keep-alive.yml` hace ping cada 14 minutos a:

```text
https://artisan-web-52a0.onrender.com
```

Objetivo: evitar que el servicio gratuito de Render se duerma por inactividad (15 min). También puede lanzarse manualmente (`workflow_dispatch`).

Limitaciones:

- No crea ni configura el servicio; no hay `render.yaml`.
- Un `302` de `/` cuenta como actividad, pero no valida la salud real.
- El cron de GitHub puede retrasarse; no es un monitor.
- Si cambia la URL, actualiza el workflow.

### 7.2 Checklist de despliegue en Render

```text
[ ] Servicio web con runtime Python.
[ ] Build: pip install -r requirements.txt
[ ] Start: gunicorn --workers 4 --bind 0.0.0.0:$PORT --timeout 120 wsgi:app
[ ] Variables: FLASK_ENV=production, SECRET_KEY, WHATSAPP_PHONE, DATABASE_URL.
[ ] Base de datos PostgreSQL de Render (o externa).
[ ] Ejecutar database_setup.py una vez (job/shell).
[ ] Disco persistente para static/img/productos (o almacenamiento externo).
[ ] HTTPS (Render lo provee) y cookies Secure.
[ ] Verificar /index y el flujo de compra.
```

> El disco de Render es efímero por defecto: las imágenes subidas se pierden en cada redeploy. Usa un disco persistente o un bucket externo. SQLite también es efímero y no sirve para producción en Render.

---

## 8. CI/CD

`.github/workflows/ci.yml` se ejecuta en `push` y `pull_request` a `main`:

| Job | Pasos |
|---|---|
| `checks` | Python 3.11, instala `requirements.txt` + `dev-requirements.txt`, compila todos los `.py` con `py_compile` (excluye `__MACOSX`, sample y `.venv`). |
| `docker-build` | Construye `Dockerfile.prod` con `docker/build-push-action@v4` (`load: true`), sin publicar. |

Lo que **no** hace:

- No ejecuta tests (no hay suite).
- No analiza lint, tipos ni seguridad.
- No publica imágenes.
- No despliega.

Mejoras sugeridas:

```yaml
- name: Tests
  run: pytest -q
- name: Lint
  run: ruff check .
- name: Audit
  run: pip-audit
- name: Push image
  if: github.ref == 'refs/heads/main'
  uses: docker/build-push-action@v4
  with:
    push: true
    tags: ghcr.io/${{ github.repository }}:latest
```

---

## 9. Problemas conocidos de Docker

Resumen de bloqueos conocidos:

| # | Problema | Archivo | Impacto | Corrección |
|---|---|---|---|---|
| 1 | Dev compose apunta a un `db` inexistente | `docker-compose.yml` + `.env.docker` | El contenedor no arranca. | Quitar `DATABASE_URL` o añadir `db`. |
| 2 | Postgres ignora `DB_*` | `docker-compose.prod.yml` | `db` no inicia sin `POSTGRES_PASSWORD`. | Usar `POSTGRES_*`. |
| 3 | `DATABASE_URL` no coincide con usuario | `.env.docker` | Error de autenticación. | Alinear usuario/clave/DB. |
| 4 | Sin healthcheck | `docker-compose.prod.yml` | Carrera al arrancar. | `condition: service_healthy`. |
| 5 | Admin no creado en prod | `Dockerfile.prod` | No se puede entrar al panel. | Ejecutar setup o crear admin manualmente. |
| 6 | Secretos de ejemplo | `.env.docker` | Riesgo si se usan. | Rotar. |
| 7 | Sin `ProxyFix` | `app/__init__.py` | Rate limit global y URLs mal generadas tras proxy. | Añadir middleware. |

Hasta corregirlos, usa el despliegue manual con Gunicorn (§3) o el workaround de §5.4.

---

## 10. Proceso de release

```text
1. Actualizar CHANGELOG.md y la versión.
2. Ejecutar comprobaciones locales (py_compile, flujo manual).
3. Backup de BD y de static/img/productos.
4. Construir imagen/tag o hacer merge a main.
5. Ejecutar database_setup.py si hay cambios de esquema.
6. Desplegar.
7. Smoke test:
   - GET /index → 200
   - GET /admin/ sin sesión → 302 /login
   - login admin → 200 /index
   - crear/editar producto de prueba
   - carrito + checkout → pedido en admin
8. Revisar logs y 429/500.
9. Anunciar/etiquetar.
```

### Rollback

- **Código:** volver al commit/tag anterior y redeploy.
- **BD:** restaurar backup solo si la migración es incompatible; `ensure_schema` no revierte cambios.
- **Imágenes:** el volumen no se ve afectado por el rollback de código.
- **Sesiones:** si cambia `SECRET_KEY`, todos los usuarios deberán volver a iniciar sesión.

---

## 11. Escalado y límites

| Componente | Estado | Cuello de botella |
|---|---|---|
| Gunicorn | 4 workers | CPU en imágenes/SSL; memoria baja. |
| Sesiones | Cookie firmada | No requiere afinidad; límite de 4 KB. |
| Carrito | Sesión | No compartido entre dispositivos. |
| Rate limit | Memoria por worker | No compartido; usar Redis. |
| SQLite | Archivo | Un escritor a la vez; no apto para múltiples hosts. |
| Uploads | Disco local | No compartido; usar objeto/CDN. |
| BD | PostgreSQL | Conexiones por worker; considerar pool. |
| Imágenes | 8–11 MB por archivo | Ancho de banda y tiempos de carga; optimizar. |

---

## 12. Monitoreo mínimo

- Códigos 5xx y 4xx en logs del proxy.
- Errores 429 (rate limit).
- Espacio en disco (`static/img/productos`, `database.db`, `postgres_data`).
- Tiempo de respuesta de `/index`.
- Crecimiento de `pedidos` y de imágenes.
- Estado de backups.

No hay endpoint `/health`; puedes usar `/index` o `/static/css/style.css`.

---

**Anterior:** [07 · Seguridad](07-seguridad.md) · **Siguiente:** [09 · Operación →](09-operacion-mantenimiento.md)
