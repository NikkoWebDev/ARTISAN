# 06 · Integración con WhatsApp

## 1. Enfoque actual

Artisan **no** usa la API de WhatsApp. Genera enlaces `wa.me` / `api.whatsapp.com` que abren la aplicación o WhatsApp Web con un mensaje preescrito. La conversación y el pago se cierran manualmente entre cliente y vendedor.

```text
Servidor Flask                          Navegador                     WhatsApp
     │                                      │                            │
     ├─ renderiza botón con URL ───────────►│                            │
     │                                      ├─ click ───────────────────►│
     │                                      │   api.whatsapp.com/send    │
     │                                      │   ?phone=...&text=...      │
     │                                      │                            ├─ chat abierto
     │                                      │                            │  con mensaje
```

Ventajas: sin credenciales, sin coste, sin webhooks.
Limitaciones: sin confirmación de entrega, sin automatización, sin historial en el sistema, depende de que el usuario tenga WhatsApp.

---

## 2. Configuración del número

```python
# app/__init__.py
WHATSAPP_PHONE = os.environ.get('WHATSAPP_PHONE', '573123580705').lstrip('+').strip()
```

| Regla | Detalle |
|---|---|
| Formato | Internacional, solo dígitos, sin `+`, sin espacios ni guiones. |
| Ejemplo Colombia | `573123580705` (57 = país, 3123580705 = móvil). |
| Valor por defecto | `573123580705`. |
| Momento de lectura | Al importar `app/__init__.py`. |
| Dónde se usa | `cart.py` (checkout), `producto.html` (botón directo), `footer.html` (enlace de contacto). |

No hay validación del número. Un valor vacío genera enlaces sin destinatario (`?phone=&text=...`).

Para cambiarlo:

```bash
# PowerShell
$env:WHATSAPP_PHONE = "573001234567"
python app.py
```

```env
# .env (solo si usas `dotenv run` o Docker)
WHATSAPP_PHONE=573001234567
```

> En Docker, el valor viene de `env_file` (`.env.docker`).

---

## 3. Puntos de integración

### 3.1 Compra directa desde la ficha (`producto.html`)

```javascript
var qty = document.querySelector('input[name="cantidad"]').value;
var prod = "{{ p.nombre }}";
var price = "{{ '{:,.0f}'.format(p.precio) }}";
var link = window.location.origin + "/producto/{{ p.id }}";
var msg = "Quiero comprar " + qty + " de " + prod + " a " + price + " COP cada uno. " + link;
var url = 'https://api.whatsapp.com/send?phone=' + whatsappPhone + '&text=' + encodeURIComponent(msg);
```

- El mensaje se actualiza al cambiar la cantidad (`input`).
- El precio se formatea con separador de miles y sin decimales.
- La cantidad **no** se limita en JavaScript; el `min="1"` es solo una restricción HTML.
- No se crea pedido en la BD.

### 3.2 Checkout del carrito (`cart.py`)

```python
msg_items = "\n".join(
    f"• {it['nombre']} x{it['cantidad']} = ${it['precio'] * it['cantidad']:,.0f}"
    for it in validated_items
)
msg = f"""Hola, me gustaría completar mi compra:

*Número de Orden:* {order_num}

*Items:*
{msg_items}

*Total:* ${total:,.0f}

Por favor confirmar disponibilidad y detalles de pago."""

whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_PHONE}&text={quote(msg)}"
```

- Usa `urllib.parse.quote`, que codifica saltos de línea, acentos, `*`, `$`, etc.
- Los ítems y el total provienen de la BD, no de la sesión.
- El pedido ya está insertado en `pedidos` cuando se genera el enlace.
- El carrito se vacía antes de la redirección.

### 3.3 Enlaces del footer

```html
<a href="https://wa.me/{{ WHATSAPP_PHONE }}" target="_blank" rel="noopener noreferrer">WhatsApp</a>
<a href="https://wa.me/{{ WHATSAPP_PHONE }}" rel="noopener noreferrer">+{{ WHATSAPP_PHONE }}</a>
```

---

## 4. Plantillas de mensaje

### 4.1 Carrito

```text
Hola, me gustaría completar mi compra:

*Número de Orden:* ORD-1779210113

*Items:*
• Pulsera mostacilla x2 = $40,000
• Aretes x1 = $15,000

*Total:* $55,000

Por favor confirmar disponibilidad y detalles de pago.
```

### 4.2 Producto directo

```text
Quiero comprar 3 de Pulsera mostacilla a 20,000 COP cada uno. http://localhost:5000/producto/5
```

### 4.3 Observaciones

- Los montos usan coma como separador de miles y **no** incluyen decimales (`:,.0f`).
- La moneda no se indica en el mensaje; se asume COP.
- El formato `*texto*` produce negrita en WhatsApp.
- El enlace del producto usa `window.location.origin`, por lo que en local apunta a `localhost`.
- No se incluye la categoría, descripción ni imágenes.

---

## 5. Flujo de conversación esperado

```text
1. Cliente confirma el pedido en la web.
2. Se registra el pedido (estado pendiente) y se abre WhatsApp.
3. Cliente envía el mensaje (puede editarlo antes de enviar).
4. Vendedor verifica disponibilidad y acuerda pago/entrega.
5. Vendedor confirma manualmente (fuera del sistema).
```

> El sistema no sabe si el mensaje se envió. Un pedido `pendiente` puede corresponder a un carrito abandonado.

---

## 6. Pruebas

### 6.1 Verificar el enlace sin enviar mensaje

1. Inicia sesión y agrega un producto.
2. Abre las herramientas de desarrollo del navegador → pestaña Network.
3. Envía el formulario de checkout.
4. Inspecciona la respuesta `302` y su cabecera `Location`.
5. Debe empezar por `https://api.whatsapp.com/send?phone=<numero>&text=...`.

### 6.2 Verificar el pedido en BD

```bash
python - <<'PY'
import sqlite3
c = sqlite3.connect('database.db')
for row in c.execute('SELECT numero_orden, usuario_nombre, total, estado FROM pedidos ORDER BY id DESC LIMIT 5'):
    print(row)
PY
```

### 6.3 Probar con un número de prueba

Usa un número propio y revisa que el mensaje llegue con saltos de línea, viñetas y total correctos. Evita usar el número de producción en pruebas.

---

## 7. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| WhatsApp abre un chat sin destinatario | `WHATSAPP_PHONE` vacío o mal formado. | Usa solo dígitos con código de país. |
| El mensaje llega cortado | Codificación manual o caracteres no escapados. | Usa `quote()` / `encodeURIComponent` (ya implementado). |
| El enlace abre WhatsApp Web en escritorio | Comportamiento normal de `api.whatsapp.com`. | Usar `wa.me` también redirige según plataforma. |
| El pedido no aparece en admin | El checkout falló antes del `INSERT` o el usuario no estaba autenticado. | Revisa flashes y logs; verifica sesión. |
| El pedido aparece pero el vendedor no recibió nada | El cliente no envió el mensaje. | Confirmar manualmente por otro canal. |
| Cambié el número y no se actualiza | Se leyó al iniciar el proceso. | Reinicia el servidor. |

---

## 8. Evolución a WhatsApp Cloud API

Para automatizar (notificaciones, confirmaciones, historial) se necesitaría:

1. **Cuenta de WhatsApp Business** y app en Meta for Developers.
2. **Token permanente** y `PHONE_NUMBER_ID`.
3. **Plantillas aprobadas** para mensajes fuera de la ventana de 24 h.
4. **Webhook** con verificación `hub.challenge` para recibir mensajes/estados.
5. **Persistencia** de conversaciones y estados.
6. **Cola/retry** para envíos y manejo de errores.
7. **Consentimiento** del usuario (opt-in) y cumplimiento de políticas de Meta.

Variables sugeridas (no implementadas):

```env
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_API_VERSION=v20.0
```

Arquitectura sugerida:

```text
checkout ──► crear pedido ──► encolar notificación ──► Cloud API
                                   ▲
                                   │
webhook ◄── estados (sent/delivered/read) ──► actualizar pedido
```

Costes y requisitos: los define Meta; esta versión no los contempla.

---

## 9. Privacidad

- El mensaje incluye nombre de productos, cantidades y total del pedido.
- El enlace se abre en un dominio de Meta; aplica su política de privacidad.
- No se envían correo, teléfono ni dirección desde la web.
- El pedido almacena `usuario_nombre`; `usuario_celular` está vacío.
- No hay cifrado adicional de la conversación por parte de la tienda.

---

**Anterior:** [05 · Flujos](05-flujos.md) · **Siguiente:** [07 · Seguridad →](07-seguridad.md)
