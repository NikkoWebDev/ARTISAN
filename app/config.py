import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SECRET', 'artisan_key_2026')
    UPLOAD_FOLDER = 'static/img/productos'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    if os.environ.get('FLASK_ENV') == 'production':
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def validate(cls):
        if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY is required in production. Set SECRET_KEY in environment.')
