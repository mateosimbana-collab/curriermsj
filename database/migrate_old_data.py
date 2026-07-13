# -*- coding: utf-8 -*-
"""Migrate preserved historical tables into the unified schema."""

import hashlib
import io
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()
load_dotenv("bot-mensajeria/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
CHECK_ONLY = "--check" in sys.argv

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: configura SUPABASE_URL y SUPABASE_SERVICE_KEY")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def supabase_get(table: str, params: dict[str, Any] | None = None, *, missing_ok: bool = False):
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params=params,
        timeout=30,
    )
    if missing_ok and response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()


def supabase_post(table: str, data: dict[str, Any]):
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        json=data,
        timeout=30,
    )
    if response.status_code in (200, 201):
        return response.json() if response.text else [data]
    raise RuntimeError(f"Error inserting into {table}: {response.status_code} {response.text}")


def table_exists(table: str, field: str = "id") -> bool:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params={"select": field, "limit": 1},
        timeout=15,
    )
    return response.status_code == 200


def parse_peso(peso_label: Any) -> float | None:
    if not peso_label:
        return None
    cleaned = str(peso_label).lower().strip()
    if "menos de 1" in cleaned:
        return 0.5
    if "1 - 5" in cleaned:
        return 3.0
    if "más de 5" in cleaned or "mas de 5" in cleaned:
        return 6.0
    try:
        return float(re.sub(r"[^\d.]", "", cleaned))
    except ValueError:
        return None


def map_estado(old_estado: Any) -> str:
    mapping = {
        "pendiente": "recibido_en_usa",
        "recibido": "recibido_en_usa",
        "en tránsito": "en_transito",
        "en transito": "en_transito",
        "en aduana": "en_aduana",
        "en destino": "en_destino",
        "entregado": "entregado",
        "devuelto": "devuelto",
        "retenido": "retenido",
    }
    return mapping.get(str(old_estado or "").lower().strip(), "recibido_en_usa")


def synthetic_cedula(phone: str) -> str:
    digest = hashlib.sha256(phone.encode("utf-8")).hexdigest()[:16].upper()
    return f"MIG-{digest}"


def masked_phone(phone: str) -> str:
    return f"***{phone[-4:]}" if len(phone) >= 4 else "***"


def ensure_client(
    phone: str,
    *,
    name: str = "Cliente migrado",
    city: str = "",
    alternate_phone: str = "",
    address: str = "",
    created_at: str = "",
) -> str:
    existing = supabase_get("clientes", {"telefono": f"eq.{phone}", "select": "id"})
    if existing:
        return existing[0]["id"]

    payload = {
        "cedula": synthetic_cedula(phone),
        "nombre_completo": name.strip() or "Cliente migrado",
        "telefono": phone,
        "telefono_alternativo": alternate_phone or None,
        "ciudad": city or "Guayaquil",
        "direccion": address or None,
        "tipo_cliente": "regular",
        "notas": "Migrado automaticamente desde el esquema historico",
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    result = supabase_post("clientes", payload)
    return result[0]["id"]


required_targets = ("clientes", "paquetes", "tracking_events", "reportes", "faq")
missing_targets = [table for table in required_targets if not table_exists(table)]
if missing_targets:
    print("ERROR: faltan tablas unificadas: " + ", ".join(missing_targets))
    print("Ejecuta primero el preflight historico y las migraciones 001 a 005.")
    sys.exit(1)

legacy_clients = supabase_get("clientes_legacy", {"order": "registrado_en.asc"}, missing_ok=True)
legacy_reports = supabase_get("reportes_legacy", {"order": "id.asc"}, missing_ok=True)
legacy_faq = supabase_get("faq_legacy", {"order": "id.asc"}, missing_ok=True)
envios = supabase_get("envios", {"order": "id.asc"}, missing_ok=True)

print("Preflight historico")
print(f"  clientes_legacy: {len(legacy_clients)}")
print(f"  envios: {len(envios)}")
print(f"  reportes_legacy: {len(legacy_reports)}")
print(f"  faq_legacy: {len(legacy_faq)}")
if CHECK_ONLY:
    print("CHECK OK: no se modificaron datos")
    sys.exit(0)

phone_to_client: dict[str, str] = {}
errors = 0

print("\nMigrando clientes...")
for old in legacy_clients:
    phone = str(old.get("phone_number") or "").strip()
    if not phone:
        print("  OMITIDO: cliente historico sin telefono")
        errors += 1
        continue
    name = " ".join(
        part.strip()
        for part in (str(old.get("nombre") or ""), str(old.get("apellido") or ""))
        if part.strip()
    )
    try:
        phone_to_client[phone] = ensure_client(
            phone,
            name=name,
            city=str(old.get("ciudad") or ""),
            alternate_phone=str(old.get("telefono_contacto") or ""),
            created_at=str(old.get("registrado_en") or ""),
        )
        print(f"  OK {masked_phone(phone)}")
    except Exception as exc:
        errors += 1
        print(f"  ERROR cliente {masked_phone(phone)}: {exc}")

print("\nMigrando envios...")
tracking_to_package: dict[str, str] = {}
for old in envios:
    legacy_id = str(old.get("id") or "")
    tracking = str(old.get("tracking_code") or f"LEG-{legacy_id}").strip().upper()
    phone = str(old.get("phone_number") or old.get("telefono_remitente") or "").strip()
    if not phone:
        phone = f"legacy-envio-{legacy_id}"
    try:
        client_id = phone_to_client.get(phone) or ensure_client(
            phone,
            name=str(old.get("remitente") or "Cliente migrado"),
            alternate_phone=str(old.get("telefono_remitente") or ""),
            address=str(old.get("direccion_origen") or ""),
            created_at=str(old.get("creado_en") or ""),
        )
        phone_to_client[phone] = client_id
        existing = supabase_get("paquetes", {"tracking_code": f"eq.{tracking}", "select": "id"})
        if existing:
            package_id = existing[0]["id"]
        else:
            package = {
                "tracking_code": tracking,
                "cliente_id": client_id,
                "remitente_nombre": old.get("remitente") or "Cliente migrado",
                "remitente_telefono": old.get("telefono_remitente") or phone,
                "remitente_pais": "Estados Unidos",
                "destinatario_nombre": old.get("destinatario") or "Por confirmar",
                "destinatario_telefono": old.get("telefono_destinatario") or None,
                "destinatario_direccion": old.get("direccion_destino") or "Por confirmar",
                "contenido": old.get("tipo_paquete") or None,
                "peso_kg": parse_peso(old.get("peso")),
                "valor_flete": float(old.get("valor_cotizado") or 0),
                "estado_actual": map_estado(old.get("estado")),
                "created_at": old.get("creado_en") or datetime.now(timezone.utc).isoformat(),
                "updated_at": old.get("creado_en") or datetime.now(timezone.utc).isoformat(),
            }
            package = {key: value for key, value in package.items() if value is not None}
            package_id = supabase_post("paquetes", package)[0]["id"]
        tracking_to_package[tracking] = package_id

        events = supabase_get("tracking_events", {"paquete_id": f"eq.{package_id}", "select": "id"})
        if not events:
            supabase_post(
                "tracking_events",
                {
                    "paquete_id": package_id,
                    "etiqueta": map_estado(old.get("estado")),
                    "descripcion": f"Migrado desde envio historico #{legacy_id}",
                    "ubicacion": "Migracion",
                    "created_at": old.get("creado_en") or datetime.now(timezone.utc).isoformat(),
                },
            )
        print(f"  OK {tracking}")
    except Exception as exc:
        errors += 1
        print(f"  ERROR envio {tracking}: {exc}")

print("\nMigrando reportes...")
valid_report_states = {"abierto", "en_proceso", "resuelto", "cerrado"}
for old in legacy_reports:
    marker = f"[LEGACY-REPORT-{old.get('id')}]"
    existing = supabase_get("reportes", {"descripcion": f"ilike.*{marker}*", "select": "id"})
    if existing:
        continue
    phone = str(old.get("phone_number") or "").strip() or "sin-telefono"
    tracking = str(old.get("tracking_code") or "").strip().upper()
    state = str(old.get("estado") or "abierto").lower()
    try:
        supabase_post(
            "reportes",
            {
                "cliente_id": phone_to_client.get(phone),
                "paquete_id": tracking_to_package.get(tracking),
                "telefono_contacto": phone,
                "descripcion": f"{marker} {old.get('descripcion') or ''}".strip(),
                "categoria": old.get("categoria"),
                "estado": state if state in valid_report_states else "abierto",
                "created_at": old.get("creado_en") or datetime.now(timezone.utc).isoformat(),
            },
        )
        print(f"  OK reporte {old.get('id')}")
    except Exception as exc:
        errors += 1
        print(f"  ERROR reporte {old.get('id')}: {exc}")

print("\nMigrando FAQ...")
for old in legacy_faq:
    question = str(old.get("pregunta") or "").strip()
    if not question:
        continue
    existing = supabase_get("faq", {"pregunta": f"eq.{question}", "select": "id"})
    if existing:
        continue
    try:
        supabase_post(
            "faq",
            {
                "pregunta": question,
                "respuesta": old.get("respuesta") or "",
                "categoria": old.get("categoria") or "general",
                "activo": True,
            },
        )
        print(f"  OK {question}")
    except Exception as exc:
        errors += 1
        print(f"  ERROR FAQ {question}: {exc}")

if errors:
    print(f"\nMigracion parcial: {errors} registro(s) requieren revision. Puedes corregirlos y repetir el script.")
    sys.exit(1)

print("\nMigracion completa. Las tablas *_legacy y envios se conservaron como respaldo.")
