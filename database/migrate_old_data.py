# -*- coding: utf-8 -*-
"""Migrate old envios to new paquetes/clientes/tracking_events"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, re, os, json, uuid
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_KEY env vars")
    sys.exit(1)
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def supabase_get(table, params=None):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def supabase_post(table, data):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=data)
    if r.status_code == 201 or r.status_code == 200:
        return r.json() if r.text else [data]
    raise Exception(f"Error inserting into {table}: {r.status_code} {r.text}")

def parse_peso(peso_label):
    if not peso_label: return None
    peso_clean = peso_label.lower().strip()
    if "menos de 1" in peso_clean: return 0.5
    if "1 - 5" in peso_clean: return 3.0
    if "más de 5" in peso_clean or "mas de 5" in peso_clean: return 6.0
    try: return float(re.sub(r'[^\d.]', '', peso_clean))
    except: return None

def map_estado(old_estado):
    mapping = {
        "pendiente": "recibido_en_usa",
        "en tránsito": "en_transito",
        "en transito": "en_transito",
        "en aduana": "en_aduana",
        "en destino": "en_destino",
        "entregado": "entregado",
        "devuelto": "devuelto",
        "retenido": "retenido",
    }
    return mapping.get(old_estado.lower().strip(), "recibido_en_usa")

# 1. Get old envios
print("Reading old envios...")
envios = supabase_get("envios", params={"order": "id.asc"})
print(f"Found {len(envios)} envios")

# 2. Create clientes from unique phone_numbers
phone_to_cliente = {}
for e in envios:
    phone = e.get("phone_number", "")
    if phone and phone not in phone_to_cliente:
        # Check if client already exists by phone
        existing = supabase_get("clientes", params={"telefono": f"eq.{phone}", "select": "id"})
        if existing:
            phone_to_cliente[phone] = existing[0]["id"]
            print(f"  Client already exists for {phone}: id={existing[0]['id']}")
        else:
            cli = {
                "nombre_completo": e.get("remitente", "Migrado"),
                "cedula": f"MIG-{phone[-6:]}",
                "telefono": phone,
                "email": "",
                "ciudad": "Guayaquil",
                "direccion": e.get("direccion_origen", ""),
                "tipo_cliente": "regular",
                "notas": f"Migrado automaticamente. Remitente original: {e.get('remitente', '')}",
            }
            try:
                res = supabase_post("clientes", cli)
                new_id = res[0]["id"]
                phone_to_cliente[phone] = new_id
                print(f"  Created client {cli['nombre_completo']} ({phone}) → id={new_id}")
            except Exception as ex:
                print(f"  ERROR creating client for {phone}: {ex}")

# 3. Migrate envios to paquetes
for e in envios:
    tracking = e.get("tracking_code", "")
    phone = e.get("phone_number", "")
    cliente_id = phone_to_cliente.get(phone)
    
    # Check if paquete already exists with this tracking code
    existing_paq = supabase_get("paquetes", params={"tracking_code": f"eq.{tracking}", "select": "id"})
    if existing_paq:
        print(f"  Paquete {tracking} already exists, skipping")
        continue
    
    paquete = {
        "tracking_code": tracking,
        "cliente_id": cliente_id,
        "remitente_nombre": e.get("remitente", ""),
        "remitente_pais": "Estados Unidos",
        "destinatario_nombre": e.get("destinatario", ""),
        "destinatario_direccion": e.get("direccion_destino", ""),
        "contenido": e.get("tipo_paquete", ""),
        "peso_kg": parse_peso(e.get("peso", "")),
        "valor_declarado": float(e.get("valor_cotizado") or 0),
        "estado_actual": map_estado(e.get("estado", "pendiente")),
        "etiqueta_actual": None,
        "created_at": e.get("creado_en", datetime.utcnow().isoformat()),
        "updated_at": e.get("creado_en", datetime.utcnow().isoformat()),
    }
    
    try:
        res = supabase_post("paquetes", paquete)
        paq_id = res[0]["id"]
        print(f"  Created paquete {tracking} -> id={paq_id}")
        
        # 4. Create tracking_event
        event = {
            "paquete_id": paq_id,
            "etiqueta": paquete["estado_actual"],
            "descripcion": f"Migrado desde sistema anterior. Estado original: '{e.get('estado', 'pendiente')}'",
            "ubicacion": "Migracion",
            "created_at": e.get("creado_en", datetime.utcnow().isoformat()),
        }
        supabase_post("tracking_events", event)
        print(f"  Created tracking_event for {tracking}")
    except Exception as ex:
        print(f"  ERROR migrating {tracking}: {ex}")

# 5. Second pass: create missing tracking_events for existing paquetes
print("\nChecking for missing tracking_events...")
paquetes = supabase_get("paquetes", params={"select": "id,tracking_code,estado_actual,created_at"})
for p in paquetes:
    existing = supabase_get("tracking_events", params={"paquete_id": f"eq.{p['id']}", "select": "id"})
    if not existing:
        event = {
            "paquete_id": p["id"],
            "etiqueta": p["estado_actual"],
            "descripcion": "Migrado desde sistema anterior",
            "ubicacion": "Migracion",
            "created_at": p["created_at"],
        }
        supabase_post("tracking_events", event)
        print(f"  Created tracking_event for {p['tracking_code']}")
    else:
        print(f"  {p['tracking_code']} already has {len(existing)} event(s)")

print("\nMigration complete!")
