import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


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

    def listar_clientes(self, page: int = 1, per_page: int = 20, filtros: dict = None) -> dict[str, Any]:
        query = self.client.table("clientes").select("*", count="exact").is_("deleted_at", "null")
        if filtros:
            if filtros.get("busqueda"):
                query = query.or_(
                    f"nombre_completo.ilike.%{filtros['busqueda']}%,"
                    f"cedula.ilike.%{filtros['busqueda']}%,"
                    f"telefono.ilike.%{filtros['busqueda']}%"
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
        data["created_at"] = datetime.utcnow().isoformat()
        res = self.client.table("clientes").insert(data).execute()
        return res.data[0] if res.data else None

    def actualizar_cliente(self, cliente_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        data["updated_at"] = datetime.utcnow().isoformat()
        res = (
            self.client.table("clientes")
            .update(data)
            .eq("id", cliente_id)
            .execute()
        )
        return res.data[0] if res.data else None

    def eliminar_cliente(self, cliente_id: str) -> bool:
        res = (
            self.client.table("clientes")
            .update({"deleted_at": datetime.utcnow().isoformat()})
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

    def listar_paquetes(self, page: int = 1, per_page: int = 20, filtros: dict = None) -> dict[str, Any]:
        query = self.client.table("paquetes").select("*, clientes(nombre_completo, telefono, cedula)", count="exact").is_("deleted_at", "null")
        if filtros:
            if filtros.get("estado"):
                query = query.eq("estado_actual", filtros["estado"])
            if filtros.get("cliente_id"):
                query = query.eq("cliente_id", filtros["cliente_id"])
            if filtros.get("busqueda"):
                query = query.or_(
                    f"tracking_code.ilike.%{filtros['busqueda']}%,"
                    f"remitente_nombre.ilike.%{filtros['busqueda']}%,"
                    f"destinatario_nombre.ilike.%{filtros['busqueda']}%"
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
        data["created_at"] = datetime.utcnow().isoformat()
        res = self.client.table("paquetes").insert(data).execute()
        return res.data[0] if res.data else None

    def actualizar_estado_paquete(self, paquete_id: str, etiqueta: str, descripcion: str = "",
                                  ubicacion: str = "", foto_url: str = "") -> Optional[dict[str, Any]]:
        now = datetime.utcnow().isoformat()
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
        self.client.table("tracking_events").insert(event_data).execute()

        return res_paq.data[0] if res_paq.data else None

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
        now = datetime.utcnow().isoformat()
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
            "created_at": datetime.utcnow().isoformat(),
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
        data["created_at"] = datetime.utcnow().isoformat()
        res = self.client.table("notificaciones").insert(data).execute()
        return res.data[0] if res.data else None

    def actualizar_estado_notificacion(self, notif_id: str, estado: str, msg_id: str = "", error: str = "") -> None:
        data = {"estado_envio": estado, "sent_at": datetime.utcnow().isoformat()}
        if msg_id:
            data["whatsapp_msg_id"] = msg_id
        if error:
            data["error_msg"] = error
        self.client.table("notificaciones").update(data).eq("id", notif_id).execute()

    # ============================================
    # DASHBOARD / ESTADISTICAS
    # ============================================

    def get_dashboard_stats(self) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        total_clientes = self.client.table("clientes").select("id", count="exact").is_("deleted_at", "null").execute()
        total_paquetes = self.client.table("paquetes").select("id", count="exact").is_("deleted_at", "null").execute()
        paquetes_hoy = self.client.table("paquetes").select("id", count="exact").gte("created_at", today_start).execute()
        paquetes_pendientes = self.client.table("paquetes").select("id", count="exact").in_("estado_actual", ["recibido", "en_transito"]).execute()
        paquetes_entregados = self.client.table("paquetes").select("id", count="exact").eq("estado_actual", "entregado").execute()
        total_prospectos = self.client.table("prospectos").select("id", count="exact").eq("estado", "activo").execute()

        res_upto = self.client.table("paquetes").select("*, clientes(nombre_completo, telefono)").is_("deleted_at", "null").order("created_at", desc=True).limit(10).execute()

        res_by_estado = self.client.rpc("paquetes_por_estado").execute()

        try:
            res_sesiones = self.client.table("sesiones_whatsapp").select("telefono", count="exact").execute()
            sesiones_activas = res_sesiones.count if hasattr(res_sesiones, "count") else len(res_sesiones.data)
        except Exception:
            sesiones_activas = 0

        return {
            "total_clientes": total_clientes.count if hasattr(total_clientes, "count") else len(total_clientes.data),
            "total_paquetes": total_paquetes.count if hasattr(total_paquetes, "count") else len(total_paquetes.data),
            "paquetes_hoy": paquetes_hoy.count if hasattr(paquetes_hoy, "count") else len(paquetes_hoy.data),
            "paquetes_pendientes": paquetes_pendientes.count if hasattr(paquetes_pendientes, "count") else len(paquetes_pendientes.data),
            "paquetes_entregados": paquetes_entregados.count if hasattr(paquetes_entregados, "count") else len(paquetes_entregados.data),
            "total_prospectos": total_prospectos.count if hasattr(total_prospectos, "count") else len(total_prospectos.data),
            "sesiones_activas": sesiones_activas,
            "ultimos_paquetes": res_upto.data,
            "paquetes_por_estado": res_by_estado.data if hasattr(res_by_estado, "data") else [],
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
            "updated_at": datetime.utcnow().isoformat()
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
    # REPORTES
    # ============================================

    def generar_reporte_paquetes(self, fecha_desde: str, fecha_hasta: str) -> list[dict[str, Any]]:
        res = self.client.table("paquetes").select(
            "tracking_code, estado_actual, cliente_id, remitente_nombre, remitente_pais, peso_kg, valor_declarado, fecha_recepcion, fecha_entrega"
        ).gte("created_at", fecha_desde).lte("created_at", fecha_hasta).execute()
        return res.data

    def generar_reporte_clientes(self) -> list[dict[str, Any]]:
        res = self.client.table("clientes").select("cedula, nombre_completo, telefono, tipo_cliente, ciudad, created_at").is_("deleted_at", "null").execute()
        return res.data
