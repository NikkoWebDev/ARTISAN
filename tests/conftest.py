"""Pruebas aisladas: cada sesión usa una base SQLite temporal y nunca toca database.db."""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_tmp = tempfile.mkdtemp(prefix='artisan_tests_')
os.environ['SQLITE_PATH'] = os.path.join(_tmp, 'test.db')
os.environ.pop('DATABASE_URL', None)
os.environ.pop('BLOB_READ_WRITE_TOKEN', None)


@pytest.fixture(scope='session')
def app():
    from app import create_app
    from seed_catalog import seed_database

    seed_database()
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def product_id(app):
    """Devuelve el id de un producto por nombre (los ids dependen de la base)."""
    from db_utils import connect_db

    def _find(nombre: str) -> int:
        db = connect_db()
        try:
            row = db.execute('SELECT id FROM productos WHERE nombre = ? AND parent_id IS NULL', (nombre,)).fetchone()
        finally:
            db.close()
        assert row is not None, f'No existe el producto {nombre!r}'
        return row['id']

    return _find
