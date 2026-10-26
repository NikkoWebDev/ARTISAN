# 📚 Documentación de Artisan

Documentación técnica y funcional de la tienda **Artisan**. Describe la aplicación tal como está implementada en el commit `dfeec6d` (rama `main`), revisada el **25 de octubre de 2026**.

> Esta documentación refleja el **comportamiento real del código**, incluyendo limitaciones y deuda técnica. Cuando una práctica recomendada no está implementada, se indica explícitamente.

---

## Mapa de documentos

| # | Documento | Para qué sirve | Público |
|---|---|---|---|
| 1 | [Arquitectura](01-arquitectura.md) | Entender la estructura, el application factory, los blueprints y el ciclo de una petición. | Desarrollo |
| 2 | [Instalación](02-instalacion.md) | Levantar el proyecto en local, configurar variables y ejecutar con Docker. | Desarrollo / DevOps |
| 3 | [Base de datos](03-base-de-datos.md) | Esquema, relaciones, migraciones automáticas, SQLite vs PostgreSQL y respaldos. | Desarrollo / DBA |
| 4 | [Rutas](04-rutas.md) | Referencia completa de endpoints, permisos, parámetros y respuestas. | Desarrollo / QA |
| 5 | [Flujos](05-flujos.md) | Recorridos funcionales: registro, catálogo, carrito, checkout y administración. | Producto / QA |
| 6 | [WhatsApp](06-whatsapp.md) | Cómo se construye el mensaje, configuración del número y límites. | Producto / Desarrollo |
| 7 | [Seguridad](07-seguridad.md) | Controles existentes, análisis de riesgos y checklist de endurecimiento. | Seguridad / DevOps |
| 8 | [Despliegue](08-despliegue.md) | Docker, Gunicorn, PostgreSQL, Render, CI y proceso de release. | DevOps |
| 9 | [Operación y mantenimiento](09-operacion-mantenimiento.md) | Runbook, respaldos, pruebas, problemas conocidos y roadmap. | Soporte / DevOps |
| 10 | [Referencia de código](10-referencia-codigo.md) | Explicación archivo por archivo y función por función. | Desarrollo |
| 11 | [Interfaz UI](11-interfaz-ui.md) | Sistema de diseño, componentes, JavaScript y accesibilidad. | Diseño / Frontend |
| 12 | [Inventario de archivos](12-inventario-archivos.md) | Qué es cada archivo y qué se incluye en `artisan.zip`. | Todos |

---

## Resumen en 30 segundos

- **Qué es:** tienda online Flask + SQLite/PostgreSQL con checkout por WhatsApp.
- **Entrada:** `app.py` (desarrollo) y `wsgi.py` (producción/Gunicorn).
- **Núcleo:** `app.create_app()` registra cuatro blueprints: `auth`, `shop`, `cart`, `admin`.
- **Datos:** `db_utils.py` abstrae SQLite y PostgreSQL y aplica migraciones al conectar.
- **Sesión:** guarda `user_id`, `rol`, `nombre`, `csrf_token` y `cart`.
- **Compra:** el carrito vive en sesión; el checkout valida precios contra la BD, crea un registro en `pedidos` y redirige a `api.whatsapp.com`.
- **Admin:** CRUD de productos y categorías + lectura de pedidos. No cambia el estado de los pedidos.
- **Despliegue:** Dockerfile/Dockerfile.prod, Compose, Gunicorn y GitHub Actions.

---

## Convenciones de esta documentación

- Los bloques de código con `text` representan árboles, diagramas o salidas.
- Las rutas se muestran con su método HTTP y su ruta exacta.
- «Sesión» significa usuario autenticado (`session['user_id']`).
- «Admin» significa `session['rol'] == 'admin'`.
- Los avisos ⚠️ señalan limitaciones reales o riesgos, no necesariamente errores bloqueantes.
- Las rutas de archivo son relativas a la raíz del proyecto.

---

## Fuentes de verdad

1. Código en `app/`, `templates/`, `static/`, `db_utils.py`.
2. Esquema en `db_utils.ensure_schema()`.
3. Configuración en `app/config.py`.
4. Workflows en `.github/workflows/`.
5. Documentos históricos: `CHANGELOG.md`, `CONTRIBUTING.md`, `PRODUCTION_CHECKLIST.md`, `RELEASE.md`.

Si el código y esta documentación difieren, **prevalece el código**; actualiza el documento correspondiente en el mismo cambio.

---

## Cómo mantener la documentación

- Al añadir una ruta: actualiza [04-rutas.md](04-rutas.md), [09-inventario](12-inventario-archivos.md) si crea archivos y [05-flujos](05-flujos.md) si cambia un recorrido.
- Al cambiar el esquema: actualiza [03-base-de-datos.md](03-base-de-datos.md) y la sección de migraciones.
- Al añadir una variable de entorno: actualiza [02-instalación](02-instalacion.md#3-variables-de-entorno), [08-despliegue](08-despliegue.md#2-variables-de-entorno) y `.env.example`.
- Al cambiar seguridad: actualiza [07-seguridad.md](07-seguridad.md).
- Al cambiar la UI: actualiza [11-interfaz-ui.md](11-interfaz-ui.md).

---

**Versión documentada:** 2.x · **Commit:** `dfeec6d` · **Fecha:** 2026-10-25
