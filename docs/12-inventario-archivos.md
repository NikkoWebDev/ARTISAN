# 12 · Inventario de archivos

Este documento responde a tres preguntas: **qué es cada archivo**, **cuánto pesa** y **qué entra en `artisan.zip`**. Sirve como mapa rápido del repositorio y como referencia para auditar la entrega.

> **Base:** commit `dfeec6d` (rama `main`), revisado el **25 de octubre de 2026**. Los tamaños son los del árbol de trabajo en esa fecha y pueden variar con nuevos productos o imágenes.

---

## 1. Resumen del árbol

```text
Artisan Web/
├── .github/workflows/       # CI y keep-alive (2 archivos)
├── .vscode/                 # Configuración del editor (1 archivo)
├── app/                     # Paquete Flask: fábrica, configuración y blueprints
│   └── routes/              # auth, shop, cart, admin
├── docs/                    # Esta documentación (13 archivos con este)
├── static/
│   ├── css/style.css        # Hoja de estilos única
│   └── img/                 # Logo + 29 imágenes de producto
├── templates/               # 11 plantillas Jinja2
├── database.db              # SQLite local con datos de prueba
├── db_utils.py              # Acceso a SQLite/PostgreSQL y migraciones
├── database_setup.py        # Inicialización de esquema y datos base
├── app.py / wsgi.py         # Puntos de entrada (desarrollo / producción)
├── Dockerfile / Dockerfile.prod
├── docker-compose.yml / docker-compose.prod.yml
├── requirements.txt / dev-requirements.txt
├── run.bat / run.sh
├── .env.example / .env.docker
└── README.md + documentos históricos
```

**Totales aproximados del contenido entregable:**

| Grupo | Archivos | Tamaño |
|---|---:|---:|
| Código Python (sin `__pycache__`) | 12 | ~23 KB |
| Plantillas Jinja2 | 11 | ~26 KB |
| Hoja de estilos | 1 | ~25 KB |
| Imágenes | 30 | ~108 MB |
| Documentación (`docs/`) | 13 | ~150 KB |
| Base de datos SQLite | 1 | 36 KB |
| Configuración, despliegue y scripts | ~17 | ~15 KB |
| **Total estimado** | **~85** | **~108,4 MB** |

El peso está dominado por las fotografías de producto: 29 archivos de `static/img/productos/` suman unos **100 MB** y varias pesan entre 7 y 11 MB.

---

## 2. Archivos de la raíz

| Archivo | Tipo | Para qué sirve | ¿En el ZIP? |
|---|---|---|---|
| `app.py` | Entrada | Crea la app y la ejecuta en desarrollo con `debug=True`. | Sí |
| `wsgi.py` | Entrada | Expone `app` para Gunicorn u otro WSGI. | Sí |
| `db_utils.py` | Código | `connect_db()`, `ensure_schema()`, traducción de SQLite a PostgreSQL y migraciones. | Sí |
| `database_setup.py` | Script | Crea el esquema, categorías base y admin opcional vía `INITIAL_ADMIN_*`. | Sí |
| `requirements.txt` | Config | Dependencias de ejecución (Flask, Gunicorn, psycopg2, python-dotenv, Flask-Limiter). | Sí |
| `dev-requirements.txt` | Config | Dependencias de desarrollo (pytest, etc.). | Sí |
| `.env.example` | Config | Plantilla de variables de entorno. No se carga sola. | Sí |
| `.env.docker` | Config | Variables usadas por `docker-compose.yml`. Apunta a un servicio `db` inexistente. | Sí |
| `.gitignore` | Config | Excluye `.env`, `.venv`, `__pycache__`, `database.db`, etc. | Sí |
| `.dockerignore` | Config | Excluye del contexto de build lo que no debe copiarse. | Sí |
| `Dockerfile` | Despliegue | Imagen de desarrollo; ejecuta `python app.py`. | Sí |
| `Dockerfile.prod` | Despliegue | Imagen de producción con Gunicorn. | Sí |
| `docker-compose.yml` | Despliegue | Compose de desarrollo; referencia un servicio `db` que no está definido. | Sí |
| `docker-compose.prod.yml` | Despliegue | Compose de producción con PostgreSQL. | Sí |
| `run.bat` | Script | Arranque rápido en Windows. | Sí |
| `run.sh` | Script | Arranque rápido en Linux/macOS. | Sí |
| `e2e_test.py` | Prueba | Prueba de extremo a extremo **desactualizada** (usa GET en rutas POST y no envía CSRF). | Sí |
| `database.db` | Datos | SQLite local con usuarios, categorías, un producto y un pedido de prueba. | Sí, con advertencia |
| `README.md` | Doc | Presentación, instalación, rutas y enlaces a `docs/`. | Sí |
| `CHANGELOG.md` | Doc | Historial de cambios de mayo de 2026; contiene referencias a archivos eliminados. | Sí |
| `CONTRIBUTING.md` | Doc | Guía de contribución y convenciones de commit. | Sí |
| `PRODUCTION_CHECKLIST.md` | Doc | Checklist de despliegue; corregido para usar `wsgi:app`. | Sí |
| `RELEASE.md` | Doc | Pasos de release; corregido para no invocar scripts inexistentes. | Sí |
| `LICENSE` | Legal | Licencia del proyecto. | Sí |

> ⚠️ **`database.db` contiene datos locales**: dos usuarios (`Admin` y `Tester`), un producto de ejemplo y un pedido de prueba. No incluye secretos de producción, pero conviene eliminar los usuarios de prueba antes de publicar la base. El archivo está ignorado por Git.

---

## 3. Paquete `app/`

| Archivo | Líneas | Propósito |
|---|---:|---|
| `app/__init__.py` | 61 | `create_app()`: configuración, extensiones, blueprints, CSRF, límites, manejo de errores y contexto de plantillas. |
| `app/config.py` | 18 | Clase `Config`, cookies seguras en producción y validación de `SECRET_KEY`. |
| `app/csrf.py` | 22 | Generación/validación del token CSRF en sesión. |
| `app/db.py` | 15 | `get_db()`, `close_db()` y registro en `g`. |
| `app/extensions.py` | 7 | Instancias de Flask-Limiter. |
| `app/routes/__init__.py` | 0 | Paquete de blueprints (vacío). |
| `app/routes/auth.py` | 81 | Login, registro y logout. |
| `app/routes/shop.py` | 64 | Inicio, listado, detalle de producto y WhatsApp. |
| `app/routes/cart.py` | 180 | Carrito en sesión, actualización, eliminación y checkout. |
| `app/routes/admin.py` | 246 | Panel, CRUD de productos/categorías y consulta de pedidos. |

Tamaño del código fuente: **~22 KB**. Los `.pyc` de `__pycache__` **no** se incluyen en el ZIP.

---

## 4. Plantillas (`templates/`)

| Plantilla | Líneas | Uso |
|---|---:|---|
| `header.html` | 50 | Cabecera, navegación, sesión, carrito y flashes. |
| `footer.html` | 46 | Pie, enlaces y cierre de layout. |
| `_flash.html` | 14 | Renderizado de mensajes flash. |
| `index.html` | 27 | Página de inicio. |
| `lineaproductos.html` | 70 | Catálogo con filtro por categoría. |
| `producto.html` | 76 | Detalle, subproductos y añadir al carrito. |
| `carrito.html` | 54 | Carrito y botón de checkout por WhatsApp. |
| `login.html` | 27 | Inicio de sesión. |
| `registro.html` | 27 | Registro de clientes. |
| `admin.html` | 169 | Panel de administración y pedidos. |
| `edit_product.html` | 44 | Edición de producto. |

Total: **~26 KB**. No hay herencia con `base.html`; cada página incluye header y footer mediante `{% include %}`.

---

## 5. Recursos estáticos

### 5.1 CSS

| Archivo | Tamaño | Contenido |
|---|---:|---|
| `static/css/style.css` | ~25 KB | Estilos globales, layout, tarjetas, carrito, panel admin, formularios y responsive. Es la única hoja de estilos. |

### 5.2 Imágenes

| Ubicación / familia | Archivos | Peso aproximado | Observaciones |
|---|---:|---:|---|
| `static/img/IMG_20260121_150438.jpg` | 1 | 8,1 MB | Imagen suelta en la raíz de `img/`; no está referenciada por el catálogo por defecto. |
| `static/img/productos/` | 29 | 100,1 MB | Fotos de producto y placeholders. |
| **Total** | **30** | **~108,2 MB** | |

**Familias de imágenes de producto:**

| Familia | Archivos | Peso | Nota |
|---|---:|---:|---|
| `Pulsera_Mostacilla_1_pul_mosta_0_*` | 7 | ~2,7 MB | Set más completo (vistas 1–7). |
| `joyas_aajjaja_1_*` | 3 | ~23 MB | Tres fotos de ~7,5–8 MB. |
| `sdfgh_*` | 4 | ~30 MB | Incluye duplicados exactos con otros nombres. |
| `Manilla_Delica_*` | 2 | ~406 KB | Variantes de 2 y 3 líneas. |
| `323r4_1_*` | 1 | 9,3 MB | Foto individual. |
| `aretes_en_mostacilla_1_*` | 1 | 7,8 MB | Duplicada con dos nombres `sdfgh*`. |
| `casdfg_1_*` | 1 | 11,3 MB | La imagen más pesada del proyecto. |
| `sdf_1_*`, `zxcvb23456_1_*` | 2 | ~15 MB | Fotos individuales. |
| Placeholders PNG | 8 | 9 bytes en total | Archivos de 1 byte (y uno de 4 bytes) que no renderizan. |

**Placeholders de 1 byte:** `MainProd_1_a.png`, `Primero_1_a.png`, `ProdBisuteria_1_a.png`, `ProdMarroquineria_1_a.png`, `Segundo_1_b.png`, `Segundo_1_c.png`, `SubProd_1_b.png` y `Prueba_1_img1.png` (4 bytes). Son residuos de pruebas; no deben usarse como imagen por defecto.

**Duplicados exactos (MD5):**

| Grupo | Archivos | Acción sugerida |
|---|---|---|
| 3 copias | `aretes_en_mostacilla_1_IMG_20260120_142208.jpg`, `sdfgh_1_IMG_20260120_142208.jpg`, `sdfghsdfghjdfgh_1_IMG_20260120_142208.jpg` | Conservar una y actualizar referencias. |
| 3 copias | `Manilla_Delica_2_lineas_1_pul_mosta_0_1.jpg`, `Manilla_Delica_3_lineas_1_pul_mosta_0_1.jpg`, `Pulsera_Mostacilla_1_pul_mosta_0_1.jpg` | Verificar cuál corresponde a cada producto. |
| 2 copias | `joyas_aajjaja_1_IMG_20260120_142717.jpg`, `sdfgh_3_IMG_20260120_142717.jpg` | Conservar una. |
| 6 copias de 1 byte | Los PNG listados arriba (excepto `Prueba_1_img1.png`) | Eliminar o reemplazar por una imagen real. |

Deduplicar estos grupos permitiría ahorrar varios MB, aunque el ahorro principal vendría de recomprimir las fotos de 7–11 MB.

---

## 6. Documentación (`docs/`)

| Archivo | Tamaño | Contenido |
|---|---:|---|
| `README.md` | ~4,5 KB | Índice, convenciones y fuentes de verdad. |
| `01-arquitectura.md` | ~11,5 KB | Fábrica de aplicación, blueprints, ciclo de petición. |
| `02-instalacion.md` | ~8,2 KB | Entorno local, variables, Docker y problemas frecuentes. |
| `03-base-de-datos.md` | ~15 KB | Esquema, relaciones, migraciones y respaldos. |
| `04-rutas.md` | ~14,2 KB | Referencia completa de endpoints. |
| `05-flujos.md` | ~13,1 KB | Registro, catálogo, carrito, checkout y admin. |
| `06-whatsapp.md` | ~8,3 KB | Construcción del mensaje y configuración del número. |
| `07-seguridad.md` | ~13,5 KB | Controles, riesgos y checklist. |
| `08-despliegue.md` | ~15,5 KB | Docker, Gunicorn, PostgreSQL, Render y CI. |
| `09-operacion-mantenimiento.md` | ~13,4 KB | Runbook, pruebas, problemas conocidos y roadmap. |
| `10-referencia-codigo.md` | ~13,7 KB | Referencia archivo por archivo. |
| `11-interfaz-ui.md` | ~12,5 KB | Sistema de diseño, componentes y accesibilidad. |
| `12-inventario-archivos.md` | ~10 KB | Este documento. |

Todos los documentos están en español y enlazados desde `docs/README.md` y `README.md`.

---

## 7. Automatización y editor

| Archivo | Tamaño | Propósito |
|---|---:|---|
| `.github/workflows/ci.yml` | 912 B | Instala dependencias y ejecuta comprobaciones/pruebas en cada push o PR. |
| `.github/workflows/keep-alive.yml` | 333 B | Ping periódico para evitar que un servicio gratuito se duerma. |
| `.vscode/settings.json` | 351 B | Configuración local del editor (interprete, formato). |

---

## 8. Carpetas excluidas del ZIP

| Carpeta/archivo | Motivo de exclusión |
|---|---|
| `.git/` | Historial y metadatos de Git; no forma parte del entregable. |
| `.venv/` | Entorno virtual local; se recrea con `requirements.txt`. |
| `__pycache__/` (raíz y `app/`) | Bytecode generado; innecesario y dependiente de la versión de Python. |
| `__MACOSX/` | Residuos de macOS (2.343 archivos, ~374 KB). |
| `Flask_HTML_Sample/` | Proyecto de ejemplo ajeno (2.745 archivos, ~50 MB). |
| `github.copilot-chat-0.37.9.vsix` | Extensión de VS Code de 20 MB; no es parte del proyecto. |

También se excluyen archivos temporales, `.pyc`, `.log` y cualquier `.env` real con secretos.

---

## 9. Contenido del ZIP

`artisan.zip` se genera en la raíz del proyecto e incluye:

- Código: `app/`, `db_utils.py`, `database_setup.py`, `app.py`, `wsgi.py`.
- Plantillas: `templates/`.
- Recursos: `static/css/` y `static/img/` (todas las imágenes).
- Documentación: `docs/`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `PRODUCTION_CHECKLIST.md`, `RELEASE.md`, `LICENSE`.
- Configuración y despliegue: `requirements.txt`, `dev-requirements.txt`, `.env.example`, `.env.docker`, `.gitignore`, `.dockerignore`, `Dockerfile`, `Dockerfile.prod`, `docker-compose.yml`, `docker-compose.prod.yml`, `run.bat`, `run.sh`.
- Automatización: `.github/`, `.vscode/`.
- Pruebas: `e2e_test.py` (con la advertencia de que está desactualizado).
- Datos locales: `database.db`.

**No incluye** `.git/`, `.venv/`, `__pycache__/`, `__MACOSX/`, `Flask_HTML_Sample/` ni el `.vsix` de Copilot. El ZIP resultante ronda los **108 MB**, casi todo imágenes.

### Verificación rápida tras descomprimir

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python database_setup.py
python app.py
```

Abre `http://127.0.0.1:5000`. Si usas PostgreSQL o producción, revisa [Instalación](02-instalacion.md) y [Despliegue](08-despliegue.md) antes de arrancar.

---

## 10. Archivos que conviene revisar o eliminar

| Archivo | Situación | Recomendación |
|---|---|---|
| `e2e_test.py` | Usa GET en `/carrito/add/1` y no envía CSRF; falla con el código actual. | Reescribir con POST, token CSRF y sesión. |
| `database.db` | Datos de prueba y usuarios demo. | No publicar; regenerar con `database_setup.py`. |
| `.env.docker` | Apunta a `db:5432`, pero no existe servicio `db`. | Corregir o eliminar. Ver [Despliegue §9](08-despliegue.md#9-problemas-conocidos-de-docker). |
| `docker-compose.yml` / `docker-compose.prod.yml` | Configuración inconsistente (variables `DB_*` vs `POSTGRES_*`, placeholders). | Revisar antes de usar. |
| Imágenes de 1 byte | No renderizan. | Sustituir por una imagen real o un placeholder válido. |
| Fotos de 7–11 MB | Ralentizan la carga. | Recomprimir a WebP/JPEG ~200–500 KB. |
| `CHANGELOG.md`, `RELEASE.md` | Referencias a scripts eliminados. | Ya corregidas las referencias principales; el historial se conserva como registro. |

---

## 11. Cómo regenerar este inventario

Desde la raíz del proyecto:

```powershell
# Conteo y tamaño por carpeta
Get-ChildItem app,templates,static,docs -Recurse -File |
  Group-Object { $_.DirectoryName.Split('\')[0] } |
  Select-Object Name, Count, @{n='MB';e={[math]::Round(($_.Group | Measure-Object Length -Sum).Sum/1MB,2)}}

# Duplicados por MD5
Get-ChildItem static -Recurse -File -Include *.jpg,*.png |
  Get-FileHash -Algorithm MD5 |
  Group-Object Hash | Where-Object Count -gt 1
```

Actualiza las tablas cuando añadas productos, imágenes o documentos.

---

**Volver al [índice](README.md)** · **Ver [despliegue](08-despliegue.md)** · **Ver [operación](09-operacion-mantenimiento.md)**
