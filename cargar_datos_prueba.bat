@echo off
title CurrierMsj - Cargar datos de prueba
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================
echo  CurrierMsj - Cargar datos de prueba
echo ============================================
echo.

cd /d "bot-mensajeria"

echo Ejecutando script Python...
echo.
python cargar_datos_prueba.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Fallo al cargar datos. Revisa los mensajes arriba.
) else (
    echo.
    echo Puedes ver los datos en:
    echo   Dashboard Dueno:   http://localhost:5000/dashboard
    echo   Dashboard Soporte: http://localhost:5000/dashboard/soporte
)

echo.
pause
