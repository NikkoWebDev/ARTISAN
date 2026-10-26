from __future__ import annotations

from flask import current_app, flash, redirect, request, session, url_for


def validate_csrf() -> bool:
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return True

    if current_app.config.get('TESTING') and not current_app.config.get('WTF_CSRF_ENABLED', True):
        return True

    token = (
        request.headers.get('X-CSRF-Token')
        or request.headers.get('X-CSRFToken')
        or request.form.get('csrf_token')
    )
    if not token and request.is_json:
        data = request.get_json(silent=True)
        if isinstance(data, dict):
            token = data.get('csrf_token')

    expected = session.get('csrf_token')
    if not token or not expected or token != expected:
        if not (request.path.startswith('/api/') or request.is_json):
            flash('Error de seguridad: formulario inválido. Intenta de nuevo.', 'error')
        return False
    return True


def csrf_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not validate_csrf():
            if request.is_json or request.path.startswith('/api/'):
                from flask import jsonify
                return jsonify({'error': 'Token CSRF inválido o ausente'}), 403
            return redirect(request.referrer or url_for('shop.index'))
        return f(*args, **kwargs)
    return wrapper
