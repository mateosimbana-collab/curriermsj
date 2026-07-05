from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4


@dataclass
class Usuario:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    nombre: str = ""
    telefono: str = ""
    rol: str = "agente"
    activo: bool = True
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    def is_admin(self) -> bool:
        return self.rol == "admin"

    def can(self, permiso: str) -> bool:
        permisos: dict[str, list[str]] = {
            "admin": ["*"],
            "supervisor": ["clientes.*", "paquetes.*", "reportes.*", "tracking.*"],
            "agente": ["clientes.read", "paquetes.*", "tracking.*"],
            "soporte": ["clientes.read", "paquetes.read", "tracking.read"],
        }
        roles = permisos.get(self.rol, [])
        return "*" in roles or permiso in roles


@dataclass
class Cliente:
    id: UUID = field(default_factory=uuid4)
    cedula: str = ""
    nombre_completo: str = ""
    telefono: str = ""
    telefono_alternativo: str = ""
    email: str = ""
    direccion: str = ""
    ciudad: str = "Guayaquil"
    pais: str = "Ecuador"
    tipo_cliente: str = "regular"
    grupo_id: Optional[UUID] = None
    notas: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    @property
    def identificacion(self) -> str:
        return f"{self.nombre_completo} - {self.cedula}"


@dataclass
class Paquete:
    id: UUID = field(default_factory=uuid4)
    tracking_code: str = ""
    cliente_id: UUID = field(default_factory=uuid4)
    remitente_nombre: str = ""
    remitente_direccion: str = ""
    remitente_pais: str = "Estados Unidos"
    destinatario_nombre: str = ""
    destinatario_telefono: str = ""
    destinatario_direccion: str = ""
    destinatario_ciudad: str = ""
    tipo_paquete: str = ""
    peso_kg: float = 0.0
    contenido: str = ""
    valor_declarado: float = 0.0
    valor_flete: float = 0.0
    servicio_envio: str = ""
    estado_actual: str = "recibido"
    etiqueta_actual: str = ""
    fecha_recepcion: datetime = field(default_factory=datetime.utcnow)
    fecha_despacho: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    imagen_url: str = ""
    notas_internas: str = ""
    requiere_aprobacion: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None


@dataclass
class TrackingEvent:
    id: UUID = field(default_factory=uuid4)
    paquete_id: UUID = field(default_factory=uuid4)
    etiqueta: str = ""
    descripcion: str = ""
    ubicacion: str = ""
    foto_url: str = ""
    es_automatico: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Notificacion:
    id: UUID = field(default_factory=uuid4)
    paquete_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None
    telefono_destino: str = ""
    tipo: str = "tracking"
    mensaje: str = ""
    estado_envio: str = "pendiente"
    whatsapp_msg_id: str = ""
    error_msg: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Prospecto:
    id: UUID = field(default_factory=uuid4)
    telefono: str = ""
    nombre: str = ""
    origen: str = "whatsapp"
    paso_actual: str = "nuevo"
    estado: str = "activo"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEntry:
    id: UUID = field(default_factory=uuid4)
    tabla: str = ""
    registro_id: Optional[UUID] = None
    accion: str = ""
    usuario_id: Optional[UUID] = None
    valores_anteriores: dict[str, Any] = field(default_factory=dict)
    valores_nuevos: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
