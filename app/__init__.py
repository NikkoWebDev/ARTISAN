import os
import secrets
import time
from flask import Flask, session
import markupsafe
from app.config import Config
from app.extensions import limiter
from app.db import close_db

WHATSAPP_PHONE = os.environ.get('WHATSAPP_PHONE', '573123580705').lstrip('+').strip()

_proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(_proj_root, 'templates'),
        static_folder=os.path.join(_proj_root, 'static'),
    )
    app.config.from_object(Config)
    Config.validate()

    app.config['UPLOAD_FOLDER'] = os.path.join(_proj_root, app.config['UPLOAD_FOLDER'])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    limiter.init_app(app)

    app.jinja_env.filters['nl2br'] = (
        lambda v: markupsafe.Markup('<br>'.join(markupsafe.escape(line) for line in v.splitlines()))
        if v else ''
    )

    @app.before_request
    def ensure_csrf():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)

    @app.context_processor
    def inject_globals():
        def _cache_buster():
            css_path = os.path.join(app.static_folder, 'css', 'style.css')
            try:
                return str(int(os.path.getmtime(css_path)))
            except OSError:
                return str(int(time.time()))

        return {
            'WHATSAPP_PHONE': WHATSAPP_PHONE,
            'csrf_token': lambda: session.get('csrf_token', ''),
            'cache_buster': _cache_buster,
        }

    app.teardown_appcontext(close_db)

    from app.routes.auth import auth_bp
    from app.routes.shop import shop_bp
    from app.routes.cart import cart_bp
    from app.routes.admin import admin_bp

    limiter.exempt(shop_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)

    return app
