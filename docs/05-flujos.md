# 05 · Flujos funcionales

Este documento describe los recorridos de usuario de extremo a extremo. Los detalles técnicos de cada endpoint están en [04-rutas.md](04-rutas.md).

---

## 1. Puesta en marcha del administrador

```text
Operador                     database_setup.py              Base de datos
   │                                │                            │
   │ exporta INITIAL_ADMIN_*        │                            │
   ├───────────────────────────────►│                            │
   │                                ├─ ensure_schema() ─────────►│ crea tablas
   │                                ├─ hash(password)            │
   │                                ├─ INSERT admin ────────────►│ usuarios
   │                                ├─ INSERT categorías base ──►│ categorias
   │                                └─ commit()                  │
   │                                │                            │
   │◄────────── "Base de datos lista." ──────────────────────────┘
```

- Solo se crea el admin si **ambas** variables están definidas.
- Si el correo ya existe, `INSERT OR IGNORE` lo evita en SQLite.
- No hay promoción de usuario a admin desde la interfaz.

---

## 2. Registro de cliente

```text
Cliente                 /registro (POST)                 BD
   │                         │                           │
   ├─ nombre, correo, pass ─►│                           │
   │                         ├─ CSRF ok?                 │
   │                         ├─ validaciones              │
   │                         ├─ generate_password_hash    │
   │                         ├─ INSERT usuario ─────────►│
   │                         ├─ commit()                  │
   │◄── 302 /login + flash ──┤                           │
```

Validaciones:

| Regla | Mensaje |
|---|---|
| Todos los campos | `Por favor completa todos los campos.` |
| Contraseña ≥ 6 | `La contraseña debe tener al menos 6 caracteres.` |
| Contraseñas iguales | `Las contraseñas no coinciden.` |
| Nombre ≥ 3 | `El nombre debe tener al menos 3 caracteres.` |
| Correo único | `El correo ya está registrado.` |

El cliente creado tiene `rol = 'cliente'`. No se envía correo de confirmación.

---

## 3. Inicio y cierre de sesión

```text
Cliente                 /login (POST)                    BD
   │                         │                           │
   ├─ correo + password ────►│                           │
   │                         ├─ CSRF ok?                 │
   │                         ├─ SELECT usuario ─────────►│
   │                         ├─ check_password_hash      │
   │                         ├─ session.update(...)      │
   │                         ├─ session.permanent = True │
   │◄── 302 /index + flash ──┤                           │
```

Sesión resultante:

```python
{
    "user_id": 2,
    "rol": "cliente",
    "nombre": "Tester",
    "csrf_token": "…",
    "cart": [...]
}
```

Cierre: `GET /logout` → `session.clear()` → `302 /login`.

> Al cerrar sesión se pierde el carrito, porque vive en la sesión.

---

## 4. Navegación del catálogo

```text
Visitante
   │
   ├─ GET /index ─────────────► lista de categorías
   │       │
   │       └─ click categoría ─► GET /lineaproductos?categoria=Bisutería
   │                                  │
   │                                  ├─ select de producto (nombres distintos)
   │                                  └─ grilla de productos principales
   │
   └─ click producto ─────────► GET /producto/<id>
                                      │
                                      ├─ imagen principal + img2/img3
                                      ├─ descripción (acordeón)
                                      ├─ formulario cantidad + agregar al carrito
                                      ├─ botón WhatsApp directo
                                      └─ subproductos (si existen)
```

Filtros combinables:

```text
/lineaproductos                                → todos los principales
/lineaproductos?categoria=Bisutería            → categoría
/lineaproductos?categoria=Bisutería&nombre=X   → categoría + producto
/lineaproductos?nombre=X                       → producto en todas las categorías
```

El `<select>` de categoría solo aparece cuando no se llegó desde una categoría; en ese caso se muestra el nombre como título.

---

## 5. Carrito

### 5.1 Agregar

```text
Cliente autenticado          /carrito/add/<id> (POST)          BD
   │                                │                          │
   ├─ cantidad + csrf ─────────────►│                          │
   │                                ├─ ¿sesión? ──no──► 302 /login
   │                                ├─ CSRF ok? ──no──► 302 referrer
   │                                ├─ clamp 1..1000          │
   │                                ├─ SELECT producto ──────►│
   │                                │   (solo parent_id NULL) │
   │                                ├─ suma o crea ítem       │
   │                                ├─ session['cart'] = ...  │
   │◄── 302 referrer + flash ───────┤                          │
```

Un subproducto **no** puede agregarse directamente: la consulta exige `parent_id IS NULL`. Si se intenta, se muestra `Producto no encontrado.`

### 5.2 Ver y modificar

```text
GET /carrito
  ├─ items = session['cart']
  ├─ total = Σ(precio_sesión × cantidad)
  └─ render carrito.html

POST /carrito/update/<id>  → cambia cantidad (1..1000)
POST /carrito/remove/<id>  → elimina el ítem
POST /carrito/clear        → session.pop('cart')
```

Los precios mostrados provienen de la sesión; el total definitivo se recalcula en el checkout.

### 5.3 Estados del carrito

| Estado | `session['cart']` | Vista |
|---|---|---|
| Vacío | ausente o `[]` | Mensaje «El carrito está vacío» + enlace al catálogo. |
| Con ítems | lista de dicts | Lista, total, botones de compra/vaciar. |
| Sin sesión | — | Redirección a login al entrar a `/carrito`. |

---

## 6. Checkout por WhatsApp

```text
Cliente                   /carrito/checkout (POST)               BD
   │                                │                             │
   ├─ csrf ────────────────────────►│                             │
   │                                ├─ ¿sesión? ──no──► 302 /login
   │                                ├─ ¿carrito vacío? ──sí──► 302 /carrito
   │                                │                             │
   │                                ├─ por cada ítem:             │
   │                                │    SELECT producto ────────►│
   │                                │    (precio real, parent NULL)
   │                                │    clamp cantidad           │
   │                                │    suma total               │
   │                                ├─ ¿total > 0? ──no──► error  │
   │                                ├─ SELECT usuario ───────────►│
   │                                ├─ numero_orden = ORD-<epoch> │
   │                                ├─ INSERT pedido ────────────►│
   │                                ├─ commit()                   │
   │                                ├─ construir mensaje          │
   │                                ├─ session.pop('cart')        │
   │◄── 302 api.whatsapp.com/send ──┤                             │
```

Mensaje generado (ver [06-whatsapp.md](06-whatsapp.md)):

```text
Hola, me gustaría completar mi compra:

*Número de Orden:* ORD-1779210113

*Items:*
• Producto x2 = $39.98

*Total:* $39.98

Por favor confirmar disponibilidad y detalles de pago.
```

Puntos críticos:

1. El pedido se guarda **antes** de abrir WhatsApp.
2. El carrito se vacía aunque el usuario no envíe el mensaje.
3. No se guarda teléfono del cliente (`usuario_celular` queda `NULL`).
4. No se descuenta stock (no existe).
5. El estado inicial siempre es `pendiente`.

---

## 7. Compra directa desde la ficha

Además del carrito, `producto.html` ofrece **COMPRAR POR WHATSAPP**:

- JavaScript lee cantidad, nombre, precio y URL del producto.
- Construye el mensaje `Quiero comprar <qty> de <producto> a <precio> COP cada uno. <url>`.
- Abre `api.whatsapp.com/send`.
- **No** crea pedido en la BD, **no** valida stock y **no** pasa por el carrito.

Es un atajo de contacto, no una transacción registrada.

---

## 8. Administración de catálogo

### 8.1 Crear categoría

```text
Admin → /admin/ → formulario "Gestionar Categorías"
  → POST /admin/cat/add
  → INSERT OR IGNORE categorias
  → 302 /admin/ + flash
```

### 8.2 Crear producto principal

```text
Admin → /admin/ → "Subir Producto"
  ├─ nombre, categoría, precio, descripción (obligatorios)
  ├─ img1 (obligatoria en HTML), img2, img3 (opcionales)
  └─ parent_id vacío
       │
       ├─ validación de campos y precio > 0
       ├─ por cada archivo: extensión + firma binaria + secure_filename
       ├─ file.save(static/img/productos/<nombre>_<i><ext>)
       └─ INSERT productos (parent_id = NULL)
```

### 8.3 Crear subproducto

```text
Admin → fila de producto → botón "Subprod"
  → GET /admin/?parent_id=<id>  (preselecciona el padre)
  → mismo formulario de alta
  → INSERT productos con parent_id = <id>
```

El subproducto:

- Aparece en la ficha del padre.
- **No** aparece en el catálogo general.
- **No** se puede agregar al carrito.
- Tiene su propia ficha y botón de WhatsApp.

### 8.4 Editar producto

```text
Admin → "Editar" → GET /admin/prod/edit/<id>
  ├─ formulario precargado
  ├─ imágenes actuales en campos old_img1..3
  └─ POST
       ├─ si hay archivo nuevo: se guarda y reemplaza la ruta
       ├─ si no: se conserva old_imgN
       └─ UPDATE productos
```

### 8.5 Borrar producto o categoría

- Borrar producto: elimina solo la fila; no borra imágenes ni subproductos.
- Borrar categoría: elimina solo la fila; los productos conservan el texto de la categoría.

---

## 9. Gestión de pedidos (solo lectura)

```text
Admin → /admin/ → "Pedidos Recibidos"
  ├─ tabla: orden, cliente, total, nº artículos, estado, fecha
  └─ botón "Ver" → modal con el detalle de items
```

Limitaciones actuales:

- No hay botón para cambiar el estado (`pendiente` → `confirmado`/`cancelado`).
- No hay filtros, búsqueda ni paginación.
- No se muestra el teléfono del cliente.
- El modal se construye en JavaScript a partir de `data-items` (JSON).

> El `CHANGELOG.md` y el `README` anteriores mencionan que el vendedor «confirma la orden en el panel admin». Esa funcionalidad **no está implementada** en el código actual.

---

## 10. Flujos de error

| Escenario | Resultado |
|---|---|
| Registro con correo existente | Flash de correo registrado; sigue en `/registro`. |
| Login incorrecto | Flash genérico; sigue en `/login`. |
| Acceso a `/carrito` sin sesión | Flash + redirección a `/login`. |
| Acceso a `/admin/` sin rol | Flash + redirección a `/login`. |
| POST sin CSRF | Redirección con flash de seguridad o re-render. |
| Producto borrado antes del checkout | Se descarta del pedido; si no queda ninguno, error. |
| Precio modificado en sesión | Se ignora; se usa el de la BD. |
| Imagen inválida | Se ignora; el producto puede quedar sin imagen. |
| Colisión de `numero_orden` | Excepción → flash `Error al procesar la compra.` |
| Límite de rate excedido | `429` de Flask-Limiter. |

---

## 11. Máquina de estados del pedido

```text
        creación
           │
           ▼
     ┌───────────┐
     │ pendiente │  ← único estado alcanzable desde la UI
     └───────────┘
        (sin transiciones implementadas)
```

El campo `estado` admite cualquier texto, pero solo se escribe `'pendiente'`. Los estados `confirmado` y `cancelado` existen únicamente en la documentación histórica y en los estilos CSS (`estado-confirmado`, `estado-cancelado`).

---

**Anterior:** [04 · Rutas](04-rutas.md) · **Siguiente:** [06 · WhatsApp →](06-whatsapp.md)
