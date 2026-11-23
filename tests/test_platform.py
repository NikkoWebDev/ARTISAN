import io
import os
import sqlite3
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))


def test_home_en_raiz_y_redirect_301(client):
    assert client.get('/').status_code == 200
    r = client.get('/index')
    assert r.status_code == 301 and r.headers['Location'].endswith('/')


def test_seo_basico(client):
    html = client.get('/').get_data(as_text=True)
    assert 'rel="canonical"' in html and 'og:title' in html and 'application/ld+json' in html
    assert 'Sitemap:' in client.get('/robots.txt').get_data(as_text=True)
    assert '<urlset' in client.get('/sitemap.xml').get_data(as_text=True)
    assert 'noindex' in client.get('/carrito').get_data(as_text=True)


def test_politica_comercial_visible(client):
    html = client.get('/').get_data(as_text=True)
    assert 'máximo 6 días' in html
    for prohibido in ('Comercio Justo', 'Envío Gratis', 'Cambios garantizados'):
        assert prohibido not in html


def test_secret_key_obligatoria_en_vercel(monkeypatch):
    from app.config import Config
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        Config.validate()
    monkeypatch.setenv('SECRET_KEY', 'x' * 64)
    Config.validate()


def test_ensure_schema_se_ejecuta_una_vez(monkeypatch):
    import db_utils
    llamadas = []
    monkeypatch.setattr(db_utils, 'ensure_schema', lambda c: llamadas.append(1))
    monkeypatch.setattr(db_utils, '_SCHEMA_READY', set())
    db_utils.ensure_schema_once(None)
    db_utils.ensure_schema_once(None)
    assert len(llamadas) == 1


class _File(io.BytesIO):
    def save(self, path):
        with open(path, 'wb') as fh:
            fh.write(self.getvalue())


def test_storage_local(app, tmp_path, monkeypatch):
    from app import storage
    monkeypatch.delenv('BLOB_READ_WRITE_TOKEN', raising=False)
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = str(tmp_path)
        url = storage.save_upload(_File(b'img'), 'a.webp')
    assert url == '/static/img/productos/a.webp' and (tmp_path / 'a.webp').read_bytes() == b'img'


def test_storage_blob_con_cliente_falso(app, monkeypatch):
    from app import storage
    monkeypatch.setenv('BLOB_READ_WRITE_TOKEN', 'token-falso')
    visto = {}

    def put_falso(pathname, data, **kw):
        visto.update(pathname=pathname, data=data, **kw)
        return SimpleNamespace(url='https://store.public.blob.vercel-storage.com/productos/a-xyz.webp')

    with app.app_context():
        url = storage.save_upload(_File(b'img'), 'a.webp', put_blob=put_falso)
    assert url.startswith('https://') and visto['access'] == 'public'
    assert visto['content_type'] == 'image/webp' and visto['data'] == b'img'


def test_migracion_idempotente_con_pg_falso(tmp_path):
    import migrate_sqlite_to_pg as m
    src = tmp_path / 's.db'
    con = sqlite3.connect(src)
    con.execute('CREATE TABLE categorias (id INTEGER PRIMARY KEY, nombre TEXT)')
    con.execute("INSERT INTO categorias VALUES (1, 'Bisutería')")
    con.commit(); con.close()

    sentencias = []
    pg = SimpleNamespace(execute=lambda q, p=None: sentencias.append((q, p)), commit=lambda: None)
    assert m.migrate(str(src), pg)['categorias'] == 1
    inserts = [q for q, _ in sentencias if q.startswith('INSERT')]
    assert inserts and all('ON CONFLICT DO NOTHING' in q for q in inserts)
