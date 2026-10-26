# 07 · Seguridad

> Análisis basado en el código del commit `dfeec6d`. No sustituye una auditoría profesional. Las severidades son orientativas.

---

## 1. Resumen ejecutivo

La aplicación implementa lo esencial: contraseñas hasheadas, CSRF en formularios, control de rol, consultas parametrizadas, validación de uploads y cookies seguras en producción. Es adecuada para una tienda pequeña **si se despliega con HTTPS, una `SECRET_KEY` fuerte y las correcciones de la sección 6**.

Los riesgos más relevantes son:

1. **`SECRET_KEY` por defecto** si `FLASK_ENV` no es exactamente `production` (permite falsificar sesiones).
2. **Rate limiting en memoria por worker** y sin `ProxyFix`, lo que lo hace ineficaz o global detrás de un proxy.
3. **Ausencia de cabeceras de seguridad** (CSP, HSTS, `X-Frame-Options`, etc.).
4. **Sesión no regenerada al iniciar sesión** (session fixation).
5. **Contraseñas de ejemplo en `.env.docker`** que deben cambiarse.

---

## 2. Controles implementados

| Control | Implementación | Archivo |
|---|---|---|
| Hash de contraseñas | `generate_password_hash` / `check_password_hash` (scrypt). | `auth.py`, `database_setup.py` |
| CSRF | Token de 32 bytes en sesión; validación manual en cada `POST`. | `app/csrf.py`, `__init__.py` |
| Autorización | `@admin_required`, `@cart_required`. | `admin.py`, `cart.py` |
| SQL injection | Consultas parametrizadas (`?` → `%s`). | todas las rutas |
| XSS | Autoescape de Jinja2 activado por defecto. | plantillas |
| Uploads | Extensión permitida + firma binaria + `secure_filename`. | `admin.py` |
| Tamaño de request | `MAX_CONTENT_LENGTH = 16 MB`. | `config.py` |
| Rate limiting | 200/día y 50/hora por IP. | `extensions.py` |
| Cookies en producción | `Secure`, `HttpOnly`, `SameSite=Lax`. | `config.py` |
| Secreto en producción | `RuntimeError` si falta `SECRET_KEY`. | `config.py` |
| Debug | `debug=False` en `app.py` y `wsgi.py`. | entradas |
| Total del carrito | Recalculado desde BD en checkout. | `cart.py` |
| Subproductos en carrito | Bloqueados con `parent_id IS NULL`. | `cart.py` |
| Mensajes WhatsApp | Codificados con `quote()` / `encodeURIComponent`. | `cart.py`, `producto.html` |
| Imágenes | Se sirven como estáticos; no se ejecutan. | Flask static |

---

## 3. Modelo de amenazas

| Activo | Actor | Vector | Control actual | Riesgo residual |
|---|---|---|---|---|
| Cuentas de usuario | Atacante remoto | Fuerza bruta / credential stuffing | Rate limit global | Sin lockout ni 2FA; límite débil. |
| Sesión | Atacante remoto | Robo de cookie / fijación | `HttpOnly`, `Secure` en prod | Sin rotación al login; sin expiración corta. |
| Panel admin | Usuario malicioso | Escalada de privilegios | Rol en sesión | No se revalida el rol en BD. |
| Pedidos | Atacante | Manipulación de precios en sesión | Recalculo desde BD | Correcto. |
| Pedidos | Atacante | CSRF en checkout | Token | Correcto. |
| Imágenes | Admin comprometido | Upload de archivo malicioso | Whitelist + magic bytes | Polyglots, RIFF no verificado, nombre predecible. |
| BD | Atacante | Inyección SQL | Parámetros | Correcto. |
| Secretos | Atacante | Repositorio / env expuesto | `.gitignore` | `.env.docker` con placeholders. |
| Disponibilidad | Atacante | Flood | Rate limit | En memoria, por worker, sin proxy fix. |
| Usuarios | Tercero | Clickjacking | — | Sin `X-Frame-Options`/CSP. |
| Datos en tránsito | Intermediario | HTTP sin TLS | Cookies Secure en prod | Sin HSTS ni redirección HTTPS en la app. |

---

## 4. Hallazgos detallados

### 4.1 🔴 `SECRET_KEY` por defecto (alta)

```python
SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SECRET', 'artisan_key_2026')
```

- Solo se exige en `FLASK_ENV=production`.
- Si se despliega en Render/Heroku/VM sin `FLASK_ENV=production` y sin `SECRET_KEY`, se usa una clave pública conocida.
- Con la clave, un atacante puede **firmar cookies de sesión** y asumir `rol='admin'`.

**Mitigación:** generar una clave aleatoria, definirla siempre, y fallar el arranque si es el valor por defecto.

```python
if not os.environ.get('SECRET_KEY') or os.environ['SECRET_KEY'] == 'artisan_key_2026':
    raise RuntimeError('Define un SECRET_KEY aleatorio.')
```

### 4.2 🟠 Rate limiting ineficaz detrás de proxy (media)

```python
limiter = Limiter(key_func=get_remote_address, default_limits=['200 per day', '50 per hour'])
```

- `get_remote_address` usa `request.remote_addr`.
- Detrás de Nginx/Render, `remote_addr` es el proxy: **todos los usuarios comparten el límite**.
- Con 4 workers de Gunicorn, cada worker tiene su propio contador en memoria: el límite efectivo se multiplica por 4.
- 50 peticiones/hora es bajo para un catálogo con varias páginas.

**Mitigación:**

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

Y usar un backend compartido:

```env
RATELIMIT_STORAGE_URI=redis://localhost:6379/0
```

Además, aplicar límites específicos a login/registro:

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login(): ...
```

### 4.3 🟠 Sin cabeceras de seguridad (media)

No se envían `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` ni `Strict-Transport-Security`. La página puede embeberse en un iframe (clickjacking) y no hay defensa en profundidad contra XSS.

**Mitigación:**

```python
@app.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    resp.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'"
    )
    return resp
```

> Requiere ajustar `script-src` porque hay JavaScript inline; a medio plazo, externalizar los scripts y eliminar `'unsafe-inline'`.

### 4.4 🟠 Session fixation (media)

En `login()` se actualiza la sesión pero no se destruye ni se genera un nuevo identificador:

```python
session.update({'user_id': ..., 'rol': ..., 'nombre': ...})
session.permanent = True
```

**Mitigación:** limpiar la sesión (conservando el carrito si se desea) y regenerar el token CSRF tras autenticar.

### 4.5 🟠 Contraseñas de ejemplo en `.env.docker` (media)

```env
DB_PASSWORD=CambiarContraseñaSegura123!
SECRET_KEY=tu_clave_secreta_cambiar_en_produccion_1234567890abcdef
INITIAL_ADMIN_PASSWORD=AdminDockerPass123!
```

Son placeholders, pero si se usan tal cual en producción, las credenciales son públicas. **Cambiar todas antes de desplegar** y no versionar `.env`.

### 4.6 🟠 Logout por GET (media/baja)

`GET /logout` no valida CSRF. Un enlace o imagen puede cerrar la sesión del usuario (CSRF de logout). Impacto bajo, pero es una mala práctica.

**Mitigación:** convertir a `POST` con token CSRF.

### 4.7 🟡 Validación de uploads incompleta (media/baja)

```python
magic = file.read(4)
for sig, exts in ALLOWED_MIME_MAGIC.items():
    if magic.startswith(sig) and ext in exts:
        return ext
```

- `RIFF` solo comprueba los 4 primeros bytes; un AVI renombrado a `.webp` pasaría.
- No se valida la estructura completa de la imagen ni se re-encodea.
- El nombre se deriva del nombre del producto (`<nombre>_1.jpg`): predecible y propenso a colisiones/sobrescritura.
- No se eliminan imágenes al borrar productos.
- `img1` es obligatoria en HTML, pero el backend acepta productos sin imagen.

**Mitigación:** validar con Pillow, re-encodear a JPEG/WebP, limitar dimensiones, usar UUID como nombre, borrar huérfanas y servir desde un dominio/CDN separado.

### 4.8 🟡 Rol de sesión no revalidado (baja)

`admin_required` confía en `session['rol']`. Si a un usuario se le quita el rol en la BD, su sesión sigue siendo admin hasta que caduque (31 días por defecto).

**Mitigación:** consultar el rol en BD en cada request administrativo o usar sesiones cortas.

### 4.9 🟡 `parent_id` sin validación (baja)

`add_product`/`edit_product` aceptan cualquier `parent_id`, incluido el propio producto, uno inexistente o un subproducto. Puede generar datos inconsistentes y ciclos lógicos.

**Mitigación:** validar existencia, que sea principal y que `parent_id != id`; añadir FK.

### 4.10 🟡 Categorías y productos sin integridad referencial (baja)

`productos.categoria` es texto libre y no hay FK a `categorias`. Borrar/renombrar una categoría deja productos con categorías inexistentes.

**Mitigación:** `categoria_id` con FK y `ON DELETE RESTRICT`/`SET NULL`.

### 4.11 🟡 Colisión de número de orden (baja)

`numero_orden = f"ORD-{int(time.time())}"` colisiona si dos pedidos se crean en el mismo segundo. La restricción UNIQUE hace fallar el segundo con un error genérico.

**Mitigación:** UUID, `secrets.token_hex`, o secuencia de BD.

### 4.12 🟡 Sin política de contraseñas robusta (baja)

Mínimo 6 caracteres, sin complejidad, sin verificación contra filtraciones, sin cambio/reseteo. El registro no valida formato de correo en servidor.

**Mitigación:** mínimo 8–12, `zxcvbn`/HaveIBeenPwned, verificación de email, flujo de reseteo con token de un solo uso.

### 4.13 🟡 Comparación de CSRF no constante (baja)

```python
if not token or token != session.get('csrf_token'):
```

La comparación no es de tiempo constante. Con tokens de 256 bits el riesgo práctico es despreciable, pero se recomienda `secrets.compare_digest`.

### 4.14 🟡 Sin logs ni auditoría (baja)

No hay registro de inicios de sesión, fallos, cambios de productos ni pedidos. Dificulta investigar incidentes.

**Mitigación:** logging estructurado + auditoría en BD.

### 4.15 ℹ️ Contenido de la base incluida

`database.db` contiene hashes de contraseña (Admin/Tester) y un pedido de prueba. Si el ZIP se comparte, considera eliminarla o rotar credenciales. Los hashes son scrypt, pero la contraseña del admin de pruebas podría ser débil.

### 4.16 ℹ️ Dependencias

No hay `pip-audit`, Dependabot ni Renovate. Flask 3.0.0, Werkzeug 3.0.1 y Flask-Limiter 2.9.0 son versiones de 2023–2024. Revisa vulnerabilidades conocidas antes de desplegar.

---

## 5. Fortalezas a mantener

- No se almacenan contraseñas en texto plano.
- No se concatena entrada de usuario en SQL.
- Los precios del checkout se leen de la BD.
- Los subproductos no pueden comprarse directamente.
- Jinja2 autoescapa nombres, descripciones y mensajes.
- El token CSRF es aleatorio y de 256 bits.
- `secure_filename` impide path traversal en uploads.
- `debug=False` por defecto en los puntos de entrada.
- Cookies `Secure`/`HttpOnly`/`SameSite` en producción.
- Rate limiting presente (aunque mejorable).

---

## 6. Checklist de endurecimiento

### Antes de publicar

```text
[ ] SECRET_KEY aleatoria (>= 32 bytes) y distinta por entorno.
[ ] FLASK_ENV=production en el servidor.
[ ] HTTPS terminado en proxy; HSTS activado.
[ ] Eliminar o cambiar credenciales de .env.docker.
[ ] Verificar que .env no está en Git.
[ ] ProxyFix configurado si hay proxy.
[ ] RATELIMIT_STORAGE_URI con Redis (o similar) si hay más de un worker.
[ ] Copia de seguridad de la BD y de static/img/productos.
[ ] Cambiar contraseña del admin inicial.
[ ] Revisar dependencias con pip-audit.
[ ] Probar login, carrito, checkout y admin en el entorno real.
```

### Mejoras recomendadas (prioridad)

| Prioridad | Acción |
|---|---|
| Alta | Fallar el arranque si `SECRET_KEY` es el valor por defecto. |
| Alta | `ProxyFix` + límites específicos para login. |
| Alta | Cabeceras de seguridad y CSP. |
| Media | Regenerar sesión al autenticar; logout por POST. |
| Media | Redis para rate limiting. |
| Media | UUID para nombres de archivo + validación con Pillow. |
| Media | Validar `parent_id` y categorías con FK. |
| Media | Logs de acceso y auditoría. |
| Baja | `compare_digest` para CSRF. |
| Baja | Política de contraseñas y reseteo. |
| Baja | 2FA para administradores. |
| Baja | Revalidar rol en BD por request. |

---

## 7. Configuración segura de ejemplo

```python
# app/config.py (ejemplo de endurecimiento)
import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12  # 12 horas
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
```

> Un `SECRET_KEY` aleatorio en cada arranque invalida las sesiones al reiniciar; en producción debe ser fijo y secreto. La línea anterior es solo para desarrollo.

---

## 8. Divulgación responsable

Si encuentras una vulnerabilidad:

1. No la publiques en issues públicos.
2. Contacta al mantenedor del repositorio (`InmaWebDev/Artisan-Web`).
3. Incluye impacto, pasos de reproducción y versión/commit.
4. Da un plazo razonable antes de divulgarla.

---

**Anterior:** [06 · WhatsApp](06-whatsapp.md) · **Siguiente:** [08 · Despliegue →](08-despliegue.md)
