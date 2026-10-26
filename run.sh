#!/bin/bash
# Script para ejecutar Artisan en Linux/Mac

set -e

echo ""
echo "========================================"
echo "   ARTISAN WEB - Iniciando servidor"
echo "========================================"
echo ""

# Ir al directorio del script
cd "$(dirname "$0")"

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar venv
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install -q -r requirements.txt

# Inicializar BD si no existe
if [ ! -f "database.db" ]; then
    echo "Inicializando base de datos..."
    python3 database_setup.py
fi

# Mostrar credenciales
echo ""
echo "========================================"
echo "   CREDENCIALES DE ADMIN"
echo "========================================"
echo "Email:    admin@artisan.com"
echo "Password: admin123"
echo ""
echo "⚠️  CAMBIAR CONTRASEÑA DESPUÉS DEL PRIMER ACCESO"
echo ""
echo "========================================"
echo ""

# Ejecutar aplicación
echo "Iniciando servidor en http://localhost:5000"
echo "Presiona Ctrl+C para detener"
echo ""

python3 app.py
