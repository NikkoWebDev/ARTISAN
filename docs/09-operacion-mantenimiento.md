# 09 · Operación y mantenimiento

## 1. Runbook rápido

| Tarea | Comando |
|---|---|
| Arrancar en desarrollo | `python app.py` |
| Arrancar en producción | `gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 wsgi:app` |
| Inicializar/reparar BD | `python database_setup.py` |
| Compilar sintaxis | `python -m py_compile app.py wsgi.py database_setup.py db_utils.py app/*.py app/routes/*.py` |
| Ver rutas | script con `app.url_map` (ver [04-rutas §8](04-rutas.md#8-cómo-inspeccionar-las-rutas)) |
| Backup SQLite | `sqlite3 database.db ".backup 'backups/database.db'"` |
| Backup PostgreSQL | `pg_dump "$DATABASE_URL" -Fc -f backups/artisan.dump` |
| Ver logs Docker | `docker compose logs -f web` |
| Reiniciar Docker | `docker compose restart web` |
| Ver estado | `docker compose ps` |

---

## 2. Rutinas de mantenimiento

### Diario

```text
[ ] Revisar que el sitio responde (GET /index = 200).
[ ] Revisar pedidos nuevos en /admin/.
[ ] Revisar logs de 500/429.
[ ] Confirmar que los backups programados se ejecutaron.
```

### Semanal

```text
[ ] Backup completo (BD + static/img/productos).
[ ] Revisar espacio en disco.
[ ] Revisar imágenes huérfanas o duplicadas.
[ ] Revisar intentos de login fallidos (si hay logs).
[ ] Probar el flujo de compra de punta a punta.
```

### Mensual

```text
[ ] Actualizar dependencias y revisar CVEs (pip-audit).
[ ] Rotar credenciales si corresponde.
[ ] Revisar crecimiento de pedidos y productos.
[ ] Verificar restauración de un backup en un entorno de prueba.
[ ] Revisar el checklist de seguridad (07-seguridad.md).
```

---

## 3. Backups

### 3.1 SQLite

```bash
mkdir -p backups
sqlite3 database.db ".backup 'backups/database-$(date +%Y%m%d).db'"
# Verificar
sqlite3 backups/database-20261025.db "PRAGMA integrity_check;"
```

Copia también `static/img/productos/`. Un backup de BD sin imágenes deja productos con imágenes rotas.

### 3.2 PostgreSQL

```bash
pg_dump "$DATABASE_URL" --format=custom --file="backups/artisan-$(date +%F).dump"
pg_restore --list backups/artisan-2026-10-25.dump | head
```

Restaurar:

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" backups/artisan-2026-10-25.dump
```

### 3.3 Retención sugerida

| Frecuencia | Retención |
|---|---|
| Diaria | 7 días |
| Semanal | 4 semanas |
| Mensual | 12 meses |

Guarda los backups fuera del servidor y cifrados si contienen datos personales.

---

## 4. Pruebas

### 4.1 Estado actual

- No hay suite `pytest` ni tests automatizados en el repositorio.
- `dev-requirements.txt` incluye `pytest` y `requests`, pero no se usa en CI.
- `CI` solo compila archivos y construye la imagen.
- `e2e_test.py` es un script **legado** que no funciona contra la versión actual.

### 4.2 Por qué falla `e2e_test.py`

| Línea | Problema |
|---|---|
| `s.post('/registro', ...)` sin `csrf_token` | El servidor rechaza el POST y no crea el usuario. |
| `s.get('/carrito/add/1')` | La ruta es solo `POST`; devuelve `405`. |
| `s.post('/carrito/checkout')` sin CSRF | Redirige al carrito sin crear pedido. |
| No mantiene el token CSRF | Ningún formulario pasa la validación. |

### 4.3 Prueba manual completa (smoke test)

```text
1.  GET /index                       → 200, categorías visibles.
2.  GET /lineaproductos              → 200, productos visibles.
3.  GET /producto/1                  → 200 o redirección si no existe.
4.  GET /registro                    → 200.
5.  POST /registro (válido + CSRF)   → 302 /login.
6.  POST /login (credenciales)       → 302 /index.
7.  POST /carrito/add/1              → 302, carrito con 1 ítem.
8.  GET /carrito                     → 200, total correcto.
9.  POST /carrito/update/1           → cantidad actualizada.
10. POST /carrito/checkout           → 302 api.whatsapp.com.
11. Verificar pedido en /admin/      → aparece con estado pendiente.
12. POST /carrito/remove/1           → ítem eliminado.
13. POST /carrito/clear              → carrito vacío.
14. GET /admin/ (admin)              → 200.
15. POST /admin/cat/add              → categoría creada.
16. POST /admin/add_prod (con foto)  → producto creado.
17. GET /admin/prod/edit/<id>        → formulario.
18. POST /admin/prod/edit/<id>       → actualizado.
19. POST /admin/prod/del/<id>        → eliminado.
20. GET /logout                      → sesión cerrada.
```

### 4.4 Prueba de seguridad mínima

```text
[ ] POST /login sin csrf_token → no autentica.
[ ] POST /admin/add_prod sin sesión → 302 /login.
[ ] POST /admin/add_prod como cliente → 302 /login.
[ ] GET /carrito sin sesión → 302 /login.
[ ] GET /admin/ como cliente → 302 /login.
[ ] Subir archivo .php renombrado a .jpg → rechazado.
[ ] Subir archivo > 16 MB → 413.
[ ] Manipular precio en session['cart'] → checkout usa el precio de BD.
[ ] Acceder a /producto/<id> inexistente → redirección, no 500.
```

### 4.5 Pruebas automatizadas sugeridas

```python
# tests/test_smoke.py (no incluido)
def test_index(client):
    assert client.get('/index').status_code == 200

def test_admin_requires_login(client):
    r = client.get('/admin/')
    assert r.status_code == 302
    assert '/login' in r.headers['Location']

def test_checkout_recalculates_total(auth_client, product):
    auth_client.post(f'/carrito/add/{product}', data={'cantidad': 2, 'csrf_token': token})
    ...
```

Para testear CSRF necesitas extraer el token de la sesión (`client.session_transaction()`) o desactivar la validación en un fixture.

---

## 5. Logs

### 5.1 Estado actual

- No hay configuración de `logging`.
- Gunicorn escribe a stdout/stderr.
- Flask en `debug=False` no muestra trazas al usuario.
- Las excepciones de BD se silencian con `flash` genérico en varias rutas, lo que dificulta el diagnóstico.

### 5.2 Recomendación

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/artisan.log', maxBytes=5_000_000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

Y registrar eventos clave:

- Login fallido/éxitos.
- Altas/bajas/ediciones de productos.
- Checkout y número de orden.
- Errores 500 con `app.logger.exception`.

---

## 6. Performance

| Punto | Observación | Mejora |
|---|---|---|
| Imágenes | Hay archivos de 8–11 MB; se sirven completos. | Redimensionar, comprimir, WebP y thumbnails. |
| `cache_buster()` | Calcula `mtime` de CSS por request. | Cachear el valor en memoria. |
| Catálogo | Sin paginación. | `LIMIT/OFFSET`. |
| Consultas | Sin índices adicionales. | Índices en `categoria`, `parent_id`, `usuario_id`, `fecha_creacion`. |
| Conexiones | Una por request/worker. | Pool en PostgreSQL. |
| Rate limit | Contador por worker. | Redis. |
| Fuentes | Google Fonts externo. | Auto-hospedar o `font-display: swap` (ya está en la URL). |
| Sesión | Cookie con carrito. | Carrito en BD si crece. |
| Estáticos | Sin CDN. | CDN/objeto. |

---

## 7. Problemas conocidos (deuda técnica)

| # | Problema | Impacto | Estado / workaround |
|---|---|---|---|
| 1 | `.env` no se carga automáticamente | Configuración confusa | Exportar variables o `dotenv run`. |
| 2 | Docker dev apunta a `db` inexistente | No arranca | Ver [08 §5.4](08-despliegue.md#54-workaround-para-desarrollo-con-sqlite). |
| 3 | Docker prod no usa `POSTGRES_*` | `db` no inicia | Ver [08 §9](08-despliegue.md#9-problemas-conocidos-de-docker). |
| 4 | Admin no se crea en Docker prod | Sin acceso al panel | Ejecutar `database_setup.py` dentro del contenedor. |
| 5 | `fecha_creacion` falla en admin con PostgreSQL | 500 en `/admin/` | Convertir a string en Python/Jinja. |
| 6 | `nl2br` escapa `<br>` | Saltos de línea visibles como `&lt;br&gt;` | Devolver `Markup` con el texto escapado. |
| 7 | Migración SQLite con `CURRENT_TIMESTAMP` | Falla en BD antiguas | Recrear columna/tabla. |
| 8 | `e2e_test.py` obsoleto | Falsa alarma en CI/manual | Actualizar o eliminar. |
| 9 | Sin cambio de estado de pedidos | No se confirma/cancela | Implementar endpoint + UI. |
| 10 | Sin historial de pedidos del cliente | Mala experiencia | Añadir `/mis-pedidos`. |
| 11 | Sin stock | Sobreventa | Añadir inventario y reservas. |
| 12 | Sin borrado de imágenes | Disco crece | Hook de borrado. |
| 13 | `parent_id` sin validar | Datos inconsistentes | Validar y FK. |
| 14 | Categorías sin FK | Huérfanos | Normalizar. |
| 15 | `numero_orden` por segundo | Colisiones | UUID. |
| 16 | Rate limit global por worker | 429 inesperados / bypass | Redis + ProxyFix + límites por ruta. |
| 17 | Imágenes de 8–11 MB | Lentitud | Optimización. |
| 18 | Sin cabeceras de seguridad | Riesgo | Añadir `after_request`. |
| 19 | Logout por GET | CSRF de logout | POST + token. |
| 20 | `run.bat`/`run.sh` muestran credenciales falsas | Confusión | Actualizar banners. |
| 21 | Referencias a archivos inexistentes (`seed_data.py`, `compile_all.py`, `verify_db.py`, `templates/base.html`) en docs antiguas | Confusión | Esta documentación las sustituye. |
| 22 | `FLASK_DEBUG` no se usa | Config inútil | Eliminar o implementar. |
| 23 | `usuario_celular` sin uso | Campo muerto | Rellenar en checkout o eliminar. |
| 24 | Sin manejo de errores personalizado | Mala UX | Plantillas 404/500. |

---

## 8. Troubleshooting

| Síntoma | Causa probable | Diagnóstico | Solución |
|---|---|---|---|
| `429 Too Many Requests` | Límite 50/h o 200/día; detrás de proxy todos comparten IP. | Revisar logs y si hay proxy. | Reiniciar (memoria) o configurar Redis/ProxyFix/límites. |
| El login no persiste | `SESSION_COOKIE_SECURE=True` sobre HTTP. | Mirar si `FLASK_ENV=production` y URL es http. | Usar HTTPS o development. |
| Sesión se pierde al reiniciar | `SECRET_KEY` cambia (p. ej. aleatoria por arranque). | Comparar claves entre reinicios. | Fijar `SECRET_KEY`. |
| `Error de seguridad: formulario inválido` | Token CSRF ausente/expirado. | Revisar campo `csrf_token` y sesión. | Recargar formulario; no borrar cookies. |
| `no such table` | BD no inicializada o ruta incorrecta. | `sqlite3 database.db ".tables"`. | `python database_setup.py`. |
| `database is locked` (SQLite) | Escritura concurrente. | Ver procesos y `busy_timeout`. | Reintentar, migrar a PostgreSQL. |
| `psycopg2.OperationalError` | URL/credenciales/host incorrectos. | Probar `psql "$DATABASE_URL"`. | Corregir `DATABASE_URL`. |
| `psycopg2-binary is required` | Driver no instalado. | `pip show psycopg2-binary`. | `pip install psycopg2-binary`. |
| `/admin/` 500 solo en Postgres | `datetime[:10]` en plantilla. | Traza en logs. | Formatear fecha antes de pasar a la plantilla. |
| Imagen 404 | Ruta relativa (`static/...`) o archivo ausente. | Revisar `imagen_url` y disco. | Normalizar a `/static/...`; volver a subir. |
| Imagen subida no se ve | Nombre con acentos/espacios o validación fallida. | Revisar `static/img/productos`. | Usar nombre simple o UUID; revisar flash. |
| No se crea el admin | Variables no exportadas. | `echo $env:INITIAL_ADMIN_EMAIL`. | Exportar y ejecutar setup. |
| No puedo entrar al admin | Usuario cliente o contraseña distinta. | Consultar `rol` en BD. | Crear/promover admin con hash. |
| WhatsApp sin destinatario | `WHATSAPP_PHONE` vacío/mal formado. | Revisar URL. | Solo dígitos con país. |
| El pedido no aparece | Checkout falló o no se envió. | Ver `pedidos` y flashes. | Revisar CSRF, sesión, BD. |
| Dos pedidos con la misma orden | Mismo segundo. | `SELECT numero_orden, COUNT(*) ... GROUP BY`. | UUID/retry. |
| `413 Request Entity Too Large` | Imagen > 16 MB. | Tamaño del archivo. | Comprimir o subir el límite. |
| Docker `db` reinicia | Falta `POSTGRES_PASSWORD` o credenciales no coinciden. | `docker compose logs db`. | Ver §6.3 de despliegue. |
| `ModuleNotFoundError` en Docker | `requirements.txt` incompleto. | Logs de build. | Añadir dependencia y rebuild. |
| CSS no se actualiza | Caché del navegador. | `cache_buster` en URL. | Hard reload. |

---

## 9. Roadmap sugerido

### Corto plazo

1. Corregir la configuración Docker (dev y prod).
2. Cargar `.env` con `load_dotenv()` o documentar el uso de variables.
3. Arreglar `nl2br` y las fechas en PostgreSQL.
4. Añadir `ProxyFix` y límites específicos a login.
5. Cabeceras de seguridad.
6. Cambiar logout a POST.
7. Actualizar/eliminar `e2e_test.py`.
8. Optimizar imágenes.

### Medio plazo

1. CRUD de estados de pedido y notificaciones.
2. Historial de pedidos del cliente.
3. Inventario/stock.
4. Cambio y reseteo de contraseña.
5. Verificación de email.
6. Logs y auditoría.
7. Suite de tests con `pytest`.
8. Redis para rate limiting.
9. Backups automáticos.

### Largo plazo

1. API REST/JSON para integraciones.
2. WhatsApp Cloud API.
3. Pasarela de pagos.
4. Roles y permisos granulares.
5. Panel de reportes y métricas.
6. Almacenamiento de imágenes en S3/CDN.
7. Multi-idioma y multi-moneda.

---

## 10. Contacto y responsables

- Repositorio: `https://github.com/InmaWebDev/Artisan-Web`.
- Rama principal: `main`.
- Último commit documentado: `dfeec6d`.
- Licencia: MIT.

Para incidencias de seguridad, sigue [07-seguridad §8](07-seguridad.md#8-divulgación-responsable).

---

**Anterior:** [08 · Despliegue](08-despliegue.md) · **Siguiente:** [10 · Referencia de código →](10-referencia-codigo.md)
