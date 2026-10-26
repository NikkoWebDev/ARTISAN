from __future__ import annotations

import json
import secrets
import time
from functools import wraps
from typing import Any, Dict, List
from urllib.parse import quote

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import WHATSAPP_PHONE
from app.csrf import validate_csrf
from app.db import get_db
from app.extensions import limiter

cart_bp = Blueprint('cart', __name__)

MAX_QTY = 1000


def cart_required(f):
    """Legacy decorator kept for backwards compatibility."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def get_cart_payload() -> Dict[str, Any]:
    """Recalculates cart items against the database to prevent price tampering.

    Purges nonexistent products, clamps quantities, and synchronizes the session.
    Allows both parent products and subproduct variants.
    """
    cart: List[Dict[str, Any]] = session.get('cart', [])
    csrf_token = session.get('csrf_token', '')
    if not cart:
        return {'items': [], 'total': 0.0, 'count': 0, 'csrf_token': csrf_token}

    db = get_db()
    validated_items: List[Dict[str, Any]] = []
    total = 0.0
    count = 0
    sanitized_cart: List[Dict[str, Any]] = []

    for item in cart:
        item_id = item.get('id')
        if not item_id:
            continue

        p = db.execute(
            'SELECT id, nombre, precio, imagen_url FROM productos WHERE id = ?',
            (item_id,),
        ).fetchone()

        if not p:
            continue

        try:
            qty = int(item.get('cantidad', 1))
            qty = max(1, min(qty, MAX_QTY))
        except (ValueError, TypeError):
            qty = 1

        price = float(p['precio'])
        subtotal = round(price * qty, 2)
        total += subtotal
        count += qty

        item_data = {
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': price,
            'cantidad': qty,
            'imagen_url': p['imagen_url'] or '',
            'subtotal': subtotal,
        }
        validated_items.append(item_data)
        sanitized_cart.append({
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': price,
            'cantidad': qty,
            'imagen_url': p['imagen_url'] or '',
        })

    session['cart'] = sanitized_cart
    session.modified = True

    return {
        'items': validated_items,
        'total': round(total, 2),
        'count': count,
        'csrf_token': csrf_token,
    }


# ==========================================
# Traditional HTML Routes (Guest Friendly)
# ==========================================

@cart_bp.route('/carrito')
@limiter.exempt
def view_cart():
    payload = get_cart_payload()
    return render_template('carrito.html', items=payload['items'], total=payload['total'])


@cart_bp.route('/carrito/add/<int:id>', methods=['POST'])
def add_to_cart(id: int):
    if not validate_csrf():
        return redirect(request.referrer or url_for('shop.lineaproductos'))

    try:
        raw_qty = request.form.get('cantidad', 1)
        qty = int(raw_qty)
        qty = max(1, min(qty, MAX_QTY))
    except (ValueError, TypeError):
        qty = 1

    db = get_db()
    p = db.execute(
        'SELECT id, nombre, precio, imagen_url FROM productos WHERE id = ?',
        (id,),
    ).fetchone()

    if not p:
        flash('Producto no encontrado.', 'error')
        return redirect(request.referrer or url_for('shop.lineaproductos'))

    cart = session.get('cart', [])
    for item in cart:
        if item.get('id') == p['id']:
            item['cantidad'] = min(int(item.get('cantidad', 1)) + qty, MAX_QTY)
            break
    else:
        cart.append({
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': float(p['precio']),
            'cantidad': qty,
            'imagen_url': p['imagen_url'] or '',
        })

    session['cart'] = cart
    session.modified = True
    flash(f"{p['nombre']} agregado al carrito (x{qty})", 'success')
    return redirect(request.referrer or url_for('shop.lineaproductos'))


@cart_bp.route('/carrito/remove/<int:id>', methods=['POST'])
def remove_from_cart(id: int):
    if not validate_csrf():
        return redirect(url_for('cart.view_cart'))
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item.get('id') != id]
    session.modified = True
    flash('Artículo eliminado del carrito.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/carrito/update/<int:id>', methods=['POST'])
def update_cart(id: int):
    if not validate_csrf():
        return redirect(url_for('cart.view_cart'))

    try:
        qty = int(request.form.get('cantidad', 1))
    except (ValueError, TypeError):
        qty = 1

    cart = session.get('cart', [])
    if qty <= 0:
        session['cart'] = [item for item in cart if item.get('id') != id]
        flash('Artículo eliminado del carrito.', 'info')
    else:
        qty = min(qty, MAX_QTY)
        for item in cart:
            if item.get('id') == id:
                item['cantidad'] = qty
                flash(f"Cantidad de {item.get('nombre', 'producto')} ajustada a {qty}", 'info')
                break
        session['cart'] = cart

    session.modified = True
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/carrito/clear', methods=['POST'])
def clear_cart():
    if not validate_csrf():
        return redirect(url_for('cart.view_cart'))
    session.pop('cart', None)
    session.modified = True
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/carrito/checkout', methods=['POST'])
@cart_bp.route('/api/cart/checkout', methods=['POST'])
def checkout_whatsapp():
    is_api = request.is_json or request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json'

    if not validate_csrf():
        if is_api:
            return jsonify({'error': 'Token CSRF inválido o ausente'}), 403
        return redirect(url_for('cart.view_cart'))

    payload = get_cart_payload()
    validated_items = payload['items']
    total = payload['total']

    if not validated_items or total <= 0:
        if is_api:
            return jsonify({'error': 'El carrito está vacío'}), 400
        flash('Tu carrito está vacío.', 'error')
        return redirect(url_for('cart.view_cart'))

    db = get_db()
    try:
        user_id = session.get('user_id')
        usuario_nombre = None
        usuario_celular = None

        if request.is_json and request.get_json(silent=True):
            body = request.get_json(silent=True)
            usuario_nombre = body.get('nombre')
            usuario_celular = body.get('celular')
        else:
            usuario_nombre = request.form.get('nombre')
            usuario_celular = request.form.get('celular')

        if user_id:
            user = db.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
            if user:
                if not usuario_nombre:
                    usuario_nombre = user['nombre']
                if not usuario_celular and 'celular' in user.keys():
                    usuario_celular = user['celular']
            else:
                user_id = None

        if not usuario_nombre:
            usuario_nombre = 'Invitado'

        order_num = f"ORD-{int(time.time())}-{secrets.token_hex(2).upper()}"

        db.execute(
            '''INSERT INTO pedidos (numero_orden, usuario_id, usuario_nombre, usuario_celular, items, total, estado)
               VALUES (?, ?, ?, ?, ?, ?, 'pendiente')''',
            (order_num, user_id, usuario_nombre, usuario_celular, json.dumps(validated_items), total),
        )
        db.commit()

        msg_items = "\n".join(
            f"• {it['nombre']} x{it['cantidad']} = ${it['precio'] * it['cantidad']:,.0f}"
            for it in validated_items
        )
        client_lines = f"\n*Cliente:* {usuario_nombre}"
        if usuario_celular:
            client_lines += f"\n*Teléfono:* {usuario_celular}"

        msg = f"""Hola, me gustaría completar mi compra:

*Número de Orden:* {order_num}{client_lines}

*Items:*
{msg_items}

*Total:* ${total:,.0f}

Por favor confirmar disponibilidad y detalles de pago."""

        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_PHONE}&text={quote(msg)}"
        session.pop('cart', None)
        session.modified = True

        if is_api:
            return jsonify({
                'success': True,
                'whatsapp_url': whatsapp_url,
                'order_num': order_num,
                'total': total,
                'items': validated_items,
            })

        return redirect(whatsapp_url)

    except Exception as exc:
        if is_api:
            return jsonify({'error': 'Error al procesar la compra', 'detail': str(exc)}), 500
        flash('Error al procesar la compra.', 'error')
        return redirect(url_for('cart.view_cart'))


# ==========================================
# JSON API Routes (Drawer Cart & Async)
# ==========================================

@cart_bp.route('/api/cart', methods=['GET'])
@limiter.exempt
def api_get_cart():
    payload = get_cart_payload()
    return jsonify(payload)


@cart_bp.route('/api/cart/add/<int:id>', methods=['POST'])
def api_add_to_cart(id: int):
    if not validate_csrf():
        return jsonify({'error': 'Token CSRF inválido o ausente'}), 403

    if request.is_json and request.get_json(silent=True):
        raw_qty = request.get_json(silent=True).get('cantidad', 1)
    else:
        raw_qty = request.form.get('cantidad', 1)

    try:
        qty = int(raw_qty)
        qty = max(1, min(qty, MAX_QTY))
    except (ValueError, TypeError):
        qty = 1

    db = get_db()
    p = db.execute(
        'SELECT id, nombre, precio, imagen_url FROM productos WHERE id = ?',
        (id,),
    ).fetchone()

    if not p:
        return jsonify({'error': 'Producto no encontrado'}), 404

    cart = session.get('cart', [])
    for item in cart:
        if item.get('id') == p['id']:
            item['cantidad'] = min(int(item.get('cantidad', 1)) + qty, MAX_QTY)
            break
    else:
        cart.append({
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': float(p['precio']),
            'cantidad': qty,
            'imagen_url': p['imagen_url'] or '',
        })

    session['cart'] = cart
    session.modified = True

    payload = get_cart_payload()
    return jsonify(payload)


@cart_bp.route('/api/cart/update/<int:id>', methods=['POST'])
def api_update_cart(id: int):
    if not validate_csrf():
        return jsonify({'error': 'Token CSRF inválido o ausente'}), 403

    if request.is_json and request.get_json(silent=True):
        raw_qty = request.get_json(silent=True).get('cantidad', 1)
    else:
        raw_qty = request.form.get('cantidad', 1)

    try:
        qty = int(raw_qty)
    except (ValueError, TypeError):
        qty = 1

    cart = session.get('cart', [])
    if qty <= 0:
        session['cart'] = [item for item in cart if item.get('id') != id]
    else:
        qty = min(qty, MAX_QTY)
        for item in cart:
            if item.get('id') == id:
                item['cantidad'] = qty
                break
        session['cart'] = cart

    session.modified = True
    payload = get_cart_payload()
    return jsonify(payload)


@cart_bp.route('/api/cart/remove/<int:id>', methods=['POST'])
def api_remove_from_cart(id: int):
    if not validate_csrf():
        return jsonify({'error': 'Token CSRF inválido o ausente'}), 403

    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item.get('id') != id]
    session.modified = True
    payload = get_cart_payload()
    return jsonify(payload)


@cart_bp.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    if not validate_csrf():
        return jsonify({'error': 'Token CSRF inválido o ausente'}), 403

    session.pop('cart', None)
    session.modified = True
    return jsonify({'items': [], 'total': 0.0, 'count': 0, 'csrf_token': session.get('csrf_token', '')})
