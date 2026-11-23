# Artisan: guía para editar el proyecto

Tienda Flask para joyería textil y marroquinería (San Agustín, Huila). Checkout por WhatsApp. El sitio es un **draft que se va a terminar y pulir**.

## Dónde está todo

- Mapa de dependencias, rutas, plantillas y JS: `docs/13-grafo-proyecto.md`. Tabla "quiero X, toco Y" en §5.
- Estado, riesgos con línea exacta y backlog priorizado: `docs/14-estado-draft-y-pendientes.md`.
- Entrada de la app: `app.py` (dev) y `wsgi.py` (producción). Todo pasa por `create_app()` en `app/__init__.py`.
- Rutas: `app/routes/{auth,shop,cart,admin}.py`. Plantillas: `templates/`. Estilos: `static/css/style.css`. JS: `static/js/{app,cart-drawer}.js`.
- Base de datos: `app/db.py` (conexión por petición) y `db_utils.py` (esquema y migraciones). Nunca conectar directo desde una ruta.

## Reglas al editar

- Cada formulario POST valida CSRF con `validate_csrf()` y lleva `<input name="csrf_token">`.
- Las rutas de administración usan `@admin_required`.
- El precio del carrito se recalcula en el servidor con `get_cart_payload()`. No confiar en precios del cliente.
- `header.html` y `footer.html` afectan todas las páginas. `footer.html` carga los dos scripts globales.
- `login.html` y `registro.html` no incluyen el header.
- Cambios en el esquema: migración en `ensure_schema()` (SQLite y PostgreSQL) y actualizar `seed_catalog.py`.
- Si cambias una ruta, variable de entorno o archivo, actualiza el documento correspondiente en `docs/`.

## Qué no hacer

- No leer ni copiar valores de `.env`, `backend.env` ni `env.md`. Pueden tener secretos.
- No modificar `database.db` desde pruebas. Las pruebas viven en `tests/` y usan una base temporal.
- No inventar datos comerciales (tiempos de envío, costos, certificaciones, reseñas). Si falta un dato, dejarlo marcado como pendiente. Ver `docs/14` §5.
- No desplegar ni publicar sin confirmación del dueño.
- No usar `docs/10` ni `docs/12` como fuente: están desactualizados. La fuente es el código.

## Verificación rápida

```bash
python -c "from app import create_app; a = create_app(); print('arranca ok')"
.venv/bin/python -m pytest tests -q
```
