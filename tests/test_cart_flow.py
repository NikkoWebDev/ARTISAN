from __future__ import annotations

import json
import os
import sqlite3
import markupsafe
import pytest


ARETES = 'Aretes de Mostacilla Checa Flor Silvestre'


@pytest.fixture
def aid(product_id):
    return product_id(ARETES)


def get_session_csrf(client) -> str:
    """Helper to initialize session and extract csrf_token."""
    res = client.get('/api/cart')
    data = res.get_json()
    return data.get('csrf_token', '')


def test_guest_can_access_api_cart(client):
    """Criterion 1 & 2: Guest can query GET /api/cart without login."""
    res = client.get('/api/cart')
    assert res.status_code == 200
    data = res.get_json()
    assert 'items' in data
    assert 'total' in data
    assert 'count' in data
    assert data['items'] == []
    assert data['total'] == 0.0
    assert data['count'] == 0


def test_csrf_protection_on_api(client, aid):
    """Criterion: Mutating endpoints reject requests without valid CSRF."""
    # Attempt POST without CSRF token
    res = client.post(f'/api/cart/add/{aid}', json={'cantidad': 1})
    assert res.status_code == 403

    res_upd = client.post(f'/api/cart/update/{aid}', json={'cantidad': 2})
    assert res_upd.status_code == 403

    res_rem = client.post(f'/api/cart/remove/{aid}', json={})
    assert res_rem.status_code == 403


def test_api_cart_lifecycle_for_guest(client, aid, product_id):
    """Criterion 2: Add, update, remove in JSON with proper recalculation."""
    csrf_token = get_session_csrf(client)
    headers = {'X-CSRF-Token': csrf_token}

    # 1. Add item 2 (Aretes de Mostacilla: $35,000)
    res = client.post(f'/api/cart/add/{aid}', json={'cantidad': 2}, headers=headers)
    assert res.status_code == 200
    cart = res.get_json()
    assert cart['count'] == 2
    assert cart['total'] == 70000.0
    assert len(cart['items']) == 1
    assert cart['items'][0]['id'] == aid
    assert cart['items'][0]['nombre'] == 'Aretes de Mostacilla Checa Flor Silvestre'
    assert cart['items'][0]['precio'] == 35000.0

    pid = product_id('Pulsera de Mostacilla Multicolor Étnica')
    # 2. Add item 3 (Pulsera de Mostacilla: $28,000)
    res2 = client.post(f'/api/cart/add/{pid}', json={'cantidad': 1}, headers=headers)
    assert res2.status_code == 200
    cart2 = res2.get_json()
    assert cart2['count'] == 3
    assert cart2['total'] == 98000.0
    assert len(cart2['items']) == 2

    # 3. Update quantity of item 2 to 3
    res3 = client.post(f'/api/cart/update/{aid}', json={'cantidad': 3}, headers=headers)
    assert res3.status_code == 200
    cart3 = res3.get_json()
    assert cart3['count'] == 4
    assert cart3['total'] == 133000.0  # (35,000 * 3) + 28,000

    # 4. Remove item 3
    res4 = client.post(f'/api/cart/remove/{pid}', headers=headers)
    assert res4.status_code == 200
    cart4 = res4.get_json()
    assert cart4['count'] == 3
    assert cart4['total'] == 105000.0
    assert len(cart4['items']) == 1
    assert cart4['items'][0]['id'] == aid


def test_price_anti_tampering(client, aid):
    """Anti-manipulation: cart total must be verified against database."""
    csrf_token = get_session_csrf(client)
    headers = {'X-CSRF-Token': csrf_token}

    # Add item normally
    client.post(f'/api/cart/add/{aid}', json={'cantidad': 1}, headers=headers)

    # Malicious tampering in session cookie
    with client.session_transaction() as sess:
        sess['cart'] = [{'id': aid, 'nombre': 'Aretes', 'precio': 1.0, 'cantidad': 1}]

    # Query GET /api/cart: should reconcile against DB price ($35,000)
    res = client.get('/api/cart')
    data = res.get_json()
    assert data['items'][0]['precio'] == 35000.0
    assert data['total'] == 35000.0


def test_html_cart_guest_views_and_add(client, aid):
    """Criterion 1: Unauthenticated user can view /carrito and add items via POST without login."""
    # 1. View /carrito
    res = client.get('/carrito')
    assert res.status_code == 200
    assert b'Bolsa de Compras' in res.data
    assert b'bolsa de compras' in res.data.lower()

    csrf_token = get_session_csrf(client)

    # 2. GET /carrito/add/<id> must be rejected (405 Method Not Allowed) to prevent CSRF by GET
    res_get = client.get(f'/carrito/add/{aid}')
    assert res_get.status_code == 405

    # 3. Add via POST with valid CSRF
    res_add = client.post(
        f'/carrito/add/{aid}',
        data={'cantidad': '1', 'csrf_token': csrf_token},
        follow_redirects=True,
    )
    assert res_add.status_code == 200
    assert b'Aretes de Mostacilla' in res_add.data

    # Verify item is in cart page now
    res_cart = client.get('/carrito')
    assert res_cart.status_code == 200
    assert b'35,000' in res_cart.data


def test_guest_can_add_subproduct_variant(client, aid):
    """BUG-01: Verify subproducts (parent_id IS NOT NULL) can be added and purchased."""
    conn = sqlite3.connect(os.environ.get('SQLITE_PATH', 'database.db'))
    conn.row_factory = sqlite3.Row
    sub = conn.execute('SELECT * FROM productos WHERE parent_id IS NOT NULL LIMIT 1').fetchone()
    if not sub:
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO productos (nombre, categoria, precio, descripcion, parent_id)
               VALUES ('Variante Test', 'Bisutería', 25000, 'Variante de prueba', ?)''', (aid,)
        )
        conn.commit()
        sub = conn.execute('SELECT * FROM productos WHERE id = ?', (cur.lastrowid,)).fetchone()
    sub_id = sub['id']
    sub_name = sub['nombre']
    sub_price = float(sub['precio'])
    conn.close()

    csrf_token = get_session_csrf(client)
    headers = {'X-CSRF-Token': csrf_token}

    # Add subproduct via API
    res = client.post(f'/api/cart/add/{sub_id}', json={'cantidad': 2}, headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data['count'] == 2
    assert data['total'] == sub_price * 2
    assert any(it['id'] == sub_id for it in data['items'])

    # View cart page
    res_cart = client.get('/carrito')
    assert res_cart.status_code == 200
    escaped_sub_name = markupsafe.escape(sub_name).encode('utf-8')
    assert escaped_sub_name in res_cart.data


def test_guest_checkout_whatsapp(client, aid):
    """Criterion 1 & checkout: Guest checkout generates order without login redirect."""
    csrf_token = get_session_csrf(client)
    headers = {'X-CSRF-Token': csrf_token}

    # Add item
    client.post(f'/api/cart/add/{aid}', json={'cantidad': 2}, headers=headers)

    # Checkout as guest with name and phone
    checkout_payload = {
        'nombre': 'Carlos Artesano',
        'celular': '3001234567',
    }
    res = client.post(
        '/api/cart/checkout',
        json=checkout_payload,
        headers=headers,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'ORD-' in data['order_num']
    assert data['total'] == 70000.0
    assert 'api.whatsapp.com/send' in data['whatsapp_url']
    assert 'Carlos+Artesano' in data['whatsapp_url'] or 'Carlos%20Artesano' in data['whatsapp_url']

    # Verify cart is now empty
    cart_res = client.get('/api/cart')
    assert cart_res.get_json()['count'] == 0

    # Verify order was saved in database with usuario_id = None
    conn = sqlite3.connect(os.environ.get('SQLITE_PATH', 'database.db'))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        'SELECT * FROM pedidos WHERE numero_orden = ?',
        (data['order_num'],)
    ).fetchone()
    assert row is not None
    assert row['usuario_id'] is None
    assert row['usuario_nombre'] == 'Carlos Artesano'
    assert row['usuario_celular'] == '3001234567'
    assert row['total'] == 70000.0
    conn.close()
