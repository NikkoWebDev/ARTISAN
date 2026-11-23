"""Almacenamiento de imágenes subidas desde el admin.

- Con `BLOB_READ_WRITE_TOKEN` y el paquete `vercel` instalados: sube a Vercel Blob (store público)
  y devuelve la URL https del blob.
- Si no: guarda en disco (`UPLOAD_FOLDER`) y devuelve `/static/img/productos/<nombre>`.

El import de `vercel.blob` es opcional y perezoso, y `put_blob` se puede inyectar para pruebas.
"""
from __future__ import annotations

import os
from typing import Callable, Optional

from flask import current_app

LOCAL_URL_PREFIX = '/static/img/productos/'
CONTENT_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif'}


def blob_enabled() -> bool:
    return bool(os.environ.get('BLOB_READ_WRITE_TOKEN'))


def _default_put_blob() -> Callable:
    try:
        from vercel.blob.sync import put_blob  # type: ignore
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            'BLOB_READ_WRITE_TOKEN está definido pero falta el paquete "vercel". Instálalo con: pip install vercel'
        ) from exc
    return put_blob


def save_upload(file, filename: str, put_blob: Optional[Callable] = None) -> str:
    """Guarda un archivo (werkzeug FileStorage) y devuelve la URL pública."""
    if blob_enabled():
        put = put_blob or _default_put_blob()
        ext = os.path.splitext(filename)[1].lower()
        data = file.read()
        file.seek(0)
        result = put(
            f'productos/{filename}',
            data,
            access='public',
            content_type=CONTENT_TYPES.get(ext),
            add_random_suffix=True,
        )
        return result.url

    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return f'{LOCAL_URL_PREFIX}{filename}'
