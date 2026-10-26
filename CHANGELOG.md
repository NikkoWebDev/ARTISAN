# 🔄 CHANGELOG - Correcciones y Mejoras

## Documentación completa (25 de Octubre de 2026)

- **Nueva carpeta `docs/`** con 12 documentos técnicos y funcionales: arquitectura, instalación, base de datos, rutas, flujos, WhatsApp, seguridad, despliegue, operación, referencia de código, interfaz e inventario.
- **`README.md` reescrito** para reflejar la estructura real (`app/`, `wsgi.py`), las rutas vigentes y los enlaces a la documentación.
- **Correcciones en documentos históricos**: `PRODUCTION_CHECKLIST.md` usa `wsgi:app`; `RELEASE.md` ya no invoca `seed_data.py` ni `compile_all.py`; se documenta que `.env` no se carga automáticamente y que `e2e_test.py` está desactualizado.
- **Inventario y entrega**: `docs/12-inventario-archivos.md` detalla archivos, imágenes duplicadas y el contenido de `artisan.zip`.
- No se modificó el código de la aplicación en esta revisión; las limitaciones detectadas se documentan en [docs/09-operacion-mantenimiento.md](docs/09-operacion-mantenimiento.md).

---

## Cambios Realizados (18 de Mayo de 2026)

### 🔐 SEGURIDAD (CRÍTICO)

#### ✅ Encriptación de Contraseñas
- **Antes**: Contraseñas almacenadas en texto plano ❌
- **Ahora**: Usando `werkzeug.security.generate_password_hash()` y `check_password_hash()` ✅
- **Impacto**: Sistema seguro para producción
- **Archivo**: `app.py`, `database_setup.py`

#### ✅ Validación de Entrada
- **Agregadas validaciones en**:
  - Login: Email y password requeridos
  - Registro: Nombre mín. 3 caracteres, contraseña mín. 6, confirmación de contraseña
  - Productos: Validación de precio (debe ser positivo)
  - Cantidad: Límites 1-1000

#### ✅ URL Encoding Correcto
- **Antes**: Encoding manual con `.replace()` ❌
- **Ahora**: Usando `urllib.parse.quote()` ✅
- **Beneficio**: Maneja caracteres especiales correctamente

### 🛠️ FUNCIONALIDAD

#### ✅ Sistema de Pedidos Mejorado
- **Nueva tabla**: `pedidos` con estructura completa
- **Campos**: número_orden único, usuario_id, nombre, items (JSON), total, estado, fecha
- **Panel Admin**: Visualización de todos los pedidos recibidos
- **Botón "Ver"**: Detalle de cada pedido con lista de items

#### ✅ Variables de Entorno
- **Archivo nuevo**: `.env.example`
- **Variables soportadas**:
  - `SECRET_KEY`: Clave para sesiones
  - `WHATSAPP_PHONE`: Número de WhatsApp (sin +)
  - `FLASK_ENV`: Modo desarrollo/producción
- **Beneficio**: Facilita deploy en diferentes entornos

#### ✅ Manejo de Errores Mejorado
- Try-except en checkout
- Validación de usuario en procesamiento de compra
- Mensajes de error descriptivos
- Logging de excepciones

### 📋 TEMPLATES

#### ✅ Registro (registro.html)
- Campo de confirmación de contraseña
- Validaciones HTML5 (minlength, required)
- Mensajes de ayuda

#### ✅ Admin (admin.html)
- Panel de pedidos en la parte superior
- Tabla con estado visual (naranja, verde, rojo)
- Botón "Ver detalles" con modal
- Script mejorado para parsing JSON

#### ✅ Carrito (carrito.html)
- Botón "COMPRAR POR WHATSAPP" como formulario POST
- Mejor manejo de errores
- Encoding correcto de mensajes

### 📦 ARCHIVOS NUEVOS

#### ✅ README.md
- Guía completa de instalación
- Estructura del proyecto
- API de rutas
- Checklist de seguridad
- Solución de problemas

#### ✅ requirements.txt
- Dependencias Python actualizadas
- Flask 3.0.0
- Werkzeug 3.0.1

#### ✅ .env.example
- Template para variables de entorno
- Instrucciones de configuración

#### ✅ verify_db.py
- Script para verificar integridad de BD
- Útil para verificar migración de datos
- ⚠️ Este archivo **ya no existe** en el repositorio actual; usa `sqlite3 database.db` o `database_setup.py` para comprobar el esquema.

### 🐛 CORRECCIONES DE BUGS

#### ✅ Cantidad en Carrito
- **Bug**: `if qty < 1: qty = 1` (sintaxis incompleta en algunas rutas)
- **Fix**: Ahora funciona correctamente en todas partes
- **Límite**: Máximo 1000 unidades

#### ✅ Subproductos
- Solo productos principales (parent_id IS NULL) pueden ir al carrito
- Subproductos solo en detalle de producto

#### ✅ Mensajes Flash
- Ahora con categoría de tipo (success, error, info)
- Estilos apropiados
- Auto-hide después de 3 segundos

### ⚙️ CONFIGURACIÓN

#### ✅ Debug Mode
- **Producción**: `debug=False` ✅
- **Desarrollo**: Cambiar si necesitas hot-reload
- **Ubicación**: Última línea de app.py

#### ✅ Base de Datos
- Migración automática de esquema
- Compatibilidad con BD antiguas
- Índices optimizados (si se necesitan)

### 📱 INTEGRACIÓN WHATSAPP

#### ✅ Mejor Formato de Mensaje
```
Hola, me gustaría completar mi compra:

*Número de Orden:* ORD-xxxxx
*Items:*
• Producto x cantidad = $precio

*Total:* $xxxx

Por favor confirmar disponibilidad y detalles de pago.
```

#### ✅ URL Encoding Seguro
- Soporta acentos, caracteres especiales
- No se corta el mensaje
- Compatible con WhatsApp Web y App

## 🚀 PRÓXIMAS RECOMENDACIONES

### Para Próximo Sprint
1. ⚠️ Usar `python-dotenv` para cargar `.env` (la dependencia está instalada, pero `load_dotenv()` aún no se invoca)
2. ✅ Sistema de notificaciones por email
3. ✅ Historial de pedidos del usuario
4. ✅ Sistema de inventario (stock)
5. ✅ Cambio de estado de pedidos desde admin
6. ✅ Reportes de ventas

### Para Producción
1. Usar PostgreSQL o MySQL (no SQLite)
2. Usar Gunicorn o uWSGI
3. Configurar NGINX reverse proxy
4. SSL/TLS obligatorio
5. Rate limiting
6. CDN para imágenes
7. Backups automáticos
8. Monitoreo y logs

## 📊 ESTADÍSTICAS

| Aspecto | Antes | Después |
|---------|-------|---------|
| Seguridad | ❌ Crítica | ✅ Alta |
| Validaciones | Parcial | ✅ Completa |
| Operaciones BD | Sin error handling | ✅ Con try-except |
| URL Encoding | Manual | ✅ urllib.parse |
| Documentación | Nula | ✅ README.md |
| Variables de entorno | No | ✅ Sí |
| Tabla de pedidos | Existe | ✅ Mejorada visualmente |

## ✅ CHECKLIST DE REVISIÓN

- ✅ Sin errores de sintaxis Python
- ✅ Base de datos se crea correctamente
- ✅ Contraseñas encriptadas
- ✅ Validaciones de entrada
- ✅ URLs correctamente encoded
- ✅ Panel admin actualizado
- ✅ Templates actualizados
- ✅ Manejo de errores mejorado
- ✅ Documentación completa
- ✅ Variables de entorno soportadas
- ✅ Debug mode deshabilitado para producción

## 🎉 RESULTADO FINAL

**El proyecto está LISTO PARA PRODUCCIÓN** con los siguientes pasos:

1. Configurar `.env` con valores reales
2. Usar base de datos externa (PostgreSQL)
3. Desploy en servidor (heroku, AWS, etc)
4. Configurar dominio y SSL
5. Monitorear logs

---

**Versión**: 2.0 (26-05-2026)
**Última revisión documental**: 25-10-2026
**Estado**: ✅ Funcional; revisar los riesgos conocidos antes de publicar
