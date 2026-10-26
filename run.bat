@echo off
REM Script para ejecutar Artisan en Windows

cd /d "%~dp0"

echo.
echo ========================================
echo    ARTISAN WEB - Iniciando servidor
echo ========================================
echo.

REM Verificar si venv existe
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar venv
call venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando dependencias...
pip install -q -r requirements.txt

REM Inicializar BD si no existe
if not exist database.db (
    echo Inicializando base de datos...
    python database_setup.py
)

REM Mostrar credenciales
echo.
echo ========================================
echo    CREDENCIALES DE ADMIN
echo ========================================
echo Email:    admin@artisan.com
echo Password: admin123
echo.
echo ⚠️  CAMBIAR CONTRASEÑA DESPUÉS DEL PRIMER ACCESO
echo.
echo ========================================
echo.

REM Ejecutar aplicación
echo Iniciando servidor en http://localhost:5000
echo Presiona Ctrl+C para detener
echo.

python app.py
