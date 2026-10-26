FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p static/img/productos logs

# Exponer puerto
EXPOSE 5000

# Ejecutar inicialización de DB y Gunicorn en tiempo de ejecución
CMD ["sh", "-lc", "python database_setup.py && gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 wsgi:app"]
