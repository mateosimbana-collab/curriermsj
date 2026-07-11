@echo off
title CurrierMsj - Inicio Rapido
cd /d "%~dp0"

echo ============================================
echo  CurrierMsj - Iniciando servicios
echo ============================================

:: Cargar variables de entorno desde .env si existe
if exist ".env" (
    for /f "tokens=1,* delims==" %%a in ('type ".env"') do set "%%a=%%b"
)

echo.
echo [1/3] Verificando ngrok...
curl -s http://127.0.0.1:4040/api/tunnels >nul 2>&1
if %errorlevel% neq 0 (
    echo ngrok no esta corriendo. Iniciando...
    start "ngrok" cmd /c "ngrok http 5000"
    echo Esperando 5 segundos para que ngrok se conecte...
    timeout /t 5 /nobreak >nul
) else (
    echo ngrok ya esta corriendo.
)

echo.
echo [2/3] Iniciando backend Flask (puerto 5000)...
start "CurrierMsj Backend" cmd /k "py run.py"

timeout /t 3 /nobreak >nul

echo.
echo [3/3] Abriendo dashboard...
start http://localhost:5000

echo.
echo Servicios iniciados. Presiona Ctrl+C para cerrar.
echo.
