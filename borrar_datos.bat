@echo off
title CurrierMsj - Borrar todos los datos
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================
echo  CurrierMsj - BORRAR TODOS LOS DATOS
echo ============================================
echo.
echo  ATENCION: Esto eliminara TODOS los registros
echo  de las tablas: clientes, envios, estado_usuario,
echo  reportes, movimientos_financieros, planilla_personal,
echo  margenes_producto y FAQ.
echo.
echo  Los datos NO se pueden recuperar.
echo.
set /p confirm="Escribe BORRAR para confirmar: "
if /i not "%confirm%"=="BORRAR" (
    echo Operacion cancelada.
    pause
    exit /b 0
)

where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: curl no esta instalado
    pause
    exit /b 1
)

if not exist "bot-mensajeria\.env" (
    echo ERROR: No se encuentra bot-mensajeria/.env
    pause
    exit /b 1
)

for /f "tokens=1,* delims==" %%a in ('type "bot-mensajeria\.env" ^| findstr /b "SUPABASE_URL"') do set "SUPABASE_URL=%%b"
for /f "tokens=1,* delims==" %%a in ('type "bot-mensajeria\.env" ^| findstr /b "SUPABASE_KEY"') do set "SUPABASE_KEY=%%b"

if "%SUPABASE_URL%"=="" (
    echo ERROR: No se pudo leer SUPABASE_URL de .env
    pause
    exit /b 1
)

set AUTH=apikey: %SUPABASE_KEY%
set API=%SUPABASE_URL%/rest/v1

echo.
echo Eliminando datos...

echo [1/8] Borrando margenes_producto...
curl -s -X DELETE "%API%/margenes_producto" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [2/8] Borrando planilla_personal...
curl -s -X DELETE "%API%/planilla_personal" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [3/8] Borrando movimientos_financieros...
curl -s -X DELETE "%API%/movimientos_financieros" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [4/8] Borrando reportes...
curl -s -X DELETE "%API%/reportes" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [5/8] Borrando envios...
curl -s -X DELETE "%API%/envios" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [6/8] Borrando estado_usuario...
curl -s -X DELETE "%API%/estado_usuario" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [7/8] Borrando clientes...
curl -s -X DELETE "%API%/clientes" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" >nul
echo    OK

echo [8/8] Restaurando FAQ base...
curl -s -X POST "%API%/faq" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: resolution=merge-duplicates" -d "[
  {\"pregunta\":\"horario\",\"respuesta\":\"Nuestro horario de atencion es de Lunes a Sabado de 8:00 a 18:00.\",\"categoria\":\"general\"},
  {\"pregunta\":\"costo\",\"respuesta\":\"El costo depende del peso y la ruta. Usa la opcion Cotizar envio para obtener un estimado.\",\"categoria\":\"envios\"},
  {\"pregunta\":\"tiempo entrega\",\"respuesta\":\"El tiempo estimado EE.UU. a Ecuador depende del servicio y aduana.\",\"categoria\":\"envios\"},
  {\"pregunta\":\"formas pago\",\"respuesta\":\"Aceptamos efectivo, transferencia bancaria y pago acordado con el agente.\",\"categoria\":\"pagos\"},
  {\"pregunta\":\"cobertura\",\"respuesta\":\"La ruta principal del servicio es Estados Unidos hacia Ecuador.\",\"categoria\":\"general\"},
  {\"pregunta\":\"abono\",\"respuesta\":\"Puedes coordinar abono o pago completo con el agente antes del envio.\",\"categoria\":\"pagos\"}
]" >nul
echo    OK - FAQ restaurada a valores base

echo.
echo ============================================
echo  Todos los datos fueron eliminados.
echo  FAQ restaurada a valores base.
echo ============================================
echo.
pause
