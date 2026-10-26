import os
from werkzeug.security import generate_password_hash
from db_utils import connect_db, ensure_schema


def setup():
    db = connect_db()
    ensure_schema(db)

    admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
    admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')

    if admin_email and admin_password:
        try:
            pwd = generate_password_hash(admin_password)
            db.execute(
                'INSERT OR IGNORE INTO usuarios (nombre, correo, password, rol) VALUES (?, ?, ?, ?)',
                ('Admin', admin_email, pwd, 'admin')
            )
        except Exception:
            pass

    try:
        db.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Bisutería')")
        db.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Marroquinería')")
    except Exception:
        pass

    db.commit()
    db.close()
    print('Base de datos lista.')


if __name__ == '__main__':
    setup()
