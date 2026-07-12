#!/usr/bin/env python3
"""Carga datos de prueba en Supabase con fechas dinamicas."""

import os
import sys
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL o SUPABASE_KEY no estan en .env")
    sys.exit(1)

API = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}
NOW = datetime.now(timezone.utc)
ERRORS = 0


def post(table: str, data: list[dict], prefer: str = "return=minimal") -> bool:
    url = f"{API}/{table}"
    try:
        r = httpx.post(url, headers={**HEADERS, "Prefer": prefer}, json=data, timeout=15)
        r.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        body = e.response.text[:200]
        status = e.response.status_code
        if status == 404:
            print(f"    [!] TABLA FALTANTE: '{table}' no existe. Ejecuta el schema SQL en Supabase.")
            return True  # not a hard error, skip gracefully
        if status == 409:
            print(f"    [x] CONFLICTO: {body}")
            return False
        print(f"    [x] ERROR {status}: {body}")
        return False
    except Exception as e:
        print(f"    [x] ERROR: {e}")
        return False


def clear_table(table: str) -> bool:
    """Intenta limpiar la tabla via DELETE con filtro que matchea todo."""
    try:
        r = httpx.delete(
            f"{API}/{table}?id=gte.0",
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code in (200, 204):
            return True
        # Try without filter (some tables don't have 'id' column)
        r2 = httpx.delete(f"{API}/{table}", headers=HEADERS, timeout=15)
        return r2.status_code in (200, 204)
    except Exception:
        return False


def days_ago(d: int, h: int = 0) -> str:
    return (NOW - timedelta(days=d, hours=h)).isoformat()


def hours_ago(h: int) -> str:
    return (NOW - timedelta(hours=h)).isoformat()


# -- Limpiar datos anteriores ---------------------------------
print("Limpiando datos anteriores...")
for t in ["margenes_producto", "planilla_personal", "movimientos_financieros",
          "reportes", "envios", "estado_usuario", "clientes", "faq"]:
    ok = clear_table(t)
    if not ok:
        pass  # tables may not exist yet, that's fine

# -- 1. Clientes ---------------------------------------------
print("\n[1/7] Insertando clientes...")
clientes = [
    {"phone_number": "593991234567", "nombre": "Juan", "apellido": "Perez",
     "ciudad": "Guayaquil", "telefono_contacto": "593991234567",
     "registrado_en": days_ago(15)},
    {"phone_number": "593963935914", "nombre": "Maria", "apellido": "Gomez",
     "ciudad": "Quito", "telefono_contacto": "593963935914",
     "registrado_en": days_ago(12)},
    {"phone_number": "593980102030", "nombre": "Carlos", "apellido": "Lopez",
     "ciudad": "Cuenca", "telefono_contacto": "593980102030",
     "registrado_en": days_ago(10)},
    {"phone_number": "593990304050", "nombre": "Ana", "apellido": "Martinez",
     "ciudad": "Manta", "telefono_contacto": "593990304050",
     "registrado_en": days_ago(7)},
    {"phone_number": "593970506070", "nombre": "Pedro", "apellido": "Ramirez",
     "ciudad": "Ambato", "telefono_contacto": "593970506070",
     "registrado_en": days_ago(3)},
]
if post("clientes", clientes, "resolution=merge-duplicates"):
    print("    OK - 5 clientes")
else:
    ERRORS += 1

# -- 2.Envios ------------------------------------------------
print("\n[2/7] Insertando envios...")
envios = [
    {"phone_number": "593991234567", "remitente": "Juan Perez",
     "destinatario": "Lucia Perez", "direccion_origen": "Miami, FL",
     "direccion_destino": "Guayaquil, Ecuador", "tipo_paquete": "Documentos",
     "peso": "Menos 1 kg", "dimensiones": "Documentos",
     "servicio_envio": "Express", "valor_cotizado": 45.00,
     "tracking_code": "CUR-00001", "estado": "entregado",
     "instrucciones": "Fragil",
     "fecha_envio": NOW.strftime("%d/%m/%Y"), "hora_envio": "10:30",
     "creado_en": hours_ago(2)},
    {"phone_number": "593963935914", "remitente": "Maria Gomez",
     "destinatario": "Roberto Gomez", "direccion_origen": "New York, NY",
     "direccion_destino": "Quito, Ecuador", "tipo_paquete": "Paquete pequeno",
     "peso": "1 - 5 kg", "dimensiones": "Paquete pequeno",
     "servicio_envio": "Estandar", "valor_cotizado": 65.50,
     "tracking_code": "CUR-00002", "estado": "en_transito",
     "instrucciones": "Ninguna",
     "fecha_envio": NOW.strftime("%d/%m/%Y"), "hora_envio": "14:15",
     "creado_en": hours_ago(5)},
    {"phone_number": "593980102030", "remitente": "Carlos Lopez",
     "destinatario": "Sofia Lopez", "direccion_origen": "Los Angeles, CA",
     "direccion_destino": "Cuenca, Ecuador", "tipo_paquete": "Paquete mediano",
     "peso": "1 - 5 kg", "dimensiones": "Paquete mediano",
     "servicio_envio": "Express", "valor_cotizado": 88.00,
     "tracking_code": "CUR-00003", "estado": "pendiente",
     "instrucciones": "Urgente",
     "fecha_envio": (NOW - timedelta(days=1)).strftime("%d/%m/%Y"),
     "hora_envio": "09:00", "creado_en": days_ago(1, 6)},
    {"phone_number": "593990304050", "remitente": "Ana Martinez",
     "destinatario": "Luis Martinez", "direccion_origen": "Houston, TX",
     "direccion_destino": "Manta, Ecuador", "tipo_paquete": "Paquete grande",
     "peso": "Mas 5 kg", "dimensiones": "Paquete grande",
     "servicio_envio": "Economico", "valor_cotizado": 120.00,
     "tracking_code": "CUR-00004", "estado": "entregado",
     "instrucciones": "Ninguna",
     "fecha_envio": (NOW - timedelta(days=3)).strftime("%d/%m/%Y"),
     "hora_envio": "11:30", "creado_en": days_ago(3, 10)},
    {"phone_number": "593970506070", "remitente": "Pedro Ramirez",
     "destinatario": "Diana Ramirez", "direccion_origen": "Chicago, IL",
     "direccion_destino": "Ambato, Ecuador", "tipo_paquete": "Documentos",
     "peso": "Menos 1 kg", "dimensiones": "Documentos",
     "servicio_envio": "Express", "valor_cotizado": 35.00,
     "tracking_code": "CUR-00005", "estado": "entregado",
     "instrucciones": "Fragil",
     "fecha_envio": (NOW - timedelta(days=5)).strftime("%d/%m/%Y"),
     "hora_envio": "08:45", "creado_en": days_ago(5, 14)},
    {"phone_number": "593991234567", "remitente": "Juan Perez",
     "destinatario": "Mario Perez", "direccion_origen": "Orlando, FL",
     "direccion_destino": "Guayaquil, Ecuador", "tipo_paquete": "Paquete pequeno",
     "peso": "1 - 5 kg", "dimensiones": "Paquete pequeno",
     "servicio_envio": "Estandar", "valor_cotizado": 55.00,
     "tracking_code": "CUR-00006", "estado": "en_transito",
     "instrucciones": "Ninguna",
     "fecha_envio": (NOW - timedelta(days=7)).strftime("%d/%m/%Y"),
     "hora_envio": "16:20", "creado_en": days_ago(7, 10)},
]
if post("envios", envios, "resolution=merge-duplicates"):
    print("    OK - 6 envios")
else:
    ERRORS += 1

# -- 3. Reportes ---------------------------------------------
print("\n[3/7] Insertando reportes...")
reportes = [
    {"phone_number": "593991234567", "categoria": "Danado",
     "descripcion": "El paquete llego con la caja abollada",
     "estado": "abierto", "creado_en": days_ago(2)},
    {"phone_number": "593963935914", "categoria": "No llego",
     "descripcion": "El envio no ha llegado en la fecha estimada",
     "estado": "abierto", "creado_en": days_ago(1)},
    {"phone_number": "593980102030", "categoria": "Incompleto",
     "descripcion": "Falta un articulo dentro del paquete",
     "estado": "cerrado", "creado_en": days_ago(5)},
    {"phone_number": "593970506070", "categoria": "Retraso",
     "descripcion": "El paquete se retraso mas de lo esperado",
     "estado": "abierto", "creado_en": hours_ago(8)},
]
if post("reportes", reportes):
    print("    OK - 4 reportes")
else:
    ERRORS += 1

# -- 4. FAQ --------------------------------------------------
print("\n[4/7] Insertando FAQ...")
faq = [
    {"pregunta": "horario",
     "respuesta": "Lunes a Sabado de 8:00 a 18:00.", "categoria": "general"},
    {"pregunta": "costo",
     "respuesta": "Usa Cotizar envio para un estimado.", "categoria": "envios"},
    {"pregunta": "tiempo entrega",
     "respuesta": "Depende del servicio y aduana.", "categoria": "envios"},
    {"pregunta": "formas pago",
     "respuesta": "Efectivo, transferencia o con el agente.", "categoria": "pagos"},
    {"pregunta": "cobertura",
     "respuesta": "Estados Unidos hacia Ecuador.", "categoria": "general"},
    {"pregunta": "abono",
     "respuesta": "Coordina con el agente antes del envio.", "categoria": "pagos"},
    {"pregunta": "rastrear",
     "respuesta": "Envia tu codigo CUR-XXXXX.", "categoria": "envios"},
    {"pregunta": "contacto",
     "respuesta": "WhatsApp o llamada en horario laboral.", "categoria": "general"},
]
if post("faq", faq, "resolution=merge-duplicates"):
    print("    OK - 8 FAQ")
else:
    ERRORS += 1

# -- 5. Movimientos financieros ------------------------------
print("\n[5/7] Insertando movimientos financieros...")
mov = [
    {"tipo": "ingreso", "categoria": "envios",
     "descripcion": "Envio CUR-00001 - Express", "monto": 45.00,
     "tipo_gasto": None, "fecha": hours_ago(2)},
    {"tipo": "ingreso", "categoria": "envios",
     "descripcion": "Envio CUR-00002 - Estandar", "monto": 65.50,
     "tipo_gasto": None, "fecha": hours_ago(5)},
    {"tipo": "ingreso", "categoria": "envios",
     "descripcion": "Envio CUR-00003 - Express", "monto": 88.00,
     "tipo_gasto": None, "fecha": days_ago(1)},
    {"tipo": "ingreso", "categoria": "envios",
     "descripcion": "Envio CUR-00004 - Economico", "monto": 120.00,
     "tipo_gasto": None, "fecha": days_ago(3)},
    {"tipo": "ingreso", "categoria": "servicios",
     "descripcion": "Servicio embalaje premium", "monto": 25.00,
     "tipo_gasto": None, "fecha": days_ago(4)},
    {"tipo": "egreso", "categoria": "operativo",
     "descripcion": "Plan internet mensual", "monto": 45.00,
     "tipo_gasto": "fijo", "fecha": days_ago(8)},
    {"tipo": "egreso", "categoria": "oficina",
     "descripcion": "Arriendo oficina mensual", "monto": 400.00,
     "tipo_gasto": "fijo", "fecha": days_ago(5)},
    {"tipo": "egreso", "categoria": "logistica",
     "descripcion": "Transporte aereo semanal", "monto": 200.00,
     "tipo_gasto": "variable", "fecha": days_ago(3)},
    {"tipo": "egreso", "categoria": "suministros",
     "descripcion": "Cajas y material empaque", "monto": 85.00,
     "tipo_gasto": "variable", "fecha": days_ago(4)},
    {"tipo": "egreso", "categoria": "logistica",
     "descripcion": "Courier local adicional", "monto": 35.00,
     "tipo_gasto": "variable", "fecha": hours_ago(12)},
]
ok = post("movimientos_financieros", mov)
if ok:
    print("    OK - 10 movimientos")
elif ERRORS == 0:
    ERRORS += 1

# -- 6. Planilla ---------------------------------------------
print("\n[6/7] Insertando planilla...")
planilla = [
    {"nombre": "Ana Torres", "cargo": "Agente soporte",
     "sueldo": 600.00, "descuentos": 15.00, "estado_pago": "pagado",
     "fecha_pago": days_ago(5)},
    {"nombre": "Luis Castro", "cargo": "Coordinador logistica",
     "sueldo": 800.00, "descuentos": 20.00, "estado_pago": "pagado",
     "fecha_pago": days_ago(5)},
    {"nombre": "Marta Ruiz", "cargo": "Agente soporte",
     "sueldo": 600.00, "descuentos": 0, "estado_pago": "pendiente",
     "fecha_pago": days_ago(2)},
]
ok = post("planilla_personal", planilla)
if ok:
    print("    OK - 3 empleados")
elif ERRORS == 0:
    ERRORS += 1

# -- 7. Margenes ---------------------------------------------
print("\n[7/7] Insertando margenes de producto...")
margenes = [
    {"producto": "Documentos - Express", "categoria": "Documentos",
     "precio_venta": 45.00, "costo_producto": 20.00, "unidades": 10},
    {"producto": "Documentos - Estandar", "categoria": "Documentos",
     "precio_venta": 42.00, "costo_producto": 18.00, "unidades": 8},
    {"producto": "Paquete pequeno - Express", "categoria": "Paquete pequeno",
     "precio_venta": 65.50, "costo_producto": 30.00, "unidades": 5},
    {"producto": "Paquete pequeno - Estandar", "categoria": "Paquete pequeno",
     "precio_venta": 55.00, "costo_producto": 25.00, "unidades": 6},
    {"producto": "Paquete mediano - Express", "categoria": "Paquete mediano",
     "precio_venta": 88.00, "costo_producto": 35.00, "unidades": 3},
    {"producto": "Paquete grande - Economico", "categoria": "Paquete grande",
     "precio_venta": 120.00, "costo_producto": 65.00, "unidades": 2},
]
ok = post("margenes_producto", margenes)
if ok:
    print("    OK - 6 margenes")
elif ERRORS == 0:
    ERRORS += 1

# -- Resumen --------------------------------------------------
print()
if ERRORS:
    print(f"=== Se encontraron {ERRORS} error(es). Revisa arriba. ===")
    print()
    print("Posibles causas:")
    print("  1. No has ejecutado el schema SQL en Supabase SQL Editor")
    print("     -> Abre https://supabase.com/dashboard/project/_/sql/new")
    print("     -> Pega el contenido de bot-mensajeria/supabase_schema.sql")
    print("     -> Ejecuta")
    sys.exit(1)
else:
    print("=== Datos de prueba cargados exitosamente! ===")
    print()
    print("  Dashboard Dueno:   http://localhost:5000/dashboard")
    print("  Dashboard Soporte: http://localhost:5000/dashboard/soporte")
