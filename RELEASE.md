# RELEASE Checklist

Este documento describe los pasos finales para publicar la tienda Artisan como la versión oficial.

## 1) Preparación de entorno
- Crear un `.env` en producción con variables seguras:
  - `SECRET_KEY` — cadena larga aleatoria (obligatoria si `FLASK_ENV=production`)
  - `WHATSAPP_PHONE`
  - `INITIAL_ADMIN_EMAIL` y `INITIAL_ADMIN_PASSWORD` (solo para `database_setup.py`)
  - Otros: `DB_*`, `MAIL_*` según necesidad
- Exportar esas variables en el proceso o arrancar con `dotenv run -- ...`: esta versión **no carga** `.env` automáticamente.

## 2) Inicializar base de datos y crear admin
```bash
# en local o en el servidor antes de iniciar el servicio
# exporta las variables (o usa dotenv run) antes de ejecutar
python database_setup.py
```

`database_setup.py` crea el esquema, las categorías base y, si existen `INITIAL_ADMIN_EMAIL` y `INITIAL_ADMIN_PASSWORD`, un usuario administrador. No existe `seed_data.py` en este repositorio.

## 3) Ejecutar comprobaciones básicas
```bash
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m compileall app db_utils.py database_setup.py app.py wsgi.py
```

`e2e_test.py` está desactualizado (usa GET en rutas POST y no envía CSRF) y fallará; no lo uses como puerta de release hasta reescribirlo. No existen `compile_all.py` ni `seed_data.py`.

## 4) Despliegue con Docker (producción)
- Usar `Dockerfile.prod` y `docker-compose.prod.yml`.
- Asegurarse de que el entorno contiene `SECRET_KEY` y valores productivos.
- Revisar antes las inconsistencias documentadas en [docs/08-despliegue.md](docs/08-despliegue.md#9-problemas-conocidos-de-docker) (servicio `db`, variables `DB_*`/`POSTGRES_*` y placeholders).

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## 5) Recomendaciones para producción
- Usar PostgreSQL en lugar de SQLite.
- Arrancar con Gunicorn (`gunicorn wsgi:app`), nunca con `python app.py` (modo debug).
- Poner Nginx como reverse-proxy y manejar SSL (Let's Encrypt).
- No almacenar credenciales en el repositorio.
- Configurar backups automáticos de la DB.
- Implementar monitoreo y alertas.

## 6) Post-release
- Cambiar la contraseña del admin creado.
- Eliminar `INITIAL_ADMIN_*` del entorno después de la inicialización.
- Revisar logs y confirmar que los pedidos están llegando.
- Seguir la guía de [operación y mantenimiento](docs/09-operacion-mantenimiento.md).

---

Documentación completa: [docs/README.md](docs/README.md). Para ayuda con el despliegue final (configurar Nginx, PostgreSQL, pipeline CI/CD o publicar a un proveedor), indica dónde quieres desplegar (DigitalOcean, Railway, Render, Azure, Heroku, VPS).