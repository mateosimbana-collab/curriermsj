# Bot mensajeria - CurrierMsj

Backend Flask para el bot de WhatsApp de CurrierMsj. La ruta comercial documentada es EE.UU. -> Ecuador. Este directorio tambien conserva el servidor operativo anterior, sus paneles de dueno y soporte, endpoints financieros, logs y resultados de pruebas.

La documentacion completa esta en el README principal del repositorio:

```text
../README.md
```

## Archivos principales

| Archivo | Funcion |
|---|---|
| `app.py` | Punto de entrada legado: arma dependencias, registra todas las rutas y crea Flask |
| `config.py` | Carga variables de entorno y nombres de tablas |
| `bot/courier_bot.py` | Orquesta estados, solicitud manual de cotizacion, rastreo, reportes y registro |
| `bot/messages.py` | Textos tipo tarjeta y botones de WhatsApp |
| `domain/constants.py` | Estados, tarifas, servicios y aliases |
| `domain/models.py` | Modelo `IncomingMessage` |
| `services/supabase_repository.py` | Repositorio REST para Supabase |
| `services/whatsapp_client.py` | Cliente WhatsApp Cloud API |
| `web/routes.py` | Rutas Flask y parser del webhook |
| `whatsapp_db.py` | Fachada legacy para imports antiguos |
| `supabase_schema.sql` | Esquema historico para instalaciones que aun usan `envios` y `estado_usuario` |
| `requirements.txt` | Dependencias Python |

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

En otra terminal:

```bash
ngrok http 5000
```

Webhook para Meta Developers:

```text
https://TU-NGROK.ngrok-free.app/webhook
```

## Variables requeridas

Crea `bot-mensajeria/.env`:

```env
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxx
PHONE_NUMBER_ID=123456789012345
WHATSAPP_API_VERSION=vXX.X
WEBHOOK_VERIFY_TOKEN=elige-un-token-aleatorio
META_APP_SECRET=app-secret-de-meta
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxx
LEGACY_DASHBOARD_USER=operador
LEGACY_DASHBOARD_PASSWORD=una-contrasena-de-al-menos-12-caracteres
BUSINESS_NAME=CurrierMsj
BOT_NAME=Rex
ROUTE_LABEL=EE.UU. -> Ecuador
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=0

# Legacy temporal, solo si restauras codigo Telegram antiguo.
TELEGRAM_BOT_TOKEN=123456:ABCxxxxxxxxxxxxxxxx
```

Telegram no es el flujo activo del codigo actual. Queda solo como referencia legacy para eliminarlo cuando WhatsApp este estable.

No uses literalmente los valores de ejemplo. El `META_APP_SECRET` valida la firma de cada webhook y las credenciales `LEGACY_DASHBOARD_*` protegen los paneles y APIs historicos. Si las credenciales del dashboard faltan o la contrasena tiene menos de 12 caracteres, esas rutas responden `503` en lugar de quedar publicas.

## Interfaces y rutas conservadas

Ejecutar `python app.py` mantiene estas superficies:

| Metodo | Ruta | Autenticacion | Funcion |
|---|---|---|---|
| `GET` | `/health` | Publica | Comprobacion basica del proceso |
| `GET` | `/webhook` | Verify token de Meta | Alta y verificacion del webhook |
| `POST` | `/webhook` | Firma `X-Hub-Signature-256` | Recepcion de mensajes y estados |
| `GET` | `/dashboard` | HTTP Basic | Panel de dueno |
| `GET` | `/dashboard/soporte` | HTTP Basic | Panel de soporte |
| `GET` | `/dashboard-assets/<archivo>` | HTTP Basic | Recursos compartidos de los paneles |
| `GET` | `/api/dashboard` | HTTP Basic | KPIs y estado de servicios |
| `GET` | `/api/envios` | HTTP Basic | Envios historicos |
| `GET` | `/api/system-stats` | HTTP Basic | Clientes, estados y reportes |
| `GET` | `/api/earnings` | HTTP Basic | Ingresos por periodo |
| `GET` | `/api/finance-summary` | HTTP Basic | Gastos, planilla, flujo de caja y margenes |
| `POST` | `/api/finance/movimientos` | HTTP Basic | Registra ingresos y egresos |
| `POST` | `/api/finance/planilla` | HTTP Basic | Registra sueldo, descuentos y pago |
| `POST` | `/api/finance/margenes` | HTTP Basic | Registra costos y ventas por producto |
| `GET` | `/api/logs` | HTTP Basic | Ultimas lineas del log |
| `GET` | `/api/test-results` | HTTP Basic | Resumen de la suite de pruebas |

El servidor aplica CORS solo a los origenes exactos declarados en `CORS_ORIGINS`. Dejalo vacio si el navegador y Flask comparten origen.

## Esquema historico y esquema unificado

Este modo puede trabajar con instalaciones historicas, pero el repositorio completo tambien incluye el modelo normalizado nuevo:

| Caso | SQL o herramienta |
|---|---|
| Instalacion historica de los paneles | `supabase_schema.sql` |
| Finanzas del panel historico | `../database/legacy_upgrade/001_finance_dashboard.sql` |
| Preflight de una base historica | `../database/legacy_upgrade/000_preserve_historical_tables.sql` |
| Instalacion nueva unificada | `../database/migrations/001_initial_schema.sql` a `005_operational_workflow.sql` |
| Migrar clientes, `envios`, reportes y FAQ | `../database/migrate_old_data.py` |

`services/supabase_repository.py` funciona como capa de compatibilidad: mantiene los metodos que espera `CourierBot` y traduce estadisticas al contrato de los dashboards anteriores. No ejecutes los dos esquemas a ciegas sobre produccion; primero identifica las tablas existentes y crea un respaldo verificable.

## Datos de prueba

Desde la raiz del repositorio:

```powershell
.\cargar_datos_prueba.bat
```

El comando ejecuta `cargar_datos_prueba.py` contra el esquema historico. `../borrar_datos.bat` tambien se conserva, pero elimina datos de varias tablas: debe usarse solo en una base de desarrollo respaldada y exige la confirmacion textual `BORRAR`.

## Pruebas

Desde la raiz, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q bot-mensajeria\tests
```

O ejecuta `../run_tests.bat` para conservar `test_results.json`, que es leido por el panel legado.
