@echo off
echo ==========================================
echo Iniciando CurrierMsj Bot + ngrok
echo ==========================================
echo.

cd /d "C:\Users\mateo\OneDrive\Documentos\GitHub\curriermsj\bot-mensajeria"

echo [1] Iniciando servidor Flask en puerto 5000...
start "Flask Server" cmd /k "py app.py"

echo [2] Esperando 5 segundos para que Flask inicie...
timeout /nobreak /t 5 >nul

echo [3] Iniciando ngrok en puerto 5000...
echo.
echo ==========================================
echo TU URL PUBLICA SERA:
echo https://xxxxxxxx.ngrok.io
echo ==========================================
echo.
echo [IMPORTANTE] Configura el webhook en Meta:
echo URL: https://TU-URL-DE-ARRIBA/webhook
echo Token: curriermsj_secret
echo.
ngrok http 5000 --log stdout
