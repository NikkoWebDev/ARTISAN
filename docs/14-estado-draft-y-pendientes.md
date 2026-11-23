# 14 · Estado del draft y pendientes

Este documento es el punto de entrada para retomar el proyecto. Dice qué está terminado, qué es un borrador, qué riesgos hay en el código actual y qué tareas quedan, con referencias a archivo y línea.

> **Base:** commit `b77f5c5` (rama `main`), árbol limpio, revisado el **23 de noviembre de 2026**. Las líneas se verificaron con búsqueda en el código. Si el código cambia, vuelve a comprobarlas antes de editar.

---

## 1. Estado actual

**Qué es:** un sitio funcional para vender joyería textil y marroquinería, con la home, catálogo, ficha de producto, carrito, checkout por WhatsApp y panel de administración.

**Qué es draft:** el sitio funciona, pero el contenido, la identidad y la home todavía se están puliendo. Se considera un borrador que se va a terminar y pulir antes de publicar.

| Área | Estado | Comentario |
|---|---|---|
| Home (`/index`) | Draft | Funciona. Falta imagen en el hero, titular más claro y CTA de WhatsApp arriba. |
| Catálogo (`/lineaproductos`) | Funcional | Filtros por categoría y nombre. Sin paginación. |
| Ficha de producto (`/producto/<id>`) | Funcional | Incluye subproductos y migas de pan. No se revisó en detalle. |
| Carrito y drawer | Funcional | Dos implementaciones (HTML y `/api/cart`). El precio se recalcula en el servidor. |
| Checkout por WhatsApp | Funcional | Guarda el pedido en `pedidos` y abre WhatsApp. |
| Login y registro | Funcional | Contraseñas con hash. Sin recuperación de contraseña. |
| Admin | Funcional | CRUD de productos y categorías, lectura de pedidos. No cambia el estado de un pedido. |
| SEO | Incompleto | Sin canonical, Open Graph ni datos estructurados. |
| Pruebas | Parcial | `test_cart_flow.py` existe. `e2e_test.py` está desactualizado. |
| Documentación | Parcial | Los documentos 10 y 12 están desactualizados (ver §4). |

---

## 2. Riesgos verificados en el código

Ordenados por gravedad. Cada riesgo indica su ubicación exacta.

| # | Riesgo | Dónde | Impacto | Acción propuesta |
|---|---|---|---|---|
| 1 | **Clave secreta por defecto en producción posible.** Si no hay `SECRET_KEY`, se usa `artisan_key_2026`. La validación solo falla si `FLASK_ENV=production`, y `vercel.json` no define esa variable. | `app/config.py` (línea 5 para el valor por defecto y `validate()` al final). | Alto: se pueden falsificar sesiones si el despliegue no define variables. | Confirmar en Vercel y Render que `SECRET_KEY` y `FLASK_ENV` existen. Considerar validar siempre, no solo en producción. |
| 2 | **Cookies no seguras fuera de producción.** `SESSION_COOKIE_SECURE` solo se activa con `FLASK_ENV=production`. | `app/config.py` (bloque `if`). | Medio | Activar según el entorno real de despliegue. |
| 3 | **Número de WhatsApp fijo en el código.** Si no hay variable `WHATSAPP_PHONE`, se usa `573123580705`. | `app/__init__.py` (línea 11). | Bajo: cambiar de número obliga a tocar código o definir la variable. | Confirmar que el número por defecto es el correcto y documentarlo en `.env.example`. |
| 4 | **Dependencia circular controlada.** `cart.py` importa `WHATSAPP_PHONE` desde `app/__init__.py`. | `app/routes/cart.py` (línea 21). | Medio: mover la constante puede romper el arranque. | Mover la constante a `app/config.py` y leerla desde ahí. |
| 5 | **Carrito con dos implementaciones.** Las rutas HTML y las `/api/cart` repiten validaciones y mensajes. | `app/routes/cart.py` (líneas 112–410 aprox.). | Medio: un bug se corrige en un sitio y sigue en el otro. | Unificar la lógica en funciones compartidas. |
| 6 | **Catálogo y API sin paginación.** `/api/products` y `/lineaproductos` devuelven todas las filas. | `app/routes/shop.py` (líneas 25–62 y 81–93). | Medio: crece mal con muchos productos. | Paginación con `LIMIT`/`OFFSET` y columnas explícitas en lugar de `SELECT *`. |
| 7 | **Consulta sin uso en la home.** `index()` lee `categorias`, pero la plantilla no la usa. | `app/routes/shop.py` (línea 21). | Bajo: una consulta extra por visita. | Eliminar la consulta o usarla en la plantilla. |
| 8 | **`/` redirige a `/index`.** Un redirect extra por visita y dos URLs para la misma página. | `app/routes/shop.py` (líneas 12–15). Enlaces a `/index` en `header.html` y `footer.html`. | Medio para SEO. | Servir la home en `/` y redirigir `/index` a `/` con 301. |
| 9 | **Imágenes de producto sin tamaños adecuados.** La home usa `p.imagen_url` directamente y todas las imágenes tienen `loading="lazy"`, incluidas las del primer pliegue. | `templates/index.html` (línea 118). | Medio: peso y velocidad. | Usar la versión `_thumb.webp` en tarjetas, `width`/`height` y `loading="eager"` en las primeras imágenes. |
| 10 | **Atributo `onerror` inline.** Dificulta una política de seguridad de contenido (CSP). | `templates/index.html` (línea 118). | Bajo | Mover el fallback a `app.js`. |
| 11 | **Límites de peticiones con almacenamiento en memoria.** `memory://` no se comparte entre instancias ni sobrevive a reinicios. | `app/config.py` (`RATELIMIT_STORAGE_URI`). | Bajo en local, medio en serverless. | Usar Redis o aceptar el límite por instancia. |
| 12 | **`test_cart_flow.py` escribe en la base real.** Llama a `seed_database()` sin aislar la base. | `test_cart_flow.py` (línea 16) y `seed_catalog.py` (línea 124). | Medio: contamina `database.db`. | Ejecutar con `SQLITE_PATH` apuntando a un archivo temporal. |
| 13 | **Base de datos en Vercel no persiste.** Con `VERCEL=1` se copia `database.db` a `/tmp`. Los cambios se pierden al reiniciar la instancia. | `db_utils.py` (rama `VERCEL == '1'`). | Alto si el sitio se publica en Vercel con admin activo. | Decidir un hosting con base persistente (PostgreSQL) para producción. |
| 14 | **`package.json` con dependencia sin sentido.** Declara `flask ^0.2.10`, que no usa el código. | `package.json`. | Bajo: confusión y riesgo de instalar algo equivocado. | Eliminar si no hay tooling de Node. |

---

## 3. Pendientes de la home y del sitio

Lista priorizada. Cada tarea tiene archivos y un criterio para dar por terminada.

### Prioridad 1: SEO y estructura

- [ ] **Servir la home en `/`.** Cambiar `home()` para renderizar `index.html` y redirigir `/index` a `/` con 301.
  - Archivos: `app/routes/shop.py`, `templates/header.html`, `templates/footer.html`.
  - Criterio: `curl -I http://127.0.0.1:5000/index` responde 301 a `/`, y `/` responde 200.
- [ ] **Metadatos sociales y canonical.** Añadir `<link rel="canonical">`, `og:title`, `og:description`, `og:image` y `twitter:card` en `index.html` y `producto.html`.
  - Criterio: el HTML de `/` incluye esas etiquetas con valores no vacíos.
- [ ] **Datos estructurados.** `Organization` en la home y `Product` con precio y disponibilidad en `producto.html`.
  - Criterio: el resultado pasa la prueba de datos estructurados de Google (validar la URL en producción).
- [ ] **Favicon.** Añadir `<link rel="icon">` en `index.html`, `producto.html` y demás plantillas.

### Prioridad 2: Velocidad

- [ ] **Medir el peso de las imágenes.** Ejecutar `du -h static/img/productos | sort -h | tail` y comparar con `_thumb.webp`.
  - Nota: `docs/12` (desactualizado) reporta originales de 7–11 MB. No está verificado con la versión actual.
- [ ] **Usar miniaturas en listados.** En `index.html` y `lineaproductos.html`, cargar la versión `_thumb.webp` cuando exista y definir `width` y `height`.
- [ ] **Carga prioritaria en el primer pliegue.** Quitar `loading="lazy"` en las dos primeras tarjetas de `index.html`.
- [ ] **Caché de estáticos.** Confirmar que `/static/` envía cabeceras de caché. Flask no lo configura por defecto.
- [ ] **Medición base.** Correr Lighthouse o PageSpeed sobre la URL publicada antes y después de los cambios. Sin esa medición no hay forma de saber si mejoró.

### Prioridad 3: Home y ventas

- [ ] **Reescribir el titular del hero.** Debe decir qué se vende. Propuesta de punto de partida: "Joyería tejida a mano y marroquinería de autor, hechas en San Agustín". Requiere aprobación del dueño.
- [ ] **Añadir imagen al hero.** Foto de lookbook de fondo o una pieza grande. Hoy el hero es solo texto.
- [ ] **CTA de WhatsApp arriba.** Botón "Pedir por WhatsApp" junto al hero o en el header.
- [ ] **Información de compra.** Tiempos de envío, costo, medios de pago y política de cambios. **Son datos del negocio; no inventarlos.**
- [ ] **Revisar afirmaciones.** Hay promesas comerciales repetidas con redacción distinta:
  - "Comercio Justo" en `footer.html` (línea 17 aprox.).
  - "3-5 días hábiles" y "tarjeta de autenticidad" en `producto.html` (línea 89).
  - "Envíos asegurados a todo el territorio nacional" en `carrito.html` (línea 124).
  - "Envíos asegurados a todo Colombia" con barra de progreso en `_drawer_cart.html` (línea 27). La barra implica un umbral de envío gratis que no está documentado.
  - "ENVÍOS A TODA COLOMBIA" en el banner de `header.html` (línea 4) e "Envíos Asegurados" en `index.html` (línea 45).
  - Unificar la redacción en una sola fuente y confirmar cada dato con el dueño.
- [ ] **Prueba social.** Reseñas o fotos de clientes. Depende de tener esos datos.

### Prioridad 4: Experiencia de usuario

- [ ] **Quitar solapamiento de menú.** El header tiene "Catálogo", "Bisutería" y "Marroquinería", y la home repite las dos categorías. Dejar una sola ruta de navegación.
- [ ] **Botón real en el footer.** "Bolsa de Compras" en `footer.html` es un `<a href="javascript:void(0)">`. Cambiarlo a `<button>`.
- [ ] **Estado vacío con salida.** Si no hay productos, la home dice "Pronto publicaremos…" sin enlace. Añadir un botón a WhatsApp.
- [ ] **Un solo término para el carrito.** La interfaz dice "Bolsa". Revisar que todo el texto visible use el mismo término.
- [ ] **Ficha de producto sin revisar.** `producto.html` no se analizó en esta revisión. Hacer el mismo análisis que la home.

### Prioridad 5: Seguridad y deuda técnica

- [ ] Resolver los riesgos 1, 2 y 4 de §2.
- [ ] Mover `WHATSAPP_PHONE` a `app/config.py`.
- [ ] Reescribir o eliminar `e2e_test.py`.
- [ ] Eliminar `package.json` si no hay uso de Node.
- [ ] Decidir un hosting con base persistente para producción (riesgo 13).

---

## 4. Documentación desactualizada

Los documentos de `docs/` no reflejan el estado actual del código. Verificado:

| Documento | Problema |
|---|---|
| `docs/README.md` | Dice commit `dfeec6d` y fecha 2026-10-25. El commit actual es `b77f5c5`. |
| `docs/10-referencia-codigo.md` | Dice que `app/extensions.py` usa `200 per day` y `50 per hour`. El código usa `1000 per hour` y `100 per minute`. Dice que `header.html` contiene el JS del menú; ese código está en `static/js/app.js`. |
| `docs/12-inventario-archivos.md` | Dice que la raíz se llama `Artisan Web/` y que hay carpetas que no existen en esta copia (`__MACOSX/`, `Flask_HTML_Sample/`). Los tamaños de imágenes también son de otra fecha. |
| `docs/04-rutas.md`, `docs/05-flujos.md`, `docs/07-seguridad.md` | No se revisaron línea por línea en esta pasada. Tratarlos como sospechosos hasta verificarlos. |

**Recomendación:** regenerar los documentos 10 y 12 a partir del código actual, o marcarlos como históricos. El mapa de [13 · Grafo](13-grafo-proyecto.md) es la referencia actualizada para archivos y dependencias.

---

## 5. Decisiones que necesita el dueño

No son técnicas. El modelo no debe decidirlas por su cuenta.

1. **Titular y tono de marca.** El texto actual es poético y abstracto. ¿Se mantiene ese tono o se pasa a uno más directo?
2. **Datos comerciales.** Tiempos de envío, costo, medios de pago, política de cambios y cobertura de envío.
3. **Afirmaciones.** ¿Existe certificación de "Comercio Justo"? ¿Se envía a toda Colombia de forma asegurada?
4. **Número de WhatsApp.** ¿Es el número definitivo? ¿Debe ser una variable de entorno obligatoria?
5. **Hosting y base de datos.** Vercel con SQLite no persiste los datos. ¿Se usa PostgreSQL en Render u otro proveedor?
6. **Identidad visual.** ¿Hay logo o isotipo, o se mantiene el texto "ARTISAN"?
7. **Reseñas y fotos de clientes.** ¿Se pueden mostrar?

---

## 6. Orden sugerido para el modelo que edite

1. Leer [13 · Grafo](13-grafo-proyecto.md) §4 y §5 para ubicar archivos.
2. Verificar que el proyecto arranca con los comandos de [13 · §7](13-grafo-proyecto.md#7-cómo-verificar-que-un-cambio-no-rompe-el-grafo).
3. Resolver Prioridad 1 (SEO y estructura) con cambios pequeños y verificables.
4. Pedir al dueño las decisiones de §5 antes de tocar textos comerciales.
5. Medir velocidad antes y después de la Prioridad 2.
6. Actualizar los documentos afectados al terminar cada tarea (ver [README §Cómo mantener](README.md)).

---

## 7. Reglas al editar

- **No leer ni copiar valores de `.env`, `backend.env` ni `env.md`.** Pueden contener secretos.
- **No modificar `database.db` desde pruebas.** Usar `SQLITE_PATH` a un archivo temporal.
- **Todo formulario POST valida CSRF** con `validate_csrf()`. Las plantillas incluyen el campo `csrf_token`.
- **Rutas de administración con `@admin_required`.**
- **No publicar ni desplegar sin confirmación.** Subir a producción es una acción irreversible para el negocio.
- **No inventar datos comerciales.** Si falta un dato, dejarlo marcado como pendiente.

---

**Anterior:** [13 · Grafo del proyecto](13-grafo-proyecto.md) · **Índice:** [README](README.md)
