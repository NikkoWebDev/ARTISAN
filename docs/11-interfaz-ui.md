# 11 · Interfaz y experiencia de usuario

## 1. Principios visuales

| Rasgo | Implementación |
|---|---|
| Estilo | Premium, artesanal, oscuro con acentos dorados. |
| Fondo | Verde bosque profundo (`--bg: #0d2416`). |
| Acento | Dorado (`--gold: #c9a84c`) y verde (`--accent: #2b5e45`). |
| Tipografía de títulos | Playfair Display (serif). |
| Logotipo | Cormorant Garamond. |
| Texto de interfaz | Montserrat (400–800). |
| Superficies | Elevadas con bordes sutiles dorados y sombras suaves. |
| Movimiento | Aparición al hacer scroll (`.reveal`), hover con subrayado y elevación. |

Las fuentes se cargan desde Google Fonts mediante `@import` al inicio de `style.css`. Esto añade una dependencia externa y una petición bloqueante.

---

## 2. Tokens de diseño

```css
:root {
  --bg: #0d2416;
  --bg-elevated: #122d1d;
  --bg-surface: #1a3a27;
  --bg-light: #f8f6f1;
  --bg-white: #ffffff;

  --gold: #c9a84c;
  --gold-light: #e8d48b;
  --gold-dim: #a6882e;

  --accent: #2b5e45;
  --accent-hover: #367a58;

  --danger: #c0392b;
  --danger-hover: #a93226;
  --success: #27ae60;
  --info: #2980b9;

  --text: #f0ede8;
  --text-heading: #ffffff;
  --text-dark: #1a1a1a;
  --text-muted: #999487;
  --text-body: #333333;

  --border: rgba(201, 168, 76, 0.15);
  --border-light: rgba(255, 255, 255, 0.08);

  --font-heading: 'Playfair Display', Georgia, serif;
  --font-logo: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'Montserrat', system-ui, -apple-system, sans-serif;

  --radius: 16px;
  --radius-sm: 8px;
  --radius-lg: 24px;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.25);
  --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 3. Estructura de página

Todas las páginas comparten:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>… - Artisan</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  {% include 'header.html' %}
  <main>…</main>
  {% include 'footer.html' %}
</body>
</html>
```

`login.html` y `registro.html` no incluyen `header.html`; usan `_flash.html` directamente y un `body` con clase temática.

La clase `.reveal` activa la animación cuando el elemento entra en viewport. La animación se desactiva visualmente si el elemento ya está visible al cargar (el observer lo marca).

---

## 4. Página por página

### 4.1 Inicio (`/index`)

```text
Header
└── main.contenedor.centro.reveal
    ├── h1 "NUESTRAS CATEGORÍAS"
    ├── p.subtitulo
    └── div.grilla-productos
        └── a.producto.categoria-card (por categoría)
            └── h3.categoria-nombre
Footer
```

- Cada tarjeta enlaza a `/lineaproductos?categoria=<nombre>`.
- `min-height: 60vh` centra el contenido.
- Si no hay categorías, la grilla queda vacía (sin mensaje).

### 4.2 Catálogo (`/lineaproductos`)

```text
main.contenedor.reveal
├── section.filtro-productos
│   ├── (sin categoría) label + select#categoria-select
│   ├── (con categoría) h2.current-category
│   └── label + select#nombre-select
└── div.grilla-productos
    └── a.producto (por producto)
        ├── img (lazy + cache buster)
        ├── h3
        └── p "$precio COP"
```

- La grilla usa `repeat(auto-fill, minmax(...))`.
- Los productos se muestran de más nuevo a más viejo.
- No hay paginación ni estado vacío.
- El filtro se aplica al cambiar el `<select>` (no hay botón).

### 4.3 Ficha de producto (`/producto/<id>`)

```text
main.contenedor.producto-detalle.reveal
├── div.galeria
│   ├── img.principal-img
│   └── div.extra-images
│       └── img.thumb-img (hasta 2)
├── div.info-producto
│   ├── h1.producto-nombre
│   ├── p.producto-precio
│   ├── details.acordeon (Características)
│   ├── form.cantidad-form (cantidad + agregar)
│   ├── button#whatsapp-buy
│   └── a.volver-tienda
└── section.subproductos (si existen)
```

- Las miniaturas (`thumb-img`) **no son clicables**: no cambian la imagen principal.
- El acordeón usa `<details>/<summary>` nativo.
- El botón de WhatsApp actualiza su enlace al cambiar la cantidad.
- El formulario envía `POST /carrito/add/<id>` con CSRF.
- Los subproductos se muestran como enlaces con imagen.

### 4.4 Carrito (`/carrito`)

```text
div.carrito-contenedor.reveal
├── h1.carrito-titulo
├── ul.carrito-lista
│   └── li.carrito-item
│       ├── div.carrito-info (nombre, precio × cantidad)
│       ├── form (input number, onchange submit)
│       └── form (botón ×)
├── div.carrito-total
├── div.carrito-actions
│   ├── form checkout (btn-primary)
│   └── form clear (btn-ghost)
└── (vacío) div.carrito-empty
```

- El cambio de cantidad se envía automáticamente (`onchange="this.form.submit();"`).
- El botón `×` solo contiene el carácter; no tiene `aria-label`.
- El total se muestra con separador de miles y sin decimales.

### 4.5 Login y registro

- Fondo con clase `.login-page` / `.registro-page`.
- Caja centrada `.login-box` / `.registro-box`.
- Solo campos, botón y enlace para cambiar de formulario.
- No hay “recordarme”, recuperación de contraseña ni login social.

### 4.6 Panel de administración (`/admin/`)

```text
main.contenedor.mt-40.reveal
├── div.admin-caja (Pedidos)
│   └── table (Orden, Cliente, Total, Items, Estado, Fecha, Acción)
├── div.admin-caja (Categorías)
│   ├── form.flex-form (nueva categoría)
│   └── div.tag-list (tags con ×)
├── div.admin-caja (Subir Producto)
│   └── form.form-grid
└── div.admin-caja (Productos Actuales)
    └── table (Nombre, Categoría, Precio, Padre, Acción)
```

- La tabla de pedidos está dentro de `.table-responsive` (scroll horizontal).
- El botón «Ver» abre un modal dinámico con los ítems.
- La validación de campos del alta se hace en cliente con `alert()`.
- Las etiquetas de los campos son placeholders; no hay `<label>` explícito.
- La tabla de productos permite editar, crear subproducto y borrar.

### 4.7 Edición (`/admin/prod/edit/<id>`)

- Reutiliza `.admin-caja` y `.form-grid`.
- Mantiene las rutas actuales en campos ocultos `old_img1..3`.
- Avisa de que dejar una imagen en blanco conserva la actual.

---

## 5. Componentes CSS

### Botones

| Clase | Uso |
|---|---|
| `.btn` / `.boton-ver` | Base. |
| `.btn-primary` / `.boton-pagar` / `.boton-comprar` | Acción principal (dorado). |
| `.btn-secondary` / `#whatsapp-buy` | Acción secundaria (verde). |
| `.btn-danger` / `.carrito-eliminar` | Eliminar. |
| `.btn-ghost` | Acción discreta. |
| `.btn-sm`, `.btn-lg`, `.btn-block` | Tamaños. |
| `.small-btn` | Acciones de tabla. |
| `.carrito-editar` | Editar (verde). |

Todos comparten transición, `:active` con escala 0.97 y `:hover` con cambio de color.

### Toasts

```html
<div id="flash-container">
  <div class="toast success" onclick="this.remove()">Mensaje</div>
</div>
```

- Posición fija arriba a la derecha.
- Colores por categoría (`success`, `error`, `info`, `warning`).
- Se eliminan a los 4 segundos con JS.
- Clic para cerrar.

### Tablas

- `.table-responsive` con `overflow-x: auto`.
- Encabezados en mayúsculas, filas con hover.
- Estados de pedido con clases `.estado-pendiente`, `.estado-confirmado`, `.estado-cancelado` (aunque solo se usa `pendiente`).

### Modal

- `.modal-overlay` + `.modal-caja`.
- Se crea dinámicamente desde JS con `innerHTML`.
- Clic en el overlay cierra; clic dentro se detiene con `event.stopPropagation()`.
- No tiene `role="dialog"`, `aria-modal`, foco atrapado ni cierre con `Escape`.

---

## 6. JavaScript

| Archivo | Función | Detalle |
|---|---|---|
| `header.html` | Menú móvil | Alterna `.active` en `#main-menu`; actualiza `aria-expanded`; cierra al hacer clic fuera. |
| `footer.html` | Reveal | `IntersectionObserver` con `threshold: 0.16`; añade `.active` y deja de observar. |
| `_flash.html` | Toasts | `setTimeout` de 4000 ms; elimina nodos. |
| `lineaproductos.html` | Filtros | `applyFilters()` construye la URL con `encodeURIComponent` y navega. Escucha `change` en ambos selects. |
| `producto.html` | WhatsApp | `refreshWSLink()` recalcula el enlace con cantidad, nombre, precio, URL y `encodeURIComponent`. |
| `admin.html` | Validación | En `submit`, comprueba campos y lanza `alert()` si faltan. |
| `admin.html` | Modal de pedido | `verPedido(btn)` lee `data-items`, parsea JSON, genera `<li>` y monta el overlay. |

No hay `fetch`, `XMLHttpRequest`, módulos ES ni dependencias externas de JS.

---

## 7. Responsive

| Breakpoint | Cambios principales |
|---|---|
| `≤ 1024px` | Contenedor al 95 %, formularios a 1 columna, detalle a 1 columna, carrito apilado, footer a 1 columna. |
| `≤ 850px` | Menú hamburguesa visible; navegación desplegable absoluta; enlaces sin subrayado animado. |
| `≤ 768px` | Grilla a 2 columnas, tipografía 15 px, filtros apilados, toasts a ancho completo, admin con menos padding. |
| `≤ 480px` | Grilla a 1 columna, tarjetas y títulos más pequeños, subproductos a 1 columna. |

El menú móvil:

```css
@media (max-width: 850px) {
  .menu-toggle { display: flex; }
  .zona-menu { display: none; position: absolute; top: 100%; ... }
  .zona-menu.active { display: block; }
}
```

---

## 8. Accesibilidad

### Implementado

- `lang="es"` y `meta viewport`.
- `aria-label` en el botón de menú y en el logo.
- `aria-expanded` y `aria-controls` en el menú.
- `alt` en las imágenes de producto.
- `loading="lazy"` en imágenes.
- `<details>/<summary>` para el acordeón.
- Botones reales para acciones y enlaces para navegación.
- Foco visible en inputs y selects.
- Texto de los toasts legible.

### Mejorable

| Problema | Recomendación |
|---|---|
| Modal sin semántica ni foco atrapado | `role="dialog"`, `aria-modal="true"`, foco inicial, `Escape`, devolver foco. |
| Botones `×` sin nombre accesible | `aria-label="Eliminar producto"`. |
| Formularios admin solo con placeholders | `<label for>` visibles u ocultos. |
| Sin enlace «saltar al contenido» | Añadir skip link. |
| Animaciones sin `prefers-reduced-motion` | Media query para desactivar transiciones. |
| Contraste variable en texto muted | Verificar AA en `--text-muted` sobre fondos. |
| JavaScript inline | Externalizar y usar CSP sin `'unsafe-inline'`. |
| Sin mensajes de error asociados a campos | `aria-describedby` + resumen de errores. |
| Miniaturas no interactivas | Convertirlas en botones de galería. |
| Sin foco al cambiar de página | Normal en SSR; considerar `autofocus` en el primer campo. |

---

## 9. Personalización

### Cambiar colores

Edita las variables en `:root` de `static/css/style.css`. El `cache_buster()` de las imágenes y el CSS se actualiza al cambiar el `mtime` del archivo, pero el navegador puede cachear; fuerza recarga.

### Cambiar tipografías

Modifica el `@import` y las variables `--font-*`. Si eliminas Google Fonts, ajusta la CSP y las peticiones externas.

### Añadir una página

1. Crea `templates/mi-pagina.html` con el mismo esqueleto.
2. Incluye `header.html` y `footer.html`.
3. Define la ruta que la renderice.
4. Añade el enlace en `header.html` si debe ser visible.

### Cambiar el logo

El logo es texto (`<span>ARTISAN</span>`) con `--font-logo`. Para una imagen, reemplaza el contenido de `.logo-texto`.

### Añadir estilos

Sigue el orden de secciones del archivo y usa las variables existentes. Evita estilos inline nuevos; los actuales están en las plantillas por brevedad.

---

## 10. Rendimiento percibido

- Las imágenes de producto pueden pesar 8–11 MB: la carga inicial del catálogo es lenta.
- `loading="lazy"` ayuda, pero no sustituye la optimización.
- El CSS es único y pequeño (~25 KB), sin minificar.
- Las fuentes externas añaden latencia.
- La animación `reveal` puede producir saltos si el observer no se dispara (por ejemplo, sin JS).
- No hay skeletons ni placeholders de carga.

Recomendaciones: generar versiones de 800–1200 px en WebP, usar `srcset`, servir desde CDN y añadir `width`/`height` para evitar layout shift.

---

**Anterior:** [10 · Referencia de código](10-referencia-codigo.md) · **Siguiente:** [12 · Inventario →](12-inventario-archivos.md)
