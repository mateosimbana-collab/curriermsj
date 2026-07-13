import os
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


_repo_instance = None


def get_repo():
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = SupabaseRepository()
    return _repo_instance


class SupabaseRepository:
    """Repository unificado para operaciones con Supabase."""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY son requeridos")
        self.client: Client = create_client(url, key)

    @staticmethod
    def _search_term(value: Any) -> str:
        return re.sub(r"[^\w\s@+\-]", "", str(value), flags=re.UNICODE).strip()[:100]

    # ============================================
    # CLIENTES
    # ============================================

    def buscar_cliente_por_telefono(self, telefono: str) -> Optional[dict[str, Any]]:
        res = (
            self.client.table("clientes")
            .select("*")
            .eq("telefono", telefono)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def buscar_cliente_por_cedula(self, cedula: str) -> Optional[dict[str, Any]]:
        res = (
            self.client.table("clientes")
            .select("*")
            .eq("cedula", cedula)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def listar_clientes(self, page: int = 1, per_page: int = 15, filtros: dict = None) -> dict[str, Any]:
        query = self.client.table("clientes").select("*", count="exact").is_("deleted_at", "null")
        if filtros:
            if filtros.get("busqueda"):
                term = self._search_term(filtros["busqueda"])
                if term:
                    query = query.or_(
                        f"nombre_completo.ilike.%{term}%,"
                        f"cedula.ilike.%{term}%,"
                        f"telefono.ilike.%{term}%"
                    )
            if filtros.get("tipo_cliente"):
                query = query.eq("tipo_cliente", filtros["tipo_cliente"])
        query = query.order("created_at", desc=True).range((page - 1) * per_page, page * per_page - 1)
        res = query.execute()
        return {
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        }

    def crear_cliente(self, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        payload = {**data, "created_at": datetime.now(timezone.utc).isoformat()}
        res = self.client.table("clientes").insert(payload).execute()
        return res.data[0] if res.data else None

    def actualizar_cliente(self, cliente_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        payload = {**data, "updated_at": datetime.now(timezone.utc).isoformat()}
        res = (
            self.client.table("clientes")
            .update(payload)
            .eq("id", cliente_id)
            .execute()
        )
        return res.data[0] if res.data else None

    def eliminar_cliente(self, cliente_id: str) -> bool:
        res = (
            self.client.table("clientes")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", cliente_id)
            .execute()
        )
        return len(res.data) > 0

    # ============================================
    # PAQUETES
    # ============================================

    def buscar_paquete_por_tracking(self, tracking: str) -> Optional[dict[str, Any]]:
        res = (
            self.client.table("paquetes")
            .select("*, clientes!inner(*), tracking_events(*)")
            .eq("tracking_code", tracking)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def listar_paquetes(self, page: int = 1, per_page: int = 15, filtros: dict = None) -> dict[str, Any]:
        query = self.client.table("paquetes").select("*, clientes(nombre_completo, telefono, cedula)", count="exact").is_("deleted_at", "null")
        if filtros:
            if filtros.get("estado"):
                query = query.eq("estado_actual", filtros["estado"])
            if filtros.get("cliente_id"):
                query = query.eq("cliente_id", filtros["cliente_id"])
            if filtros.get("busqueda"):
                term = self._search_term(filtros["busqueda"])
                if term:
                    query = query.or_(
                        f"tracking_code.ilike.%{term}%,"
                        f"remitente_nombre.ilike.%{term}%,"
                        f"destinatario_nombre.ilike.%{term}%"
                    )
        query = query.order("created_at", desc=True).range((page - 1) * per_page, page * per_page - 1)
        res = query.execute()
        return {
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        }

    def crear_paquete(self, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        payload = {**data, "created_at": datetime.now(timezone.utc).isoformat()}
        res = self.client.table("paquetes").insert(payload).execute()
        return res.data[0] if res.data else None

    def actualizar_estado_paquete(self, paquete_id: str, etiqueta: str, descripcion: str = "",
                                  ubicacion: str = "", foto_url: str = "") -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        paquete_data = {
            "estado_actual": etiqueta.lower().replace(" ", "_"),
            "etiqueta_actual": etiqueta,
            "updated_at": now,
        }
        if etiqueta == "Entregado":
            paquete_data["fecha_entrega"] = now

        event_data = {
            "paquete_id": paquete_id,
            "etiqueta": etiqueta,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "foto_url": foto_url,
            "created_at": now,
        }

        res_paq = self.client.table("paquetes").update(paquete_data).eq("id", paquete_id).execute()
        if not res_paq.data:
            return None
        self.client.table("tracking_events").insert(event_data).execute()

        return res_paq.data[0]

    def obtener_historial_tracking(self, paquete_id: str) -> list[dict[str, Any]]:
        res = (
            self.client.table("tracking_events")
            .select("*")
            .eq("paquete_id", paquete_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data

    # ============================================
    # RECEPCIONES EN USA / CONSOLIDACION
    # ============================================

    def listar_recepciones(
        self,
        page: int = 1,
        per_page: int = 30,
        filtros: dict | None = None,
    ) -> dict[str, Any]:
        query = (
            self.client.table("recepciones_usa")
            .select(
                "*, clientes(nombre_completo, cedula, telefono, tipo_cliente, grupo_id, ciudad, direccion), "
                "paquetes(tracking_code, estado_actual, estado_pago)",
                count="exact",
            )
            .is_("deleted_at", "null")
        )
        if filtros:
            if filtros.get("estado"):
                query = query.eq("estado_operativo", filtros["estado"])
            if filtros.get("cliente_id"):
                query = query.eq("cliente_id", filtros["cliente_id"])
            if filtros.get("sin_despacho"):
                query = query.is_("despacho_id", "null")
            if filtros.get("busqueda"):
                term = self._search_term(filtros["busqueda"])
                if term:
                    query = query.or_(
                        f"tracking_externo.ilike.%{term}%,"
                        f"transportista.ilike.%{term}%,"
                        f"tienda.ilike.%{term}%"
                    )
        query = query.order("recibido_en", desc=True).range(
            (page - 1) * per_page,
            page * per_page - 1,
        )
        res = query.execute()
        return {
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        }

    def crear_recepcion(self, data: dict[str, Any], usuario_id: str = "") -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            **data,
            "tracking_externo": str(data["tracking_externo"]).strip().upper(),
            "created_at": now,
            "updated_at": now,
        }
        if usuario_id:
            payload["created_by"] = usuario_id
            payload["updated_by"] = usuario_id
        res = self.client.table("recepciones_usa").insert(payload).execute()
        return res.data[0] if res.data else None

    def actualizar_recepcion(
        self,
        recepcion_id: str,
        data: dict[str, Any],
        usuario_id: str = "",
    ) -> Optional[dict[str, Any]]:
        payload = {**data, "updated_at": datetime.now(timezone.utc).isoformat()}
        if "tracking_externo" in payload:
            payload["tracking_externo"] = str(payload["tracking_externo"]).strip().upper()
        if payload.get("estado_operativo") == "fotos_enviadas":
            payload["fotos_enviadas_en"] = datetime.now(timezone.utc).isoformat()
        if usuario_id:
            payload["updated_by"] = usuario_id
        res = (
            self.client.table("recepciones_usa")
            .update(payload)
            .eq("id", recepcion_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return res.data[0] if res.data else None

    def consolidar_recepciones(
        self,
        recepcion_ids: list[str],
        paquete_data: dict[str, Any],
        usuario_id: str = "",
    ) -> dict[str, Any]:
        ids = list(dict.fromkeys(recepcion_ids))
        if not ids:
            raise ValueError("Selecciona al menos una recepcion")

        selected = (
            self.client.table("recepciones_usa")
            .select("id, cliente_id, grupo_id, contenido, peso_kg, estado_operativo")
            .in_("id", ids)
            .is_("deleted_at", "null")
            .is_("despacho_id", "null")
            .execute()
        ).data
        if len(selected) != len(ids):
            raise ValueError("Una o mas recepciones ya fueron consolidadas o no existen")

        client_ids = {item["cliente_id"] for item in selected}
        if paquete_data.get("cliente_id") not in client_ids:
            raise ValueError("Las recepciones no pertenecen al cliente seleccionado")
        if any(item.get("estado_operativo") not in {"despachar", "armado"} for item in selected):
            raise ValueError("Solo puedes consolidar recepciones en estado despachar o armado")
        if len(client_ids) > 1:
            group_ids = {item.get("grupo_id") for item in selected}
            if None in group_ids or len(group_ids) != 1:
                raise ValueError("Solo puedes consolidar clientes distintos cuando pertenecen al mismo grupo")
            paquete_data["grupo_id"] = next(iter(group_ids))

        if not paquete_data.get("peso_kg"):
            paquete_data["peso_kg"] = round(
                sum(float(item.get("peso_kg") or 0) for item in selected),
                2,
            ) or None
        if not paquete_data.get("contenido"):
            contenidos = [str(item.get("contenido") or "").strip() for item in selected]
            paquete_data["contenido"] = ", ".join(value for value in contenidos if value)[:500]

        paquete = self.crear_paquete(paquete_data)
        if not paquete:
            raise ValueError("No se pudo crear el despacho")

        try:
            now = datetime.now(timezone.utc).isoformat()
            update_data = {
                "despacho_id": paquete["id"],
                "estado_operativo": "consolidado",
                "updated_at": now,
            }
            if usuario_id:
                update_data["updated_by"] = usuario_id
            linked = (
                self.client.table("recepciones_usa")
                .update(update_data)
                .in_("id", ids)
                .is_("despacho_id", "null")
                .execute()
            ).data
            if len(linked) != len(ids):
                raise ValueError("No se pudieron reservar todas las recepciones")
            self.actualizar_estado_paquete(
                paquete["id"],
                "Recibido en USA",
                "Despacho consolidado y guia generada",
            )
            return {"paquete": paquete, "recepciones": linked}
        except Exception:
            for previous_state in {item["estado_operativo"] for item in selected}:
                previous_ids = [item["id"] for item in selected if item["estado_operativo"] == previous_state]
                self.client.table("recepciones_usa").update({
                    "despacho_id": None,
                    "estado_operativo": previous_state,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).in_("id", previous_ids).eq("despacho_id", paquete["id"]).execute()
            self.client.table("paquetes").update({"deleted_at": datetime.now(timezone.utc).isoformat()}).eq(
                "id", paquete["id"]
            ).execute()
            raise

    # ============================================
    # COBROS
    # ============================================

    @staticmethod
    def _with_balance(paquete: dict[str, Any]) -> dict[str, Any]:
        total = float(paquete.get("valor_flete") or 0)
        verified = sum(
            float(pago.get("monto") or 0)
            for pago in paquete.get("pagos_paquete") or []
            if pago.get("estado") == "verificado"
        )
        paquete["total_pagado"] = round(verified, 2)
        paquete["saldo_pendiente"] = round(max(total - verified, 0), 2)
        return paquete

    def listar_cobros(self, estado: str = "") -> list[dict[str, Any]]:
        query = (
            self.client.table("paquetes")
            .select(
                "id, tracking_code, cliente_id, valor_flete, estado_pago, fecha_prometida, "
                "estado_actual, modalidad_entrega, categoria_importacion, created_at, "
                "clientes(nombre_completo, telefono, ciudad), "
                "pagos_paquete(id, monto, metodo, referencia, comprobante_url, estado, created_at)"
            )
            .is_("deleted_at", "null")
        )
        if estado:
            query = query.eq("estado_pago", estado)
        rows = query.order("created_at", desc=True).limit(200).execute().data
        return [self._with_balance(row) for row in rows]

    def registrar_pago(self, data: dict[str, Any], usuario_id: str = "") -> Optional[dict[str, Any]]:
        paquete_id = data["paquete_id"]
        paquete = (
            self.client.table("paquetes")
            .select("id, valor_flete, pagos_paquete(monto, estado)")
            .eq("id", paquete_id)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        if not paquete.data:
            raise ValueError("Despacho no encontrado")
        with_balance = self._with_balance(paquete.data[0])
        amount = float(data["monto"])
        if data.get("estado") == "verificado" and amount > with_balance["saldo_pendiente"] + 0.009:
            raise ValueError("El pago verificado supera el saldo pendiente")

        payload = {**data, "created_at": datetime.now(timezone.utc).isoformat()}
        if usuario_id:
            payload["registrado_por"] = usuario_id
            if payload.get("estado") == "verificado":
                payload["verificado_por"] = usuario_id
                payload["verificado_en"] = datetime.now(timezone.utc).isoformat()
        res = self.client.table("pagos_paquete").insert(payload).execute()
        return res.data[0] if res.data else None

    def actualizar_estado_pago(
        self,
        pago_id: str,
        estado: str,
        usuario_id: str,
    ) -> Optional[dict[str, Any]]:
        payment = (
            self.client.table("pagos_paquete")
            .select("id, paquete_id, monto, estado")
            .eq("id", pago_id)
            .limit(1)
            .execute()
        )
        if not payment.data:
            return None
        current = payment.data[0]
        if estado == "verificado":
            package = (
                self.client.table("paquetes")
                .select("valor_flete, pagos_paquete(id, monto, estado)")
                .eq("id", current["paquete_id"])
                .limit(1)
                .execute()
            )
            if not package.data:
                raise ValueError("Despacho no encontrado")
            target = float(package.data[0].get("valor_flete") or 0)
            verified = sum(
                float(item.get("monto") or 0)
                for item in package.data[0].get("pagos_paquete") or []
                if item.get("estado") == "verificado" and item.get("id") != pago_id
            )
            if verified + float(current["monto"]) > target + 0.009:
                raise ValueError("El pago verificado supera el saldo pendiente")

        payload: dict[str, Any] = {
            "estado": estado,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if estado == "verificado":
            payload["verificado_por"] = usuario_id
            payload["verificado_en"] = datetime.now(timezone.utc).isoformat()
        else:
            payload["verificado_por"] = None
            payload["verificado_en"] = None
        res = self.client.table("pagos_paquete").update(payload).eq("id", pago_id).execute()
        return res.data[0] if res.data else None

    def get_operational_summary(self, include_money: bool = False) -> dict[str, Any]:
        empty = {
            "available": True,
            "recepciones_por_estado": {},
            "por_procesar": 0,
            "esperando_cliente": 0,
            "por_despachar": 0,
            "cobros_pendientes": 0,
            "comprobantes_por_verificar": 0,
            "envios_atrasados": 0,
        }
        try:
            recepciones = (
                self.client.table("recepciones_usa")
                .select("estado_operativo")
                .is_("deleted_at", "null")
                .execute()
            ).data
            cobros = self.listar_cobros()
            payments = (
                self.client.table("pagos_paquete")
                .select("id", count="exact")
                .eq("estado", "pendiente")
                .execute()
            )
        except Exception as exc:
            logger.warning("Flujo operativo no disponible; aplica la migracion 005: %s", exc)
            return {**empty, "available": False}

        by_state: dict[str, int] = {}
        for row in recepciones:
            state = row.get("estado_operativo") or "por_procesar"
            by_state[state] = by_state.get(state, 0) + 1

        today = datetime.now(timezone(timedelta(hours=-5))).date()
        pending_rows = [row for row in cobros if row["saldo_pendiente"] > 0]
        delayed = [
            row
            for row in cobros
            if row.get("fecha_prometida")
            and date.fromisoformat(row["fecha_prometida"]) < today
            and row.get("estado_actual") != "entregado"
        ]
        summary = {
            **empty,
            "recepciones_por_estado": by_state,
            "por_procesar": by_state.get("por_procesar", 0),
            "esperando_cliente": by_state.get("esperando_decision", 0),
            "por_despachar": by_state.get("despachar", 0) + by_state.get("armado", 0),
            "cobros_pendientes": len(pending_rows),
            "comprobantes_por_verificar": payments.count if hasattr(payments, "count") else len(payments.data),
            "envios_atrasados": len(delayed),
        }
        if include_money:
            summary["cartera_pendiente"] = round(
                sum(row["saldo_pendiente"] for row in pending_rows),
                2,
            )
            summary["cobrado"] = round(sum(row["total_pagado"] for row in cobros), 2)
        return summary

    # ============================================
    # WHATSAPP / PROSPECTOS
    # ============================================

    def obtener_sesion(self, telefono: str) -> Optional[dict[str, Any]]:
        res = (
            self.client.table("sesiones_whatsapp")
            .select("*")
            .eq("telefono", telefono)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def guardar_sesion(self, telefono: str, paso: str, datos: dict = None) -> dict[str, Any]:
        existing = self.obtener_sesion(telefono)
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "paso_actual": paso,
            "datos_temp": datos or {},
            "updated_at": now,
        }
        if existing:
            self.client.table("sesiones_whatsapp").update(payload).eq("telefono", telefono).execute()
        else:
            payload["telefono"] = telefono
            payload["created_at"] = now
            self.client.table("sesiones_whatsapp").insert(payload).execute()
        return self.obtener_sesion(telefono)

    def crear_prospecto(self, telefono: str, nombre: str = "") -> Optional[dict[str, Any]]:
        data = {
            "telefono": telefono,
            "nombre": nombre,
            "origen": "whatsapp",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        res = self.client.table("prospectos").insert(data).execute()
        return res.data[0] if res.data else None

    def listar_prospectos(self, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        query = (
            self.client.table("prospectos")
            .select("*", count="exact")
            .eq("estado", "activo")
            .order("created_at", desc=True)
            .range((page - 1) * per_page, page * per_page - 1)
        )
        res = query.execute()
        return {
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        }

    # ============================================
    # ETIQUETAS / ESTADOS
    # ============================================

    def listar_etiquetas(self) -> list[dict[str, Any]]:
        res = (
            self.client.table("etiquetas_estado")
            .select("*")
            .is_("deleted_at", "null")
            .order("posicion")
            .execute()
        )
        return res.data

    # ============================================
    # NOTIFICACIONES
    # ============================================

    def registrar_notificacion(self, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        payload = {**data, "created_at": datetime.now(timezone.utc).isoformat()}
        res = self.client.table("notificaciones").insert(payload).execute()
        return res.data[0] if res.data else None

    def actualizar_estado_notificacion(self, notif_id: str, estado: str, msg_id: str = "", error: str = "") -> None:
        data = {"estado_envio": estado, "sent_at": datetime.now(timezone.utc).isoformat()}
        if msg_id:
            data["whatsapp_msg_id"] = msg_id
        if error:
            data["error_msg"] = error
        self.client.table("notificaciones").update(data).eq("id", notif_id).execute()

    # ============================================
    # DASHBOARD / ESTADISTICAS
    # ============================================

    def get_dashboard_stats(self) -> dict[str, Any]:
        try:
            rpc = self.client.rpc("dashboard_stats").execute()
            if isinstance(rpc.data, dict):
                return rpc.data
        except Exception as exc:
            logger.warning("dashboard_stats RPC no disponible, usando consultas compatibles: %s", exc)

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        estados_pendientes = ["recibido_en_usa", "en_transito", "en_aduana", "en_destino", "en_ruta_de_entrega"]

        def q1():
            return self.client.table("clientes").select("id", count="exact").is_("deleted_at", "null").execute()
        def q2():
            return self.client.table("paquetes").select("id", count="exact").is_("deleted_at", "null").execute()
        def q3():
            return self.client.table("paquetes").select("id", count="exact").gte("created_at", today_start).execute()
        def q4():
            return self.client.table("paquetes").select("id", count="exact").in_("estado_actual", estados_pendientes).execute()
        def q5():
            return self.client.table("paquetes").select("id", count="exact").eq("estado_actual", "entregado").execute()
        def q6():
            return self.client.table("prospectos").select("id", count="exact").eq("estado", "activo").execute()
        def q7():
            return self.client.table("paquetes").select("*, clientes(nombre_completo, telefono)").is_("deleted_at", "null").order("created_at", desc=True).limit(10).execute()
        def q8():
            try:
                return self.client.table("sesiones_whatsapp").select("telefono", count="exact").execute()
            except Exception:
                return None
        def q9():
            try:
                return self.client.rpc("paquetes_por_estado").execute()
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=5) as pool:
            f1 = pool.submit(q1)
            f2 = pool.submit(q2)
            f3 = pool.submit(q3)
            f4 = pool.submit(q4)
            f5 = pool.submit(q5)
            f6 = pool.submit(q6)
            f7 = pool.submit(q7)
            f8 = pool.submit(q8)
            f9 = pool.submit(q9)

        def _count(res):
            return res.count if hasattr(res, "count") else len(res.data) if hasattr(res, "data") else 0

        return {
            "total_clientes": _count(f1.result()),
            "total_paquetes": _count(f2.result()),
            "paquetes_hoy": _count(f3.result()),
            "paquetes_pendientes": _count(f4.result()),
            "paquetes_entregados": _count(f5.result()),
            "total_prospectos": _count(f6.result()),
            "sesiones_activas": _count(f8.result()) if f8.result() else 0,
            "ultimos_paquetes": f7.result().data if hasattr(f7.result(), "data") else [],
            "paquetes_por_estado": f9.result().data if f9.result() and hasattr(f9.result(), "data") else [],
        }

    # ============================================
    # CONFIGURACION
    # ============================================

    def obtener_config(self, clave: str) -> Optional[str]:
        res = self.client.table("configuracion").select("valor").eq("clave", clave).limit(1).execute()
        return res.data[0]["valor"] if res.data else None

    def listar_config(self) -> list[dict[str, Any]]:
        res = self.client.table("configuracion").select("*").order("clave").execute()
        return res.data

    def actualizar_config(self, clave: str, valor: str) -> bool:
        res = self.client.table("configuracion").update({
            "valor": valor,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("clave", clave).execute()
        return len(res.data) > 0

    # ============================================
    # USUARIOS (backend auth)
    # ============================================

    def buscar_usuario_por_email(self, email: str) -> Optional[dict[str, Any]]:
        res = self.client.table("usuarios").select("*").eq("email", email).is_("deleted_at", "null").limit(1).execute()
        return res.data[0] if res.data else None

    def listar_usuarios(self) -> list[dict[str, Any]]:
        res = self.client.table("usuarios").select("id, email, nombre, telefono, rol, activo, ultimo_acceso, created_at").is_("deleted_at", "null").order("created_at").execute()
        return res.data

    # ============================================
    # REPORTES / AUDITORIA
    # ============================================

    def generar_reporte_paquetes(self, fecha_desde: str, fecha_hasta: str) -> list[dict[str, Any]]:
        res = self.client.table("paquetes").select(
            "tracking_code, estado_actual, cliente_id, remitente_nombre, remitente_pais, peso_kg, valor_declarado, fecha_recepcion, fecha_entrega"
        ).gte("created_at", fecha_desde).lte("created_at", fecha_hasta).execute()
        return res.data

    def generar_reporte_clientes(self) -> list[dict[str, Any]]:
        res = self.client.table("clientes").select("cedula, nombre_completo, telefono, tipo_cliente, ciudad, created_at").is_("deleted_at", "null").execute()
        return res.data

    def listar_audit_logs(self, page: int = 1, per_page: int = 30, tabla: str = "") -> dict[str, Any]:
        query = self.client.table("audit_log").select("*", count="exact").order("created_at", desc=True).range((page - 1) * per_page, page * per_page - 1)
        if tabla:
            query = query.eq("tabla", tabla)
        res = query.execute()
        return {
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        }
