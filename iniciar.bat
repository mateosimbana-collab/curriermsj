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
echo [1/3] Preparando entorno Python...
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
)
".venv\Scripts\python.exe" -c "import flask, httpx, jwt, requests, supabase" >nul 2>&1
if %errorlevel% neq 0 (
    ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
    if %errorlevel% neq 0 exit /b 1
)

if /I "%START_NGROK%"=="1" (
    curl -s http://127.0.0.1:4040/api/tunnels >nul 2>&1
    if %errorlevel% neq 0 start "ngrok" cmd /c "ngrok http 5000"
) else (
    echo ngrok omitido. Define START_NGROK=1 para habilitarlo.
)

echo.
echo [2/3] Iniciando backend Flask (puerto 5000)...
start "CurrierMsj Backend" cmd /k "".venv\Scripts\python.exe" run.py"

timeout /t 3 /nobreak >nul

echo.
echo [3/3] Abriendo dashboard...
start http://localhost:5000

echo.
echo Servicios iniciados. Presiona Ctrl+C para cerrar.
echo.
