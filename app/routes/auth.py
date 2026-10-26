from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash


from app.db import get_db
from app.csrf import validate_csrf

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not validate_csrf():
            return render_template('login.html')

        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '')

        if not correo or not password:
            flash('Por favor completa todos los campos.', 'error')
            return render_template('login.html')

        db = get_db()
        user = db.execute('SELECT * FROM usuarios WHERE correo = ?', (correo,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session.update({'user_id': user['id'], 'rol': user['rol'], 'nombre': user['nombre']})
            session.permanent = True
            flash('Bienvenido, has iniciado sesión correctamente.', 'success')
            return redirect(url_for('shop.index'))

        flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        if not validate_csrf():
            return render_template('registro.html')

        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('password_confirm', '')

        if not all([nombre, correo, password, confirm]):
            flash('Por favor completa todos los campos.', 'error')
            return render_template('registro.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('registro.html')

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('registro.html')

        if len(nombre) < 3:
            flash('El nombre debe tener al menos 3 caracteres.', 'error')
            return render_template('registro.html')

        db = get_db()
        try:
            hashed_pwd = generate_password_hash(password)
            db.execute('INSERT INTO usuarios (nombre, correo, password, rol) VALUES (?, ?, ?, ?)',
                       (nombre, correo, hashed_pwd, 'cliente'))
            db.commit()
            flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            flash('El correo ya está registrado.', 'error')
    return render_template('registro.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
