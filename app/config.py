import os

IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'
# Cookies seguras también en Vercel (siempre HTTPS), aunque FLASK_ENV no esté definido.
SECURE_COOKIES = IS_PRODUCTION or os.environ.get('VERCEL') == '1'

WHATSAPP_PHONE = os.environ.get('WHATSAPP_PHONE', '573123580705').lstrip('+').strip()

# URL pública del sitio (canonical, Open Graph, sitemap). Sin barra final.
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')

# Política comercial: única fuente para los textos visibles (confirmada por el dueño).
POLITICA = {
    'envio_cobertura': 'Envíos a toda Colombia',
    'envio_costo': 'El envío no es gratis: el costo se confirma por WhatsApp según el destino.',
    'envio_plazo': 'Entrega en máximo 6 días.',
    'pagos': 'Aceptamos todos los medios de pago, excepto contra entrega.',
    'cambios': 'No se realizan cambios.',
}


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SECRET', 'artisan_key_2026')
    UPLOAD_FOLDER = 'static/img/productos'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    SEND_FILE_MAX_AGE_DEFAULT = 60 * 60 * 24 * 30  # caché de estáticos: 30 días (se versionan con ?v=)

    if SECURE_COOKIES:
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def validate(cls):
        if IS_PRODUCTION and not os.environ.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY is required in production. Set SECRET_KEY in environment.')
