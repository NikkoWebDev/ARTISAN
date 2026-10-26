import requests
import sqlite3
import time

BASE = 'http://127.0.0.1:5000'

s = requests.Session()

# Register a test user
email = f'tester+{int(time.time())}@example.com'
reg = s.post(f'{BASE}/registro', data={'nombre':'Tester','correo':email,'password':'Test1234','password_confirm':'Test1234'})
print('Registro status:', reg.status_code)

# Login
login = s.post(f'{BASE}/login', data={'correo':email,'password':'Test1234'}, allow_redirects=True)
print('Login final URL:', login.url)

# Add product id=1 to cart
add = s.get(f'{BASE}/carrito/add/1')
print('Add to cart status:', add.status_code)

# View cart
cart = s.get(f'{BASE}/carrito')
print('Cart page status:', cart.status_code)

# Checkout (POST)
checkout = s.post(f'{BASE}/carrito/checkout', allow_redirects=False)
print('Checkout status:', checkout.status_code)
if 'Location' in checkout.headers:
    print('Redirect location:', checkout.headers['Location'])

# Check DB for pedidos
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute('SELECT id, numero_orden, usuario_nombre, total FROM pedidos ORDER BY id DESC LIMIT 1')
row = cur.fetchone()
print('Latest pedido row:', row)
conn.close()
