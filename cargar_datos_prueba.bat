@echo off
title CurrierMsj - Cargar datos de prueba
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================
echo  CurrierMsj - Cargar datos de prueba
echo ============================================
echo.

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

echo Leyendo credenciales de Supabase...
echo URL: %SUPABASE_URL%
echo.
echo [1/7] Insertando clientes de prueba...
curl -s -X POST "%API%/clientes" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: resolution=merge-duplicates" -d "[
  {\"phone_number\":\"593991234567\",\"nombre\":\"Juan\",\"apellido\":\"Perez\",\"ciudad\":\"Guayaquil\",\"telefono_contacto\":\"593991234567\"},
  {\"phone_number\":\"593963935914\",\"nombre\":\"Maria\",\"apellido\":\"Gomez\",\"ciudad\":\"Quito\",\"telefono_contacto\":\"593963935914\"},
  {\"phone_number\":\"593980102030\",\"nombre\":\"Carlos\",\"apellido\":\"Lopez\",\"ciudad\":\"Cuenca\",\"telefono_contacto\":\"593980102030\"},
  {\"phone_number\":\"593990304050\",\"nombre\":\"Ana\",\"apellido\":\"Martinez\",\"ciudad\":\"Manta\",\"telefono_contacto\":\"593990304050\"},
  {\"phone_number\":\"593970506070\",\"nombre\":\"Pedro\",\"apellido\":\"Ramirez\",\"ciudad\":\"Ambato\",\"telefono_contacto\":\"593970506070\"}
]" >nul
echo    OK - 5 clientes insertados

echo [2/7] Insertando envios de prueba...
curl -s -X POST "%API%/envios" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" -d "[
  {\"phone_number\":\"593991234567\",\"remitente\":\"Juan Perez\",\"destinatario\":\"Lucia Perez\",\"direccion_origen\":\"Miami, FL\",\"direccion_destino\":\"Guayaquil, Ecuador\",\"tipo_paquete\":\"Documentos\",\"peso\":\"Menos 1 kg\",\"servicio_envio\":\"Express\",\"valor_cotizado\":45.00,\"estado\":\"entregado\",\"instrucciones\":\"Fragil\"},
  {\"phone_number\":\"593963935914\",\"remitente\":\"Maria Gomez\",\"destinatario\":\"Roberto Gomez\",\"direccion_origen\":\"New York, NY\",\"direccion_destino\":\"Quito, Ecuador\",\"tipo_paquete\":\"Paquete pequeno\",\"peso\":\"1 - 5 kg\",\"servicio_envio\":\"Estandar\",\"valor_cotizado\":65.50,\"estado\":\"en_transito\",\"instrucciones\":\"Ninguna\"},
  {\"phone_number\":\"593980102030\",\"remitente\":\"Carlos Lopez\",\"destinatario\":\"Sofia Lopez\",\"direccion_origen\":\"Los Angeles, CA\",\"direccion_destino\":\"Cuenca, Ecuador\",\"tipo_paquete\":\"Paquete mediano\",\"peso\":\"1 - 5 kg\",\"servicio_envio\":\"Estandar\",\"valor_cotizado\":78.00,\"estado\":\"pendiente\",\"instrucciones\":\"Urgente\"},
  {\"phone_number\":\"593990304050\",\"remitente\":\"Ana Martinez\",\"destinatario\":\"Luis Martinez\",\"direccion_origen\":\"Houston, TX\",\"direccion_destino\":\"Manta, Ecuador\",\"tipo_paquete\":\"Paquete grande\",\"peso\":\"Mas 5 kg\",\"servicio_envio\":\"Economico\",\"valor_cotizado\":120.00,\"estado\":\"pendiente\",\"instrucciones\":\"Ninguna\"},
  {\"phone_number\":\"593970506070\",\"remitente\":\"Pedro Ramirez\",\"destinatario\":\"Diana Ramirez\",\"direccion_origen\":\"Chicago, IL\",\"direccion_destino\":\"Ambato, Ecuador\",\"tipo_paquete\":\"Documentos\",\"peso\":\"Menos 1 kg\",\"servicio_envio\":\"Express\",\"valor_cotizado\":35.00,\"estado\":\"entregado\",\"instrucciones\":\"Fragil\"},
  {\"phone_number\":\"593991234567\",\"remitente\":\"Juan Perez\",\"destinatario\":\"Mario Perez\",\"direccion_origen\":\"Orlando, FL\",\"direccion_destino\":\"Guayaquil, Ecuador\",\"tipo_paquete\":\"Paquete pequeno\",\"peso\":\"1 - 5 kg\",\"servicio_envio\":\"Express\",\"valor_cotizado\":55.00,\"estado\":\"en_transito\",\"instrucciones\":\"Urgente\"}
]" >nul
echo    OK - 6 envios insertados

echo [3/7] Insertando reportes de prueba...
curl -s -X POST "%API%/reportes" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" -d "[
  {\"phone_number\":\"593991234567\",\"tracking_code\":null,\"categoria\":\"Danado\",\"descripcion\":\"El paquete llego con la caja abollada\",\"estado\":\"abierto\"},
  {\"phone_number\":\"593963935914\",\"tracking_code\":null,\"categoria\":\"No llego\",\"descripcion\":\"El envio no ha llegado en la fecha estimada\",\"estado\":\"abierto\"},
  {\"phone_number\":\"593980102030\",\"tracking_code\":null,\"categoria\":\"Incompleto\",\"descripcion\":\"Falta un articulo dentro del paquete\",\"estado\":\"cerrado\"}
]" >nul
echo    OK - 3 reportes insertados

echo [4/7] Insertando FAQ adicional...
curl -s -X POST "%API%/faq" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: resolution=merge-duplicates" -d "[
  {\"pregunta\":\"rastrear\",\"respuesta\":\"Envia tu codigo CUR-XXXXX para rastrear tu paquete.\",\"categoria\":\"envios\"},
  {\"pregunta\":\"contacto\",\"respuesta\":\"Puedes contactarnos al Whatsapp o llamar en horario laboral.\",\"categoria\":\"general\"}
]" >nul
echo    OK - FAQ actualizada

echo [5/7] Insertando movimientos financieros...
curl -s -X POST "%API%/movimientos_financieros" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" -d "[
  {\"tipo\":\"ingreso\",\"categoria\":\"envios\",\"descripcion\":\"Envio Juan Perez - Express\",\"monto\":45.00,\"tipo_gasto\":null},
  {\"tipo\":\"ingreso\",\"categoria\":\"envios\",\"descripcion\":\"Envio Maria Gomez - Estandar\",\"monto\":65.50,\"tipo_gasto\":null},
  {\"tipo\":\"ingreso\",\"categoria\":\"envios\",\"descripcion\":\"Envio Pedro Ramirez - Express\",\"monto\":35.00,\"tipo_gasto\":null},
  {\"tipo\":\"egreso\",\"categoria\":\"logistica\",\"descripcion\":\"Transporte aereo (lote semanal)\",\"monto\":200.00,\"tipo_gasto\":\"variable\"},
  {\"tipo\":\"egreso\",\"categoria\":\"operativo\",\"descripcion\":\"Plan internet mensual\",\"monto\":45.00,\"tipo_gasto\":\"fijo\"}
]" >nul
echo    OK - 5 movimientos insertados

echo [6/7] Insertando planilla de personal...
curl -s -X POST "%API%/planilla_personal" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" -d "[
  {\"nombre\":\"Ana Torres\",\"cargo\":\"Agente de soporte\",\"sueldo\":600.00,\"descuentos\":15.00,\"estado_pago\":\"pagado\"},
  {\"nombre\":\"Luis Castro\",\"cargo\":\"Coordinador logistica\",\"sueldo\":800.00,\"descuentos\":20.00,\"estado_pago\":\"pagado\"},
  {\"nombre\":\"Marta Ruiz\",\"cargo\":\"Agente de soporte\",\"sueldo\":600.00,\"descuentos\":0,\"estado_pago\":\"pendiente\"}
]" >nul
echo    OK - 3 empleados insertados

echo [7/7] Insertando margenes de producto...
curl -s -X POST "%API%/margenes_producto" -H "Content-Type: application/json" -H "%AUTH%" -H "Authorization: Bearer %SUPABASE_KEY%" -H "Prefer: return=minimal" -d "[
  {\"producto\":\"Documentos - Express\",\"categoria\":\"Documentos\",\"precio_venta\":45.00,\"costo_producto\":20.00,\"unidades\":10},
  {\"producto\":\"Paquete pequeno - Estandar\",\"categoria\":\"Paquete pequeno\",\"precio_venta\":65.50,\"costo_producto\":30.00,\"unidades\":5},
  {\"producto\":\"Paquete mediano - Estandar\",\"categoria\":\"Paquete mediano\",\"precio_venta\":78.00,\"costo_producto\":40.00,\"unidades\":3},
  {\"producto\":\"Paquete grande - Economico\",\"categoria\":\"Paquete grande\",\"precio_venta\":120.00,\"costo_producto\":65.00,\"unidades\":2}
]" >nul
echo    OK - 4 margenes insertados

echo.
echo ============================================
echo  Datos de prueba cargados exitosamente!
echo ============================================
echo.
echo Puedes ver los datos en:
echo   Dashboard Dueno:   http://localhost:5000/dashboard
echo   Dashboard Soporte: http://localhost:5000/dashboard/soporte
echo.
pause
