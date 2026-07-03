@echo off
title CurrierMsj - Inicio Rapido
cd /d "%~dp0"

echo ============================================
echo  CurrierMsj - Iniciando servicios
echo ============================================

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
start "CurrierMsj Bot" cmd /k "cd /d bot-mensajeria && python app.py"

timeout /t 3 /nobreak >nul

echo.
echo [3/3] Abriendo dashboard del Dueno...
start http://localhost:5000/dashboard

echo.
echo ============================================
echo  Servicios iniciados - Accesos directos:
echo ============================================
echo.
echo  Dashboard Dueno:   http://localhost:5000/dashboard
echo  Dashboard Soporte: http://localhost:5000/dashboard/soporte
echo  Health Check:      http://localhost:5000/health
echo.
echo  URL ngrok:
python -c "import urllib.request, json; print(json.load(urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels'))['tunnels'][0]['public_url'])" 2>nul
if %errorlevel% neq 0 echo    No se pudo obtener (intenta de nuevo en unos segundos)
echo.
echo  Webhook URL:       [NGROK_URL]/webhook
echo.
pause