import os
import sqlite3
from urllib.parse import urlparse

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

DATABASE_URL = os.environ.get('DATABASE_URL')


def using_postgres():
    return bool(DATABASE_URL and DATABASE_URL.startswith('postgres'))


class DatabaseConnection:
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.postgres = is_postgres

    def execute(self, query, params=None):
        if self.postgres:
            query = query.replace('?', '%s')
            if 'INSERT OR IGNORE' in query:
                query = query.replace('INSERT OR IGNORE', 'INSERT')
            if 'DELETE' in query and 'WHERE' in query:
                pass
        if params is None:
            params = []
        elif not isinstance(params, (list, tuple)):
            params = [params]
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def connect_db():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2-binary is required for PostgreSQL support')
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return DatabaseConnection(conn, is_postgres=True)

    sqlite_path = os.environ.get('SQLITE_PATH', 'database.db')
    sqlite_dir = os.path.dirname(sqlite_path)
    if sqlite_dir:
        os.makedirs(sqlite_dir, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 3000')
    return DatabaseConnection(conn)
def table_columns(connection, table_name):
    if using_postgres():
        cursor = connection.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
            (table_name,)
        )
        return [row['column_name'] for row in cursor.fetchall()]

    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]



def ensure_schema(connection):
    if using_postgres():
        connection.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                correo TEXT UNIQUE,
                password TEXT,
                rol TEXT
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                categoria TEXT,
                precio REAL,
                descripcion TEXT,
                imagen_url TEXT,
                img2 TEXT,
                img3 TEXT,
                parent_id INTEGER
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY,
                numero_orden TEXT UNIQUE,
                usuario_id INTEGER,
                usuario_nombre TEXT,
                usuario_celular TEXT,
                items TEXT,
                total REAL,
                estado TEXT DEFAULT 'pendiente',
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        ''')
    else:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                correo TEXT UNIQUE,
                password TEXT,
                rol TEXT
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE
            )
        ''')
        connection.execute('''
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
            )
        ''')
        connection.execute('''
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
            )
        ''')

    existing_products = table_columns(connection, 'productos')
    if 'img2' not in existing_products:
        connection.execute('ALTER TABLE productos ADD COLUMN img2 TEXT')
    if 'img3' not in existing_products:
        connection.execute('ALTER TABLE productos ADD COLUMN img3 TEXT')
    if 'parent_id' not in existing_products:
        connection.execute('ALTER TABLE productos ADD COLUMN parent_id INTEGER')

    existing_orders = table_columns(connection, 'pedidos')
    if 'usuario_nombre' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN usuario_nombre TEXT')
    if 'usuario_celular' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN usuario_celular TEXT')
    if 'items' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN items TEXT')
    if 'total' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN total REAL')
    if 'estado' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN estado TEXT DEFAULT "pendiente"')
    if 'fecha_creacion' not in existing_orders:
        connection.execute('ALTER TABLE pedidos ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP')

    connection.commit()
