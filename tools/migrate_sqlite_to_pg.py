#!/usr/bin/env python3
"""Copia database.db (SQLite) a PostgreSQL. Idempotente: se puede ejecutar varias veces.

Uso:
    DATABASE_URL=postgresql://... python tools/migrate_sqlite_to_pg.py [--sqlite database.db]

Antes de copiar crea un respaldo del archivo SQLite en backups/. Conserva los ids, así que
parent_id y usuario_id siguen apuntando a las mismas filas. Las filas que ya existen no se
modifican (ON CONFLICT DO NOTHING). Al final reajusta las secuencias SERIAL.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (tabla, columnas, clave). Orden: respeta las llaves foráneas.
TABLES = [
    ('usuarios', ['id', 'nombre', 'correo', 'password', 'rol'], 'id'),
    ('categorias', ['id', 'nombre'], 'id'),
    ('productos', ['id', 'nombre', 'categoria', 'precio', 'descripcion', 'imagen_url', 'img2', 'img3', 'parent_id'], 'id'),
    ('pedidos', ['id', 'numero_orden', 'usuario_id', 'usuario_nombre', 'usuario_celular', 'items', 'total', 'estado', 'fecha_creacion'], 'id'),
]


def backup_sqlite(path: str) -> str:
    os.makedirs('backups', exist_ok=True)
    dest = os.path.join('backups', f'database-{time.strftime("%Y%m%d-%H%M%S")}.db')
    shutil.copy2(path, dest)
    return dest


def migrate(sqlite_path: str, pg) -> dict:
    """`pg` es un DatabaseConnection de db_utils (con execute/commit) ya conectado a PostgreSQL."""
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    existing_tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {}
    for table, columns, key in TABLES:
        if table not in existing_tables:
            counts[table] = 0
            continue
        available = {r[1] for r in src.execute(f'PRAGMA table_info({table})')}
        cols = [c for c in columns if c in available]
        rows = src.execute(f'SELECT {", ".join(cols)} FROM {table} ORDER BY id').fetchall()
        sql = (
            f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({", ".join("?" for _ in cols)}) '
            'ON CONFLICT DO NOTHING'
        )
        for row in rows:
            pg.execute(sql, [row[c] for c in cols])
        counts[table] = len(rows)
    for table, _, _ in TABLES:
        pg.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), "
            f"(SELECT COUNT(*) > 0 FROM {table}))"
        )
    pg.commit()
    src.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sqlite', default='database.db')
    args = parser.parse_args()

    if not os.environ.get('DATABASE_URL', '').startswith('postgres'):
        print('Define DATABASE_URL con la cadena de conexión de PostgreSQL.', file=sys.stderr)
        return 1
    if not os.path.exists(args.sqlite):
        print(f'No existe {args.sqlite}', file=sys.stderr)
        return 1

    from db_utils import connect_db, ensure_schema

    print('Respaldo:', backup_sqlite(args.sqlite))
    pg = connect_db()
    ensure_schema(pg)
    for table, n in migrate(args.sqlite, pg).items():
        print(f'{table}: {n} filas leídas (las existentes se omiten)')
    pg.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
