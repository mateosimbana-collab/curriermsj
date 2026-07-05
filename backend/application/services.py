from typing import Any, Optional
from datetime import datetime, timedelta
from backend.domain.entities import Cliente, Paquete, TrackingEvent, Notificacion, Usuario, Prospecto
from backend.infrastructure.supabase_repository import SupabaseRepository


class ClienteService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def registrar_o_buscar(self, telefono: str, nombre: str, cedula: str) -> dict[str, Any]:
        existente = self.repo.buscar_cliente_por_telefono(telefono)
        if existente:
            return existente

        existente_cedula = self.repo.buscar_cliente_por_cedula(cedula)
        if existente_cedula:
            return existente_cedula

        data = {
            "cedula": cedula,
            "nombre_completo": nombre,
            "telefono": telefono,
        }
        return self.repo.crear_cliente(data)

    def listar(self, page: int = 1, per_page: int = 20, filtros: dict = None) -> dict[str, Any]:
        return self.repo.listar_clientes(page, per_page, filtros)


class PaqueteService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def crear(self, cliente_id: str, remitente: str, destinatario: str,
              contenido: str = "", peso: float = 0.0, destino: str = "") -> dict[str, Any]:
        data = {
            "cliente_id": cliente_id,
            "remitente_nombre": remitente,
            "destinatario_nombre": destinatario,
            "destinatario_direccion": destino,
            "contenido": contenido,
            "peso_kg": peso,
            "estado_actual": "recibido",
        }
        paquete = self.repo.crear_paquete(data)

        self.repo.actualizar_estado_paquete(
            paquete_id=paquete["id"],
            etiqueta="Recibido en USA",
            descripcion=f"Paquete registrado. Remitente: {remitente}",
            ubicacion="Bodega USA"
        )
        return paquete

    def actualizar_estado(self, paquete_id: str, etiqueta: str,
                          descripcion: str = "", ubicacion: str = "",
                          foto_url: str = "") -> Optional[dict[str, Any]]:
        return self.repo.actualizar_estado_paquete(
            paquete_id, etiqueta, descripcion, ubicacion, foto_url
        )

    def buscar_por_tracking(self, tracking: str) -> Optional[dict[str, Any]]:
        return self.repo.buscar_paquete_por_tracking(tracking)

    def listar(self, page: int = 1, per_page: int = 20, filtros: dict = None) -> dict[str, Any]:
        return self.repo.listar_paquetes(page, per_page, filtros)


class TrackingService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def obtener_historial(self, paquete_id: str) -> list[dict[str, Any]]:
        return self.repo.obtener_historial_tracking(paquete_id)


class NotificacionService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def enviar_notificacion_tracking(self, paquete_id: str, telefono: str,
                                     mensaje: str) -> Optional[dict[str, Any]]:
        data = {
            "paquete_id": paquete_id,
            "telefono_destino": telefono,
            "tipo": "tracking",
            "mensaje": mensaje,
        }
        return self.repo.registrar_notificacion(data)


class ProspectoService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def crear_desde_whatsapp(self, telefono: str, nombre: str = "") -> dict[str, Any]:
        existente = self.repo.listar_prospectos()
        for p in existente.get("data", []):
            if p["telefono"] == telefono:
                return p
        return self.repo.crear_prospecto(telefono, nombre)


class DashboardService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def obtener_stats(self) -> dict[str, Any]:
        return self.repo.get_dashboard_stats()


class ConfigService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def obtener(self, clave: str) -> Optional[str]:
        return self.repo.obtener_config(clave)

    def listar(self) -> list[dict[str, Any]]:
        return self.repo.listar_config()

    def actualizar(self, clave: str, valor: str) -> bool:
        return self.repo.actualizar_config(clave, valor)


class AuthService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo
        self._tokens: dict[str, dict[str, Any]] = {}

    def login(self, email: str, password: str) -> Optional[dict[str, Any]]:
        usuario = self.repo.buscar_usuario_por_email(email)
        if not usuario:
            return None
        from werkzeug.security import check_password_hash
        if not check_password_hash(usuario["password_hash"], password):
            return None
        return usuario

    def generar_token(self, usuario: dict[str, Any]) -> str:
        import jwt
        import os
        payload = {
            "sub": str(usuario["id"]),
            "email": usuario["email"],
            "rol": usuario["rol"],
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        secret = os.getenv("JWT_SECRET", "curriermsj-super-secret-key-change-in-prod")
        return jwt.encode(payload, secret, algorithm="HS256")
