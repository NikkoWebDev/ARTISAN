from flask import g
from db_utils import connect_db, ensure_schema


def get_db():
    if 'db' not in g:
        g.db = connect_db()
        ensure_schema(g.db)
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
