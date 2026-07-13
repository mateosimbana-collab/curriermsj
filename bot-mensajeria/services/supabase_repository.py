# ruff: noqa: E402
"""
Compatibility layer that unifies the bot's repository with the backend repo.
Extends backend's SupabaseRepository, adding bot-specific methods
(FAQ, reports, old session management) while delegating shared logic.
"""
import json
import logging
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote

import httpx

import config
from domain.constants import Step

# Import the backend package once, using the same module path as the API.
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from backend.infrastructure.supabase_repository import SupabaseRepository as BackendRepo

logger = logging.getLogger(__name__)

BUSINESS_TZ = timezone(timedelta(hours=-5))


class SupabaseRepository(BackendRepo):
    """Bot repository that extends the backend repo with bot-specific methods."""

    def __init__(self):
        # Initialize parent with env vars from bot config
        import config as bot_config
        os.environ.setdefault("SUPABASE_URL", bot_config.SUPABASE_URL)
        os.environ.setdefault("SUPABASE_KEY", bot_config.SUPABASE_KEY)
        super().__init__()
        self.supabase_url = os.environ["SUPABASE_URL"]
        self.supabase_key = os.environ["SUPABASE_KEY"]
        self.table_envios = config.SUPABASE_TABLE_ENVIOS
        self.table_estado = config.SUPABASE_TABLE_ESTADO
        self.table_faq = config.SUPABASE_TABLE_FAQ
        self.table_reportes = config.SUPABASE_TABLE_REPORTES
        self.table_clientes = config.SUPABASE_TABLE_CLIENTES
        self._unified_schema: Optional[bool] = None

    def uses_unified_schema(self) -> bool:
        if self._unified_schema is None:
            try:
                self.client.table("paquetes").select("id").limit(1).execute()
                self._unified_schema = True
            except Exception:
                self._unified_schema = False
                logger.info("Esquema historico detectado; usando tablas envios y estado_usuario")
        return self._unified_schema

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # --- Bot-specific methods using old tables ---

    def get_client(self, phone_number: str) -> Optional[dict[str, Any]]:
        if self.uses_unified_schema():
            return self.buscar_cliente_por_telefono(phone_number)
        phone = quote(phone_number, safe="")
        rows = self._request(
            "GET",
            f"{self._table_url(self.table_clientes)}?phone_number=eq.{phone}&limit=1",
        )
        return rows[0] if rows else None

    def save_client(self, phone_number: str, nombre: str, apellido: str = "", ciudad: str = "", telefono_contacto: str = "") -> dict[str, Any]:
        if not self.uses_unified_schema():
            payload = {
                "phone_number": phone_number,
                "nombre": nombre,
                "apellido": apellido,
                "ciudad": ciudad,
                "telefono_contacto": telefono_contacto or phone_number,
                "registrado_en": datetime.now(timezone.utc).isoformat(),
            }
            existing = self.get_client(phone_number)
            if existing:
                rows = self._request(
                    "PATCH",
                    f"{self._table_url(self.table_clientes)}?phone_number=eq.{quote(phone_number, safe='')}",
                    json=payload,
                )
            else:
                rows = self._request("POST", self._table_url(self.table_clientes), json=payload)
            item = rows[0] if isinstance(rows, list) and rows else rows
            return item or payload

        data = {
            "cedula": f"WA-{phone_number}",
            "telefono": phone_number,
            "telefono_alternativo": telefono_contacto or None,
            "nombre_completo": f"{nombre} {apellido}".strip(),
            "ciudad": ciudad,
            "tipo_cliente": "regular",
        }
        data = {key: value for key, value in data.items() if value is not None}
        existing = self.buscar_cliente_por_telefono(phone_number)
        if existing:
            self.actualizar_cliente(existing["id"], data)
            client = self.buscar_cliente_por_telefono(phone_number) or {}
        else:
            client = self.crear_cliente(data) or {}
        if client.get("id"):
            self.client.table("sesiones_whatsapp").update({"cliente_id": client["id"]}).eq("telefono", phone_number).execute()
        return client

    def get_user_state(self, phone_number: str) -> Optional[dict[str, Any]]:
        if self.uses_unified_schema():
            return self.obtener_sesion(phone_number)
        phone = quote(phone_number, safe="")
        rows = self._request(
            "GET",
            f"{self._table_url(self.table_estado)}?phone_number=eq.{phone}&limit=1",
        )
        return rows[0] if rows else None

    def create_user_state(self, phone_number: str, step: str = Step.MENU, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if not self.uses_unified_schema():
            existing = self.get_user_state(phone_number)
            if existing:
                return existing
            payload = {
                "phone_number": phone_number,
                "paso_actual": step,
                "datos_temp": data or {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            rows = self._request("POST", self._table_url(self.table_estado), json=payload)
            item = rows[0] if isinstance(rows, list) and rows else rows
            return item or payload

        existing = self.obtener_sesion(phone_number)
        if existing:
            return existing
        self.guardar_sesion(phone_number, step, data or {})
        return self.obtener_sesion(phone_number) or {}

    def update_user_state(self, phone_number: str, step: Optional[str] = None, data: Optional[dict[str, Any]] = None) -> None:
        if not self.uses_unified_schema():
            payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if step is not None:
                payload["paso_actual"] = step
            if data is not None:
                payload["datos_temp"] = data
            current = self.get_user_state(phone_number)
            if current:
                self._request(
                    "PATCH",
                    f"{self._table_url(self.table_estado)}?phone_number=eq.{quote(phone_number, safe='')}",
                    json=payload,
                )
            else:
                self.create_user_state(phone_number, step or Step.MENU, data)
            return

        current = self.obtener_sesion(phone_number)
        if not current:
            self.guardar_sesion(phone_number, step or Step.MENU, data)
            return
        payload = {}
        if step is not None:
            payload["paso_actual"] = step
        if data is not None:
            payload["datos_temp"] = data
        if payload:
            self.client.table("sesiones_whatsapp").update(payload).eq("telefono", phone_number).execute()

    def reset_user_state(self, phone_number: str) -> None:
        self.update_user_state(phone_number, Step.MENU, {})

    def get_temp_data(self, phone_number: str) -> dict[str, Any]:
        state = self.get_user_state(phone_number)
        return self.extract_temp_data(state)

    def save_temp_data(self, phone_number: str, data: dict[str, Any]) -> None:
        self.update_user_state(phone_number, data=data)

    def search_faq(self, question: str) -> Optional[str]:
        """Search FAQ entries from the unified schema."""
        raw = (question or "").strip()
        if not raw:
            return None
        try:
            query = quote(raw, safe="")
            url = (
                f"{self._table_url(self.table_faq)}"
                f"?select=respuesta&pregunta=ilike.%25{query}%25&limit=1"
            )
            result = self._request("GET", url)
            return result[0]["respuesta"] if result else None
        except Exception as exc:
            logger.warning("No se pudo consultar FAQ: %s", exc)
            return None

    def save_report(self, phone_number: str, description: str, category: Optional[str] = None, tracking_code: Optional[str] = None) -> int:
        if not self.uses_unified_schema():
            payload = {
                "phone_number": phone_number,
                "tracking_code": tracking_code,
                "categoria": category,
                "descripcion": description,
                "estado": "abierto",
                "agente_asignado": "Equipo soporte",
                "creado_en": datetime.now(timezone.utc).isoformat(),
            }
            try:
                data = self._request("POST", self._table_url(self.table_reportes), json=payload)
                item = data[0] if isinstance(data, list) else data
                return int(item["id"])
            except Exception as exc:
                logger.error("No se pudo crear el reporte historico: %s", exc)
                return 0

        client = self.buscar_cliente_por_telefono(phone_number)
        package = self.buscar_paquete_por_tracking(tracking_code) if tracking_code else None
        payload = {
            "cliente_id": client.get("id") if client else None,
            "paquete_id": package.get("id") if package else None,
            "telefono_contacto": phone_number,
            "descripcion": description,
            "categoria": category,
            "estado": "abierto",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            data = self._request("POST", self._table_url(self.table_reportes), json=payload)
            item = data[0] if isinstance(data, list) else data
            return int(item["id"])
        except Exception as exc:
            logger.error("No se pudo crear el reporte: %s", exc)
            return 0

    def save_shipment(self, shipment_data: dict[str, Any]) -> str:
        data = dict(shipment_data)
        now = datetime.now(timezone.utc).isoformat()
        if not self.uses_unified_schema():
            legacy = {
                "estado": "pendiente",
                "remitente": data.get("remitente_nombre") or data.get("remitente", ""),
                "telefono_remitente": data.get("remitente_telefono") or data.get("telefono_remitente", ""),
                "destinatario": data.get("destinatario_nombre") or data.get("destinatario", ""),
                "telefono_destinatario": data.get("destinatario_telefono") or data.get("telefono_destinatario", ""),
                "direccion_origen": "Bodega USA",
                "direccion_destino": data.get("destinatario_direccion") or data.get("direccion_destino", ""),
                "tipo_paquete": data.get("contenido") or data.get("tipo_paquete", ""),
                "peso": data.get("peso_kg") if data.get("peso_kg") is not None else data.get("peso"),
                "instrucciones": data.get("instrucciones"),
                "phone_number": data.get("remitente_telefono") or data.get("telefono_remitente", ""),
                "creado_en": now,
            }
            rows = self._request("POST", self._table_url(self.table_envios), json=legacy)
            item = rows[0] if isinstance(rows, list) and rows else rows
            if not item:
                return ""
            tracking = item.get("tracking_code")
            if not tracking and item.get("id"):
                tracking = f"CUR-{int(item['id']):05d}"
                self._request(
                    "PATCH",
                    f"{self._table_url(self.table_envios)}?id=eq.{item['id']}",
                    json={"tracking_code": tracking},
                )
            return tracking or ""

        data["created_at"] = now
        mapped = {
            "cliente_id": data.get("cliente_id"),
            "remitente_nombre": data.get("remitente_nombre") or data.get("remitente", ""),
            "remitente_telefono": data.get("remitente_telefono") or data.get("telefono_remitente", ""),
            "remitente_pais": data.get("remitente_pais") or data.get("pais_origen", "Estados Unidos"),
            "destinatario_nombre": data.get("destinatario_nombre") or data.get("destinatario", ""),
            "destinatario_telefono": data.get("destinatario_telefono") or data.get("telefono_destinatario", ""),
            "destinatario_direccion": data.get("destinatario_direccion") or data.get("direccion_destino") or "",
            "contenido": data.get("contenido") or data.get("tipo_paquete", ""),
            "peso_kg": data.get("peso_kg") if data.get("peso_kg") is not None else data.get("peso"),
            "notas_internas": data.get("instrucciones"),
            "estado_actual": data.get("estado_actual") or data.get("estado", "recibido"),
            "created_at": data["created_at"],
        }
        mapped = {k: v for k, v in mapped.items() if v is not None}
        if not mapped.get("cliente_id"):
            client = self.buscar_cliente_por_telefono(mapped.get("remitente_telefono", ""))
            if client:
                mapped["cliente_id"] = client["id"]
        if not mapped.get("cliente_id"):
            logger.error("No se puede crear un paquete sin cliente asociado")
            return ""
        res = self.client.table("paquetes").insert(mapped).execute()
        if not res.data:
            return ""
        # DB trigger auto-generates tracking_code; fetch it back
        inserted_id = res.data[0]["id"]
        fetch = self.client.table("paquetes").select("tracking_code").eq("id", inserted_id).limit(1).execute()
        return fetch.data[0]["tracking_code"] if fetch.data else ""

    def get_shipments_by_phone(self, phone_number: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.uses_unified_schema():
            return self._request(
                "GET",
                f"{self._table_url(self.table_envios)}?phone_number=eq.{quote(phone_number, safe='')}"
                f"&order=creado_en.desc&limit={max(1, min(limit, 100))}",
            )
        client = self.buscar_cliente_por_telefono(phone_number)
        if not client:
            return []
        res = (
            self.client.table("paquetes")
            .select("*")
            .eq("cliente_id", client["id"])
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data

    def get_shipment_by_id(self, shipment_id: str) -> Optional[dict[str, Any]]:
        if not self.uses_unified_schema():
            rows = self._request(
                "GET",
                f"{self._table_url(self.table_envios)}?id=eq.{quote(str(shipment_id), safe='')}&limit=1",
            )
            return rows[0] if rows else None
        res = (
            self.client.table("paquetes")
            .select("*")
            .eq("id", shipment_id)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_shipment_by_tracking(self, tracking_code: str) -> Optional[dict[str, Any]]:
        tracking = tracking_code.strip().upper().replace("#", "")
        if not self.uses_unified_schema():
            rows = self._request(
                "GET",
                f"{self._table_url(self.table_envios)}?tracking_code=eq.{quote(tracking, safe='')}&limit=1",
            )
            return rows[0] if rows else None
        return self.buscar_paquete_por_tracking(tracking)

    def get_dashboard_stats(self) -> dict[str, Any]:
        if not self.uses_unified_schema():
            shipments = self._request(
                "GET",
                f"{self._table_url(self.table_envios)}?select=*&order=creado_en.desc",
            )
            clients = self._request(
                "GET",
                f"{self._table_url(self.table_clientes)}?select=phone_number",
            )
            reports = self._request(
                "GET",
                f"{self._table_url(self.table_reportes)}?select=*&order=creado_en.desc",
            )
            sessions = self._request(
                "GET",
                f"{self._table_url(self.table_estado)}?select=*&order=updated_at.desc",
            )
            now = datetime.now(BUSINESS_TZ)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            active_cutoff = now - timedelta(hours=24)

            def parse_timestamp(value: Any) -> Optional[datetime]:
                if not value:
                    return None
                try:
                    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed.astimezone(BUSINESS_TZ)
                except (TypeError, ValueError):
                    return None

            shipments_today = sum(
                1
                for item in shipments
                if (created := parse_timestamp(item.get("creado_en"))) and created >= today_start
            )
            active_sessions = [
                item
                for item in sessions
                if (updated := parse_timestamp(item.get("updated_at"))) and updated >= active_cutoff
            ]
            daily = []
            for offset in range(13, -1, -1):
                day = (today_start - timedelta(days=offset)).date()
                count = sum(
                    1
                    for item in shipments
                    if (created := parse_timestamp(item.get("creado_en"))) and created.date() == day
                )
                daily.append({"date": day.isoformat(), "count": count})

            open_reports = sum(
                1 for item in reports if item.get("estado") in {None, "abierto", "en_proceso"}
            )
            return {
                "total_clientes": len(clients),
                "total_paquetes": len(shipments),
                "paquetes_hoy": shipments_today,
                "paquetes_pendientes": sum(
                    1 for item in shipments if item.get("estado") != "entregado"
                ),
                "paquetes_entregados": sum(
                    1 for item in shipments if item.get("estado") == "entregado"
                ),
                "total_shipments": len(shipments),
                "shipments_today": shipments_today,
                "active_users": len(active_sessions),
                "total_reports": len(reports),
                "open_reports": open_reports,
                "recent_shipments": shipments[:10],
                "active_sessions": active_sessions[:20],
                "shipments_by_day": daily,
            }

        stats = super().get_dashboard_stats()
        return {
            **stats,
            "total_shipments": stats.get("total_paquetes", 0),
            "shipments_today": stats.get("paquetes_hoy", 0),
            "active_users": stats.get("sesiones_activas", 0),
            "total_reports": stats.get("total_reportes", 0),
            "open_reports": stats.get("reportes_abiertos", 0),
            "recent_shipments": stats.get("ultimos_paquetes", []),
            "active_sessions": stats.get("sesiones", []),
            "shipments_by_day": stats.get("paquetes_por_dia", []),
        }

    def extract_temp_data(self, state: Optional[dict[str, Any]]) -> dict[str, Any]:
        if not state or not state.get("datos_temp"):
            return {}
        raw = state["datos_temp"]
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("datos_temp no es JSON valido: %s", raw)
                return {}
        if isinstance(raw, dict):
            return raw
        return {}

    def _table_url(self, table_name: str) -> str:
        return f"{self.supabase_url}/rest/v1/{table_name}"

    def _table(self, table_name: str) -> str:
        return self._table_url(table_name)

    def _request(self, method: str, url: str, headers: Optional[dict[str, str]] = None, **kwargs: Any) -> Any:
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("Supabase no configurado")
        request_headers = self.headers
        if headers:
            request_headers = {**self.headers, **headers}
        with httpx.Client(timeout=10) as client:
            response = client.request(method, url, headers=request_headers, **kwargs)
            response.raise_for_status()
            if not response.content:
                return []
            return response.json()
