# 04 · Referencia de rutas

## 1. Convenciones

| Símbolo | Significado |
|---|---|
| **Público** | No requiere sesión. |
| **Sesión** | Requiere `session['user_id']` (`@cart_required`). |
| **Admin** | Requiere `session['rol'] == 'admin'` (`@admin_required`). |
| **CSRF** | El `POST` valida `csrf_token` contra la sesión. |
| **Rate limit** | Límite global por IP: 200/día y 50/hora. |

Comportamiento ante fallos:

- **Sin sesión en carrito:** flash `Debes iniciar sesión para ver el carrito.` y `302` a `/login`.
- **Sin rol admin:** flash `Debes iniciar sesión como administrador.` y `302` a `/login`.
- **CSRF inválido:** en `auth` se vuelve a renderizar el formulario (200); en el resto se redirige al `referrer`, al carrito o al índice con un flash de error.
- **Método incorrecto:** `405 Method Not Allowed`.
- **Producto inexistente:** flash y redirección (no 404).

Mapa completo (generado desde `app.url_map`):

```text
/                                             ['GET']            -> shop.home
/admin/                                       ['GET']            -> admin.panel
/admin/add_prod                               ['POST']           -> admin.add_product
/admin/cat/add                                ['POST']           -> admin.add_category
/admin/cat/del/<int:id>                       ['POST']           -> admin.delete_category
/admin/prod/del/<int:id>                      ['POST']           -> admin.delete_product
/admin/prod/edit/<int:id>                     ['GET', 'POST']    -> admin.edit_product
/carrito                                      ['GET']            -> cart.view_cart
/carrito/add/<int:id>                         ['POST']           -> cart.add_to_cart
/carrito/checkout                             ['POST']           -> cart.checkout_whatsapp
/carrito/clear                                ['POST']           -> cart.clear_cart
/carrito/remove/<int:id>                      ['POST']           -> cart.remove_from_cart
/carrito/update/<int:id>                      ['POST']           -> cart.update_cart
/index                                        ['GET']            -> shop.index
/lineaproductos                               ['GET']            -> shop.lineaproductos
/login                                        ['GET', 'POST']    -> auth.login
/logout                                       ['GET']            -> auth.logout
/producto/<int:id>                            ['GET']            -> shop.producto_detalle
/registro                                     ['GET', 'POST']    -> auth.registro
/static/<path:filename>                       ['GET']            -> static
```

> `/admin` (sin barra) responde `308` hacia `/admin/`.

---

## 2. Resumen

| Método | Ruta | Acceso | CSRF | Escribe en BD |
|---|---|---|---|---|
| GET | `/` | Público | — | No |
| GET | `/index` | Público | — | No |
| GET | `/lineaproductos` | Público | — | No |
| GET | `/producto/<id>` | Público | — | No |
| GET | `/login` | Público | — | No |
| POST | `/login` | Público | Sí | No |
| GET | `/registro` | Público | — | No |
| POST | `/registro` | Público | Sí | Sí (`usuarios`) |
| GET | `/logout` | Público | — | No |
| GET | `/carrito` | Sesión | — | No |
| POST | `/carrito/add/<id>` | Sesión | Sí | No |
| POST | `/carrito/update/<id>` | Sesión | Sí | No |
| POST | `/carrito/remove/<id>` | Sesión | Sí | No |
| POST | `/carrito/clear` | Sesión | Sí | Sí (`pedidos` no; solo sesión) |
| POST | `/carrito/checkout` | Sesión | Sí | Sí (`pedidos`) |
| GET | `/admin/` | Admin | — | No |
| POST | `/admin/add_prod` | Admin | Sí | Sí (`productos`) |
| POST | `/admin/cat/add` | Admin | Sí | Sí (`categorias`) |
| POST | `/admin/cat/del/<id>` | Admin | Sí | Sí (`categorias`) |
| POST | `/admin/prod/del/<id>` | Admin | Sí | Sí (`productos`) |
| GET | `/admin/prod/edit/<id>` | Admin | — | No |
| POST | `/admin/prod/edit/<id>` | Admin | Sí | Sí (`productos`) |

---

## 3. Autenticación (`auth`)

### 3.1 `GET /login`

Renderiza `login.html`. Incluye `_flash.html` y `footer.html`.

- Contexto: `csrf_token()` (global), `WHATSAPP_PHONE` (global).
- Si ya hay sesión, no redirige automáticamente; muestra el formulario igualmente.

### 3.2 `POST /login`

| Campo | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `csrf_token` | hidden | Sí | Igual al de sesión. |
| `correo` | email | Sí | `strip()`; no vacío. |
| `password` | password | Sí | No vacío. |

Flujo:

1. CSRF inválido → renderiza `login.html` (200) sin flash específico.
2. Campos vacíos → flash `Por favor completa todos los campos.` (error) y renderiza.
3. Busca `usuarios.correo`.
4. Verifica con `check_password_hash`.
5. Correcto:
   - `session.update({user_id, rol, nombre})`
   - `session.permanent = True` (31 días por defecto de Flask).
   - flash `Bienvenido, has iniciado sesión correctamente.`
   - `302` a `/index`.
6. Incorrecto → flash `Correo o contraseña incorrectos.` y renderiza (200).

No hay bloqueo por intentos fallidos ni regeneración del ID de sesión.

### 3.3 `GET /registro`

Renderiza `registro.html`.

### 3.4 `POST /registro`

| Campo | Validaciones |
|---|---|
| `csrf_token` | Igual al de sesión. |
| `nombre` | `strip()`, no vacío, mínimo 3 caracteres. |
| `correo` | `strip()`, no vacío. No se valida formato en servidor. |
| `password` | No vacío, mínimo 6 caracteres. |
| `password_confirm` | Debe coincidir con `password`. |

Flujo:

1. Cualquier validación falla → flash de error y renderiza (200).
2. Genera hash scrypt con `generate_password_hash`.
3. `INSERT INTO usuarios (..., rol='cliente')`.
4. `commit()`.
5. Éxito → flash `Registro exitoso. Ya puedes iniciar sesión.` y `302` a `/login`.
6. Cualquier excepción (incluido correo duplicado) → flash `El correo ya está registrado.` y renderiza.

> El `except` es genérico: un fallo de BD distinto también se reporta como correo duplicado.

### 3.5 `GET /logout`

- `session.clear()`.
- flash `Sesión cerrada correctamente.` (info).
- `302` a `/login`.

No valida CSRF porque es `GET`; un tercero podría forzar el cierre de sesión con un enlace.

---

## 4. Tienda (`shop`)

### 4.1 `GET /`

Redirección `302` a `/index`.

### 4.2 `GET /index`

- Consulta todas las categorías.
- Renderiza `index.html` con `categorias`.
- Cada categoría enlaza a `/lineaproductos?categoria=<nombre>`.

### 4.3 `GET /lineaproductos`

Parámetros de query (ambos opcionales):

| Parámetro | Efecto |
|---|---|
| `categoria` | Filtra productos por `categoria` exacta. |
| `nombre` | Filtra por `nombre` exacto. |

Comportamiento:

1. Carga categorías.
2. Carga nombres distintos de productos principales (`parent_id IS NULL`), filtrados por categoría si se indicó.
3. Construye condiciones: siempre `parent_id IS NULL`; añade `categoria = ?` y `nombre = ?`.
4. `ORDER BY id DESC`.
5. Renderiza `lineaproductos.html` con `productos`, `categorias`, `nombres`, `categoria_actual`, `nombre_actual`.

El filtro por categoría se muestra solo si no hay categoría seleccionada; si hay, se muestra el título y el `<select>` de producto. El JavaScript `applyFilters()` reconstruye la URL y navega.

### 4.4 `GET /producto/<int:id>`

- Busca el producto por `id`.
- Si no existe: flash `Producto no encontrado.` y `302` a `/lineaproductos`.
- Carga subproductos `WHERE parent_id = id`.
- Renderiza `producto.html` con `p` y `subproductos`.

La ficha no comprueba si el producto es principal o subproducto; cualquiera puede abrirse por ID.

---

## 5. Carrito (`cart`)

El carrito se guarda en `session['cart']` como lista de diccionarios:

```json
[
  {"id": 1, "nombre": "Producto", "precio": 19.99, "cantidad": 3}
]
```

`MAX_QTY = 1000`. Todas las cantidades se limitan con `max(1, min(qty, 1000))`.

### 5.1 `GET /carrito`

- `@cart_required`.
- Lee `session['cart']` (vacío si no existe).
- Calcula el total con los precios **de la sesión** (solo para mostrar).
- Renderiza `carrito.html` con `items` y `total`.

### 5.2 `POST /carrito/add/<int:id>`

| Campo | Tipo | Por defecto |
|---|---|---|
| `csrf_token` | hidden | — |
| `cantidad` | number | 1 |

Flujo:

1. CSRF inválido → `302` al `referrer` o `/lineaproductos`.
2. Normaliza cantidad (entero entre 1 y 1000; valores inválidos → 1).
3. Busca el producto con `id` y `parent_id IS NULL`.
4. Si no existe o es subproducto → flash `Producto no encontrado.` y redirección.
5. Si ya está en el carrito, suma y limita a 1000.
6. Si no, añade `{id, nombre, precio, cantidad}`.
7. flash `"<nombre> agregado al carrito (x<cantidad>)"` (success).
8. `302` al `referrer` o `/lineaproductos`.

> La ruta es **solo POST**. Un `GET /carrito/add/1` devuelve `405`.

### 5.3 `POST /carrito/remove/<int:id>`

- CSRF obligatorio.
- No exige `@cart_required`; opera sobre la sesión actual.
- Filtra el ítem por `id`.
- flash `Artículo eliminado del carrito.` (info).
- `302` a `/carrito`.

### 5.4 `POST /carrito/update/<int:id>`

- CSRF obligatorio.
- Normaliza `cantidad` (1–1000).
- Si el ítem existe, actualiza la cantidad y muestra flash.
- Si no existe, no hace nada (sin error).
- `302` a `/carrito`.

### 5.5 `POST /carrito/clear`

- CSRF obligatorio.
- `session.pop('cart', None)`.
- flash `Carrito vaciado.` (info).
- `302` a `/carrito`.

### 5.6 `POST /carrito/checkout`

- CSRF obligatorio.
- Si no hay `user_id` → flash `Debes iniciar sesión para comprar.` y `302` a `/login`.
- Si el carrito está vacío → flash `Tu carrito está vacío.` y `302` a `/carrito`.

Flujo transaccional:

1. Recorre los ítems de la sesión.
2. Por cada uno, consulta `id`, `nombre`, `precio` en la BD (`parent_id IS NULL`).
3. Descarta los que ya no existen.
4. Normaliza cantidad (1–1000).
5. Recalcula `total` con precios de la BD.
6. Si no queda ningún ítem válido o `total <= 0` → flash `Error al procesar el carrito.` y redirección.
7. Busca el usuario por `session['user_id']`; si no existe → flash y `302` a `/login`.
8. Genera `numero_orden = "ORD-<epoch segundos>"`.
9. Inserta en `pedidos` con `items` JSON, `total` y `estado='pendiente'`.
10. `commit()`.
11. Construye el mensaje de WhatsApp con ítems y total.
12. `session.pop('cart', None)`.
13. `302` a `https://api.whatsapp.com/send?phone=<WHATSAPP_PHONE>&text=<mensaje urlencoded>`.

Si cualquier paso lanza excepción → flash `Error al procesar la compra.` y `302` a `/carrito`.

> Limpiar el carrito ocurre **antes** de que el usuario envíe el mensaje. Si abandona WhatsApp, el pedido ya quedó registrado como `pendiente`.

---

## 6. Administración (`admin`)

### 6.1 `GET /admin/`

- `@admin_required`.
- Productos: `SELECT p.*, parent.nombre AS parent_name ... ORDER BY p.parent_id IS NOT NULL, p.id DESC`.
- Categorías: todas.
- Pedidos: todos, ordenados por `fecha_creacion DESC`.
- Convierte `items` JSON a lista; si falla, deja `[]`.
- Añade `item_count`.
- Query opcional `parent_id` para preseleccionar el padre en el formulario de subproducto.
- Renderiza `admin.html`.

### 6.2 `POST /admin/add_prod`

| Campo | Obligatorio | Validación |
|---|---|---|
| `csrf_token` | Sí | Token de sesión. |
| `nombre` | Sí | `strip()`. |
| `categoria` | Sí | `strip()`. |
| `precio` | Sí | `float > 0`. |
| `descripcion` | Sí | `strip()`. |
| `img1` | Sí en HTML, no en servidor | Extensión y firma válidas. |
| `img2`, `img3` | No | Igual. |
| `parent_id` | No | Texto o `None`; no se valida existencia. |

- Si faltan campos → flash con la lista de faltantes y `302` a `/admin/`.
- Precio inválido → flash `El precio debe ser un número positivo.` y redirección.
- Guarda hasta 3 imágenes con `save_image()`.
- `INSERT INTO productos` y `commit()`.
- flash `Producto publicado exitosamente.` y `302` a `/admin/`.
- Error de BD → flash `Error al guardar el producto.`.

### 6.3 `POST /admin/cat/add`

| Campo | Obligatorio |
|---|---|
| `nueva_categoria` | Sí (`strip()`). |

- `INSERT OR IGNORE INTO categorias`.
- flash success o error.
- `302` a `/admin/`.

### 6.4 `POST /admin/cat/del/<int:id>`

- `DELETE FROM categorias WHERE id = ?`.
- No reasigna ni borra productos de esa categoría.
- flash `Categoría eliminada.` y `302` a `/admin/`.

### 6.5 `POST /admin/prod/del/<int:id>`

- `DELETE FROM productos WHERE id = ?`.
- No borra archivos de imagen ni subproductos.
- flash `Producto eliminado.` y `302` a `/admin/`.

### 6.6 `GET /admin/prod/edit/<int:id>`

- Carga producto por id (si no existe: flash y `302` a `/admin/`).
- Carga categorías y lista de productos para el selector de padre.
- Renderiza `edit_product.html`.

### 6.7 `POST /admin/prod/edit/<int:id>`

Mismos campos y validaciones que `add_prod`, más:

- `old_img1`, `old_img2`, `old_img3`: rutas actuales. Si no se sube imagen nueva, se conserva la anterior.
- Si se sube una imagen nueva, se guarda con el nombre del producto y se usa su URL; si falla la validación, cae al `old_img`.
- `UPDATE productos SET nombre=?, categoria=?, precio=?, descripcion=?, imagen_url=?, img2=?, img3=?, parent_id=? WHERE id=?`.
- flash `Producto actualizado exitosamente.` y `302` a `/admin/`.

No se valida que `parent_id` no sea el propio producto ni que exista.

---

## 7. Errores y códigos de estado

| Situación | Código | Respuesta |
|---|---|---|
| Página correcta | 200 | HTML. |
| Redirección normal | 302 | `Location`. |
| `/admin` sin barra | 308 | Redirección permanente. |
| Método no permitido | 405 | Página por defecto de Flask. |
| Ruta inexistente | 404 | Página por defecto de Flask. |
| Excepción no controlada | 500 | Página por defecto de Flask (sin handler propio). |
| Límite excedido | 429 | Respuesta de Flask-Limiter. |

No hay plantillas personalizadas para 404/500 ni logging configurado.

---

## 8. Cómo inspeccionar las rutas

```bash
python - <<'PY'
from app import create_app
app = create_app()
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    print(r.rule, sorted(r.methods - {'HEAD', 'OPTIONS'}), '->', r.endpoint)
PY
```

En PowerShell, guarda el bloque en un archivo `.py` o usa un here-string.

---

**Anterior:** [03 · Base de datos](03-base-de-datos.md) · **Siguiente:** [05 · Flujos →](05-flujos.md)
