import json
import os
from functools import wraps

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.utils import secure_filename

from flask import current_app
from app.db import get_db
from app.csrf import validate_csrf

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_MIME_MAGIC = {
    b'\xff\xd8': ('.jpg', '.jpeg'),
    b'\x89PNG': ('.png',),
    b'RIFF': ('.webp',),
    b'GIF8': ('.gif',),
}


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash('Debes iniciar sesión como administrador.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper


def validate_image(file):
    if not file or not file.filename:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None

    magic = file.read(4)
    file.seek(0)

    for sig, exts in ALLOWED_MIME_MAGIC.items():
        if magic.startswith(sig) and ext in exts:
            return ext
    return None


def save_image(file, nombre, index):
    ext = validate_image(file)
    if not ext:
        return None

    fname = secure_filename(f"{nombre}_{index}{ext}")
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
    return f"/static/img/productos/{fname}"


@admin_bp.route('/')
@admin_required
def panel():
    db = get_db()

    prods = db.execute(
        '''SELECT p.*, parent.nombre AS parent_name
           FROM productos p
           LEFT JOIN productos parent ON p.parent_id = parent.id
           ORDER BY p.parent_id IS NOT NULL, p.id DESC'''
    ).fetchall()

    cats = db.execute('SELECT * FROM categorias').fetchall()
    pedidos_rows = db.execute('SELECT * FROM pedidos ORDER BY fecha_creacion DESC').fetchall()

    pedidos = []
    for row in pedidos_rows:
        pedido = dict(row)
        try:
            pedido['items'] = json.loads(pedido['items']) if pedido['items'] else []
        except (json.JSONDecodeError, TypeError):
            pedido['items'] = []
        pedido['item_count'] = len(pedido['items'])
        pedidos.append(pedido)

    parent_prefill = request.args.get('parent_id')
    return render_template('admin.html', productos=prods, categorias=cats,
                           parent_prefill=parent_prefill, pedidos=pedidos)


@admin_bp.route('/add_prod', methods=['POST'])
@admin_required
def add_product():
    if not validate_csrf():
        return redirect(url_for('admin.panel'))

    nombre = request.form.get('nombre', '').strip()
    categoria = request.form.get('categoria', '').strip()
    precio_str = request.form.get('precio', '').strip()
    descripcion = request.form.get('descripcion', '').strip()

    if not all([nombre, categoria, precio_str, descripcion]):
        missing = [k for k, v in [('nombre', nombre), ('categoría', categoria),
                                   ('precio', precio_str), ('descripción', descripcion)] if not v]
        flash(f'Completa los campos obligatorios: {", ".join(missing)}.', 'error')
        return redirect(url_for('admin.panel'))

    try:
        precio = float(precio_str)
        if precio <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('El precio debe ser un número positivo.', 'error')
        return redirect(url_for('admin.panel'))

    imgs = []
    for i in range(1, 4):
        f = request.files.get(f'img{i}')
        url = save_image(f, nombre, i) if f and f.filename else None
        imgs.append(url)

    parent = request.form.get('parent_id') or None
    db = get_db()
    try:
        db.execute(
            '''INSERT INTO productos (nombre, categoria, precio, descripcion, imagen_url, img2, img3, parent_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (nombre, categoria, precio, descripcion, imgs[0], imgs[1], imgs[2], parent)
        )
        db.commit()
        flash('Producto publicado exitosamente.', 'success')
    except Exception:
        flash('Error al guardar el producto.', 'error')

    return redirect(url_for('admin.panel'))


@admin_bp.route('/cat/add', methods=['POST'])
@admin_required
def add_category():
    if not validate_csrf():
        return redirect(url_for('admin.panel'))

    nueva = request.form.get('nueva_categoria', '').strip()
    if not nueva:
        flash('El nombre de la categoría no puede estar vacío.', 'error')
    else:
        db = get_db()
        try:
            db.execute('INSERT OR IGNORE INTO categorias (nombre) VALUES (?)', (nueva,))
            db.commit()
            flash('Categoría creada exitosamente.', 'success')
        except Exception:
            flash('Error al crear la categoría.', 'error')
    return redirect(url_for('admin.panel'))


@admin_bp.route('/cat/del/<int:id>', methods=['POST'])
@admin_required
def delete_category(id):
    if not validate_csrf():
        return redirect(url_for('admin.panel'))

    db = get_db()
    try:
        db.execute('DELETE FROM categorias WHERE id = ?', (id,))
        db.commit()
        flash('Categoría eliminada.', 'success')
    except Exception:
        flash('Error al eliminar la categoría.', 'error')
    return redirect(url_for('admin.panel'))


@admin_bp.route('/prod/del/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    if not validate_csrf():
        return redirect(url_for('admin.panel'))

    db = get_db()
    try:
        db.execute('DELETE FROM productos WHERE id = ?', (id,))
        db.commit()
        flash('Producto eliminado.', 'success')
    except Exception:
        flash('Error al eliminar el producto.', 'error')
    return redirect(url_for('admin.panel'))


@admin_bp.route('/prod/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    db = get_db()

    if request.method == 'POST':
        if not validate_csrf():
            return redirect(url_for('admin.panel'))

        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        precio_str = request.form.get('precio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not all([nombre, categoria, precio_str, descripcion]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return redirect(url_for('admin.panel'))

        try:
            precio = float(precio_str)
            if precio <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash('El precio debe ser un número positivo.', 'error')
            return redirect(url_for('admin.panel'))

        imgs = []
        for i in range(1, 4):
            f = request.files.get(f'img{i}')
            if f and f.filename:
                url = save_image(f, nombre, i)
                imgs.append(url or request.form.get(f'old_img{i}'))
            else:
                imgs.append(request.form.get(f'old_img{i}'))

        parent = request.form.get('parent_id') or None

        try:
            db.execute(
                '''UPDATE productos SET nombre=?, categoria=?, precio=?, descripcion=?,
                   imagen_url=?, img2=?, img3=?, parent_id=? WHERE id=?''',
                (nombre, categoria, precio, descripcion, imgs[0], imgs[1], imgs[2], parent, id)
            )
            db.commit()
            flash('Producto actualizado exitosamente.', 'success')
        except Exception:
            flash('Error al actualizar el producto.', 'error')
        return redirect(url_for('admin.panel'))

    prod = db.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    cats = db.execute('SELECT * FROM categorias').fetchall()
    prods = db.execute('SELECT id, nombre, parent_id FROM productos').fetchall()

    if not prod:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('admin.panel'))

    return render_template('edit_product.html', p=prod, categorias=cats, productos=prods)
