# 03 · Base de datos

## 1. Motores soportados

`db_utils.py` elige el motor al importar el módulo:

```python
DATABASE_URL = os.environ.get('DATABASE_URL')

def using_postgres():
    return bool(DATABASE_URL and DATABASE_URL.startswith('postgres'))
```

| Condición | Motor | Driver |
|---|---|---|
| `DATABASE_URL` empieza por `postgres` | PostgreSQL | `psycopg2-binary` |
| Cualquier otro caso | SQLite | `sqlite3` (stdlib) |

Ruta SQLite: `SQLITE_PATH` o `database.db` en el directorio de trabajo. Si la carpeta no existe, se crea.

> `DATABASE_URL` se lee **una sola vez al importar** `db_utils`. Cambiarla en caliente no tiene efecto; hay que reiniciar el proceso.

---

## 2. Capa de abstracción (`DatabaseConnection`)

```python
class DatabaseConnection:
    def execute(query, params=None) -> cursor
    def commit()
    def close()
```

Comportamiento:

- **Placeholders:** convierte `?` en `%s` para PostgreSQL.
- **`INSERT OR IGNORE`:** en PostgreSQL se reemplaza por `INSERT`, perdiendo la semántica de ignorar duplicados. Los llamadores deben tolerar la excepción.
- **Parámetros:** normaliza escalares a lista; acepta listas y tuplas.
- **Cursores:** SQLite usa `sqlite3.Row`; PostgreSQL usa `RealDictCursor`. Ambos permiten acceso por nombre (`row['campo']`).
- **Transacciones:** PostgreSQL con `autocommit = False`; SQLite implícito. Cada ruta llama `commit()` explícitamente.
- **SQLite:** activa `PRAGMA foreign_keys = ON` y `PRAGMA busy_timeout = 3000`.
- **Cierre:** `get_db()` guarda la conexión en `flask.g`; `close_db()` la cierra al finalizar el request.

No hay ORM, pool de conexiones, migrador (Alembic) ni tabla de versiones de esquema.

---

## 3. Diagrama entidad-relación

```text
┌────────────────────┐
│ usuarios           │
│────────────────────│
│ id (PK)            │
│ nombre             │
│ correo (UNIQUE)    │
│ password (hash)    │
│ rol                │
└─────────┬──────────┘
          │ 1
          │
          │ N
┌─────────▼──────────┐         ┌────────────────────┐
│ pedidos            │         │ categorias         │
│────────────────────│         │────────────────────│
│ id (PK)            │         │ id (PK)            │
│ numero_orden (UQ)  │         │ nombre (UNIQUE)    │
│ usuario_id (FK)    │         └────────────────────┘
│ usuario_nombre     │                  ▲
│ usuario_celular    │                  │ (relación lógica
│ items (JSON texto) │                  │  por nombre, sin FK)
│ total              │                  │
│ estado             │         ┌────────┴───────────┐
│ fecha_creacion     │         │ productos          │
└────────────────────┘         │────────────────────│
                               │ id (PK)            │
                               │ nombre             │
                               │ categoria (texto)  │
                               │ precio             │
                               │ descripcion        │
                               │ imagen_url         │
                               │ img2               │
                               │ img3               │
                               │ parent_id (self)   │
                               └─────────┬──────────┘
                                         │ 1
                                         │ N (auto-referencia
                                         │    lógica, sin FK)
                                         ▼
                                   productos hijos
```

**Relaciones reales en la BD:** solo `pedidos.usuario_id → usuarios.id`.
**Relaciones lógicas sin FK:** `productos.categoria → categorias.nombre`, `productos.parent_id → productos.id`.

---

## 4. Diccionario de datos

### 4.1 `usuarios`

| Columna | SQLite | PostgreSQL | Reglas | Descripción |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | SERIAL PK | Único | Identificador. |
| `nombre` | TEXT | TEXT | Obligatorio en registro, mín. 3 | Nombre visible. |
| `correo` | TEXT UNIQUE | TEXT UNIQUE | Obligatorio | Login. |
| `password` | TEXT | TEXT | Obligatorio | Hash scrypt de Werkzeug, nunca texto plano. |
| `rol` | TEXT | TEXT | `cliente` o `admin` | Control de acceso. |

### 4.2 `categorias`

| Columna | Tipo | Reglas | Descripción |
|---|---|---|---|
| `id` | PK autoincremental | Único | Identificador. |
| `nombre` | TEXT | UNIQUE, no vacío en la práctica | Nombre mostrado. |

### 4.3 `productos`

| Columna | Tipo | Reglas | Descripción |
|---|---|---|---|
| `id` | PK autoincremental | Único | Identificador. |
| `nombre` | TEXT | Obligatorio al crear | Nombre del producto. |
| `categoria` | TEXT | Obligatorio | Copia del nombre de categoría (no FK). |
| `precio` | REAL | > 0 | Precio en COP. |
| `descripcion` | TEXT | Obligatorio al crear | Texto con saltos de línea. |
| `imagen_url` | TEXT | Puede quedar `NULL` si la imagen falla | Ruta `/static/img/productos/...` o legado relativo. |
| `img2` | TEXT | Opcional | Segunda imagen. |
| `img3` | TEXT | Opcional | Tercera imagen. |
| `parent_id` | INTEGER | Opcional, sin FK | Si no es `NULL`, el producto es subproducto del indicado. |

Los productos con `parent_id IS NULL` son los únicos que aparecen en catálogo y pueden añadirse al carrito.

### 4.4 `pedidos`

| Columna | Tipo | Reglas | Descripción |
|---|---|---|---|
| `id` | PK autoincremental | Único | Identificador interno. |
| `numero_orden` | TEXT | UNIQUE | `ORD-<timestamp Unix en segundos>`. |
| `usuario_id` | INTEGER | FK → `usuarios.id` | Autor. |
| `usuario_nombre` | TEXT | Copia histórica | Nombre al momento de comprar. |
| `usuario_celular` | TEXT | **Sin uso** | Reservado; el checkout no lo rellena. |
| `items` | TEXT | JSON serializado | Lista de ítems validados. |
| `total` | REAL | > 0 recalculado | Suma desde la BD. |
| `estado` | TEXT | `pendiente` por defecto | No hay UI para cambiarlo. |
| `fecha_creacion` | DATETIME / TIMESTAMPTZ | `CURRENT_TIMESTAMP` | Fecha de creación. |

Formato de `items`:

```json
[
  {"id": 1, "nombre": "Producto de ejemplo", "precio": 19.99, "cantidad": 2}
]
```

`precio` y `nombre` se copian de la BD en el checkout (no se confía en la sesión).

---

## 5. Esquema SQL

### 5.1 SQLite (`ensure_schema`)

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    correo TEXT UNIQUE,
    password TEXT,
    rol TEXT
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    categoria TEXT,
    precio REAL,
    descripcion TEXT,
    imagen_url TEXT,
    img2 TEXT,
    img3 TEXT,
    parent_id INTEGER
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_orden TEXT UNIQUE,
    usuario_id INTEGER,
    usuario_nombre TEXT,
    usuario_celular TEXT,
    items TEXT,
    total REAL,
    estado TEXT DEFAULT 'pendiente',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
```

### 5.2 PostgreSQL

Equivalente con `SERIAL PRIMARY KEY`, `TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP` y la misma FK. Se ejecuta el mismo `CREATE TABLE IF NOT EXISTS` en `ensure_schema`.

---

## 6. Migraciones automáticas

`ensure_schema()` se llama en **cada nueva conexión** (`get_db()`), por lo que la app repara esquemas incompletos sin intervención.

1. Ejecuta todos los `CREATE TABLE IF NOT EXISTS`.
2. Lee columnas con `table_columns()`:
   - SQLite: `PRAGMA table_info(<tabla>)`.
   - PostgreSQL: `information_schema.columns WHERE table_name = %s`.
3. Añade columnas faltantes:

| Tabla | Columna | SQL de migración |
|---|---|---|
| `productos` | `img2` | `ALTER TABLE productos ADD COLUMN img2 TEXT` |
| `productos` | `img3` | `ALTER TABLE productos ADD COLUMN img3 TEXT` |
| `productos` | `parent_id` | `ALTER TABLE productos ADD COLUMN parent_id INTEGER` |
| `pedidos` | `usuario_nombre` | `ALTER TABLE pedidos ADD COLUMN usuario_nombre TEXT` |
| `pedidos` | `usuario_celular` | `ALTER TABLE pedidos ADD COLUMN usuario_celular TEXT` |
| `pedidos` | `items` | `ALTER TABLE pedidos ADD COLUMN items TEXT` |
| `pedidos` | `total` | `ALTER TABLE pedidos ADD COLUMN total REAL` |
| `pedidos` | `estado` | `ALTER TABLE pedidos ADD COLUMN estado TEXT DEFAULT "pendiente"` |
| `pedidos` | `fecha_creacion` | `ALTER TABLE pedidos ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP` |

> ⚠️ **Migración problemática en SQLite:** SQLite no permite `ADD COLUMN` con un valor por defecto no constante (`CURRENT_TIMESTAMP`). Si una base antigua no tiene `fecha_creacion`, el `ALTER TABLE` fallará. Solución manual: crear la columna sin default y rellenar los valores, o recrear la tabla. Las instalaciones nuevas no se ven afectadas porque la columna ya existe en el `CREATE TABLE`.

No hay control de versiones ni migraciones hacia atrás. Para cambios destructivos hay que diseñar el script a mano.

---

## 7. Datos iniciales

`database_setup.py`:

```python
INSERT OR IGNORE INTO usuarios (nombre, correo, password, rol) VALUES ('Admin', <email>, <hash>, 'admin')
INSERT OR IGNORE INTO categorias (nombre) VALUES ('Bisutería')
INSERT OR IGNORE INTO categorias (nombre) VALUES ('Marroquinería')
```

La base incluida en el proyecto de ejemplo contiene datos de prueba:

| Tabla | Filas | Detalle |
|---|---|---|
| `usuarios` | 2 | `Admin` (admin) y `Tester` (cliente). |
| `categorias` | 3 | Bisutería, Marroquinería, Ejemplos. |
| `productos` | 1 | «Producto de ejemplo», categoría «Ejemplos». |
| `pedidos` | 1 | Orden de prueba `ORD-1779210113`. |

> La base local se excluye de Git por `.gitignore`, pero **sí se incluye en `artisan.zip`** para conservar los datos de ejemplo. No la publiques si llegara a contener datos reales.

---

## 8. Consultas principales

| Uso | Consulta | Archivo |
|---|---|---|
| Login | `SELECT * FROM usuarios WHERE correo = ?` | `auth.py` |
| Categorías | `SELECT * FROM categorias` | `shop.py`, `admin.py` |
| Nombres por categoría | `SELECT DISTINCT nombre FROM productos WHERE categoria = ? AND parent_id IS NULL` | `shop.py` |
| Catálogo | `SELECT * FROM productos WHERE parent_id IS NULL [AND categoria = ?] [AND nombre = ?] ORDER BY id DESC` | `shop.py` |
| Detalle | `SELECT * FROM productos WHERE id = ?` | `shop.py` |
| Subproductos | `SELECT * FROM productos WHERE parent_id = ?` | `shop.py` |
| Producto del carrito | `SELECT id, nombre, precio FROM productos WHERE id = ? AND parent_id IS NULL` | `cart.py` |
| Crear pedido | `INSERT INTO pedidos (...) VALUES (?, ?, ?, ?, ?, 'pendiente')` | `cart.py` |
| Panel admin | `SELECT p.*, parent.nombre AS parent_name FROM productos p LEFT JOIN productos parent ON p.parent_id = parent.id ...` | `admin.py` |
| Pedidos | `SELECT * FROM pedidos ORDER BY fecha_creacion DESC` | `admin.py` |

Todas usan parámetros; no hay concatenación de valores de usuario en SQL (solo la lista de condiciones fijas en `lineaproductos`).

---

## 9. Diferencias SQLite ↔ PostgreSQL

| Aspecto | SQLite | PostgreSQL |
|---|---|---|
| Conexión | Archivo local | Servidor TCP. |
| Autoincremento | `AUTOINCREMENT` | `SERIAL`. |
| Booleanos/fechas | Dinámicos | Tipados (`TIMESTAMPTZ`). |
| `INSERT OR IGNORE` | Soportado | **No**; se transforma en `INSERT` y puede fallar por duplicado. |
| `?` | Soportado | Convertido a `%s`. |
| `fecha_creacion` | `str` o `None` | `datetime` (psycopg2). |
| Admin (`admin.html`) | `p['fecha_creacion'][:10]` funciona con texto. | ⚠️ Falla con `datetime` porque no soporta slicing. |
| Migración con `CURRENT_TIMESTAMP` | ⚠️ No permitida en `ADD COLUMN`. | Permitida. |
| Concurrencia | Bloqueo de archivo (`busy_timeout`). | MVCC. |
| Backup | Copia del archivo / `VACUUM INTO`. | `pg_dump`. |

### Recomendaciones para PostgreSQL

- Corregir el formateo de fechas en el panel admin (usar `strftime`/`str()` o un filtro Jinja).
- Reemplazar `INSERT OR IGNORE` por `INSERT ... ON CONFLICT DO NOTHING` en `DatabaseConnection` o en cada consulta.
- Añadir índices:

```sql
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);
CREATE INDEX IF NOT EXISTS idx_productos_parent ON productos(parent_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_creacion DESC);
```

---

## 10. Respaldos y restauración

### SQLite

```bash
# Copia consistente (recomendado, con la app detenida)
cp database.db backups/database-$(date +%Y%m%d-%H%M%S).db

# Alternativa sin detener la app
sqlite3 database.db ".backup 'backups/database.db'"
# o
sqlite3 database.db "VACUUM INTO 'backups/database.db'"
```

Restaurar: detén la app, reemplaza `database.db`, verifica permisos y arranca.

### PostgreSQL

```bash
pg_dump "$DATABASE_URL" --format=custom --file=backups/artisan-$(date +%F).dump
pg_restore --clean --if-exists --dbname="$DATABASE_URL" backups/artisan-2026-10-25.dump
```

### Imágenes

Las imágenes viven en `static/img/productos/`. Respáldalas junto con la BD; no están dentro de la base de datos.

### Migrar SQLite → PostgreSQL

No hay script incluido. Procedimiento sugerido:

1. Crea la base y el usuario en PostgreSQL.
2. Configura `DATABASE_URL`.
3. Ejecuta `python database_setup.py` para crear el esquema.
4. Exporta/importa filas respetando el orden: `usuarios` → `categorias` → `productos` → `pedidos`.
5. Reinicia secuencias (`setval`) para que los `id` no colisionen.
6. Verifica conteos y relaciones.

---

## 11. Integridad y mantenimiento

- No hay `ON DELETE CASCADE`; borrar un producto padre deja subproductos huérfanos.
- Borrar una categoría no actualiza `productos.categoria`.
- No hay validación de que `parent_id` exista, sea principal o distinto del propio producto (puede crearse un ciclo o auto-referencia).
- `numero_orden` puede colisionar si dos compras ocurren en el mismo segundo; la segunda falla por UNIQUE y el checkout muestra error genérico.
- No hay stock, reservas ni bloqueo de inventario.
- No hay tareas de limpieza de imágenes huérfanas.
- No hay índices adicionales más allá de los UNIQUE.

---

**Anterior:** [02 · Instalación](02-instalacion.md) · **Siguiente:** [04 · Rutas →](04-rutas.md)
