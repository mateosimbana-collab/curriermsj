import json
import logging
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote

import httpx

import config
from domain.constants import Step


logger = logging.getLogger(__name__)


class SupabaseRepository:
    def __init__(
        self,
        supabase_url: str = config.SUPABASE_URL,
        supabase_key: str = config.SUPABASE_KEY,
    ) -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.table_envios = config.SUPABASE_TABLE_ENVIOS
        self.table_estado = config.SUPABASE_TABLE_ESTADO
        self.table_faq = config.SUPABASE_TABLE_FAQ
        self.table_reportes = config.SUPABASE_TABLE_REPORTES

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def get_user_state(self, phone_number: str) -> Optional[dict[str, Any]]:
        url = f"{self._table(self.table_estado)}?phone_number=eq.{quote(phone_number)}&limit=1"
        data = self._request("GET", url)
        return data[0] if data else None

    def create_user_state(
        self,
        phone_number: str,
        step: str = Step.MENU,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload = {
            "phone_number": phone_number,
            "paso_actual": step,
            "datos_temp": data or {},
            "updated_at": datetime.utcnow().isoformat(),
        }
        response = self._request("POST", self._table(self.table_estado), json=payload)
        return response[0] if response else {}

    def update_user_state(
        self,
        phone_number: str,
        step: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        payload: dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
        if step is not None:
            payload["paso_actual"] = step
        if data is not None:
            payload["datos_temp"] = data

        url = f"{self._table(self.table_estado)}?phone_number=eq.{quote(phone_number)}"
        self._request("PATCH", url, json=payload)

    def reset_user_state(self, phone_number: str) -> None:
        self.update_user_state(phone_number, Step.MENU, {})

    def get_temp_data(self, phone_number: str) -> dict[str, Any]:
        state = self.get_user_state(phone_number)
        return self.extract_temp_data(state)

    def save_temp_data(self, phone_number: str, data: dict[str, Any]) -> None:
        self.update_user_state(phone_number, data=data)

    def search_faq(self, question: str) -> Optional[str]:
        raw = (question or "").strip()
        if not raw:
            return None

        query = quote(raw, safe="")
        url = (
            f"{self._table(self.table_faq)}"
            f"?select=respuesta&pregunta=ilike.%25{query}%25&limit=1"
        )
        data = self._request("GET", url)
        return data[0]["respuesta"] if data else None

    def save_report(
        self,
        phone_number: str,
        description: str,
        category: Optional[str] = None,
        tracking_code: Optional[str] = None,
    ) -> int:
        payload = {
            "phone_number": phone_number,
            "descripcion": description,
            "categoria": category,
            "tracking_code": tracking_code,
            "estado": "abierto",
            "agente_asignado": "Equipo soporte",
            "creado_en": datetime.utcnow().isoformat(),
        }
        data = self._request("POST", self._table(self.table_reportes), json=payload)
        item = data[0] if isinstance(data, list) else data
        return int(item["id"])

    def save_shipment(self, shipment_data: dict[str, Any]) -> int:
        payload = dict(shipment_data)
        payload["creado_en"] = datetime.utcnow().isoformat()
        data = self._request("POST", self._table(self.table_envios), json=payload)
        item = data[0] if isinstance(data, list) else data
        return int(item["id"])

    def get_shipments_by_phone(self, phone_number: str, limit: int = 10) -> list[dict[str, Any]]:
        columns = ",".join(
            [
                "id",
                "tracking_code",
                "remitente",
                "destinatario",
                "direccion_destino",
                "tipo_paquete",
                "peso",
                "estado",
                "servicio_envio",
                "valor_cotizado",
                "entrega_estimada",
                "imagen_url",
                "creado_en",
            ]
        )
        url = (
            f"{self._table(self.table_envios)}?select={columns}"
            f"&telefono_remitente=eq.{quote(phone_number)}"
            f"&order=creado_en.desc&limit={limit}"
        )
        return self._request("GET", url)

    def get_shipment_by_id(self, shipment_id: int) -> Optional[dict[str, Any]]:
        url = f"{self._table(self.table_envios)}?select=*&id=eq.{shipment_id}&limit=1"
        data = self._request("GET", url)
        return data[0] if data else None

    def get_shipment_by_tracking(self, tracking_code: str) -> Optional[dict[str, Any]]:
        tracking = tracking_code.strip().upper().replace("#", "")
        url = (
            f"{self._table(self.table_envios)}?select=*"
            f"&tracking_code=eq.{quote(tracking)}&limit=1"
        )
        data = self._request("GET", url)
        if data:
            return data[0]

        if tracking.startswith("CUR-"):
            try:
                return self.get_shipment_by_id(int(tracking.replace("CUR-", "")))
            except ValueError:
                return None
        if tracking.isdigit():
            return self.get_shipment_by_id(int(tracking))
        return None

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

    def _table(self, table_name: str) -> str:
        return f"{self.supabase_url}/rest/v1/{table_name}"

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("Supabase no configurado: faltan SUPABASE_URL o SUPABASE_KEY")

        with httpx.Client(timeout=10) as client:
            response = client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            if not response.content:
                return []
            return response.json()
