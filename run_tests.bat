@echo off
title CurrierMsj - Ejecutar pruebas
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================
echo  CurrierMsj - Ejecutar todas las pruebas
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" if not exist "bot-mensajeria\.venv\Scripts\python.exe" (
    echo No se encontro .venv. Creando...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r bot-mensajeria\requirements.txt
    pip install pytest pytest-mock
) else (
    if exist ".venv\Scripts\python.exe" (
        set PYTHON=.venv\Scripts\python.exe
    ) else (
        set PYTHON=bot-mensajeria\.venv\Scripts\python.exe
    )
)

if exist ".venv\Scripts\activate" call .venv\Scripts\activate

set RESULTS_FILE=test_results.json
set RESULTS_DIR=bot-mensajeria

echo Ejecutando %PYTHON% -m pytest...
echo.

%PYTHON% -m pytest bot-mensajeria/tests/unit/ -v --tb=short --json-report --json-report-file=%RESULTS_DIR%/%RESULTS_FILE% 2>nul

if %errorlevel% equ 0 (
    if not exist "%RESULTS_DIR%/%RESULTS_FILE%" (
        :: fallback: generate results manually
        %PYTHON% -m pytest bot-mensajeria/tests/unit/ -v --tb=short 2>&1 > test_output.tmp
        type test_output.tmp
        echo.
        echo ============================================
        echo  PRUEBAS COMPLETADAS
        echo ============================================
        del test_output.tmp 2>nul
    ) else (
        echo.
        %PYTHON% -c "import json; d=json.load(open('%RESULTS_DIR%/%RESULTS_FILE%')); print(f'Total: {d.get(\"total\",\"?\")}, Pasadas: {d.get(\"passed\",\"?\")}, Fallidas: {d.get(\"failed\",\"?\")}, Errores: {d.get(\"errors\",\"?\")}')" 2>nul
        echo.
        echo Resultados guardados en: %RESULTS_DIR%/%RESULTS_FILE%
    )
    echo.
    echo Puedes ver los resultados en el Dashboard Soporte:
    echo   http://localhost:5000/dashboard/soporte
) else (
    echo.
    echo ALGUNAS PRUEBAS FALLARON.
    %PYTHON% -m pytest bot-mensajeria/tests/unit/ -v --tb=short
)

echo.
pause
