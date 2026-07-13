import os
import csv
import io
import logging
import math
import time
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from threading import Lock
from typing import Any
from urllib.parse import urlparse

import jwt as pyjwt
from flask import Blueprint, jsonify, request, send_file, send_from_directory, g
from werkzeug.security import generate_password_hash

from backend.infrastructure.supabase_repository import get_repo
from backend.application.services import AuthService


api = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

VALID_ROLES = frozenset({"admin", "supervisor", "agente", "soporte"})
OPERATIONS_ROLES = ("admin", "supervisor", "agente")
BUSINESS_TZ = timezone(timedelta(hours=-5))
CLIENT_FIELDS = frozenset({
    "cedula", "nombre_completo", "telefono", "telefono_alternativo", "email",
    "direccion", "ciudad", "pais", "tipo_cliente", "grupo_id", "mayorista_id", "notas",
})
PACKAGE_FIELDS = frozenset({
    "tracking_code", "cliente_id", "grupo_id", "remitente_nombre", "remitente_direccion",
    "remitente_telefono", "remitente_pais", "destinatario_nombre", "destinatario_telefono",
    "destinatario_direccion", "destinatario_ciudad", "tipo_paquete", "peso_kg", "dimensiones",
    "contenido", "valor_declarado", "valor_flete", "servicio_envio", "imagen_url",
    "notas_internas", "requiere_aprobacion", "categoria_importacion",
    "modalidad_entrega", "fecha_prometida",
})
RECEPTION_FIELDS = frozenset({
    "cliente_id", "grupo_id", "tracking_externo", "transportista", "tienda", "contenido",
    "peso_kg", "foto_url", "notas", "estado_operativo", "recibido_en",
})
PAYMENT_FIELDS = frozenset({
    "paquete_id", "monto", "metodo", "referencia", "comprobante_url", "estado",
})
RECEPTION_STATES = frozenset({
    "por_procesar", "fotos_enviadas", "esperando_decision", "despachar", "armado",
    "consolidado",
})
PAYMENT_STATES = frozenset({"pendiente", "verificado", "rechazado"})
PAYMENT_METHODS = frozenset({"transferencia", "efectivo", "otro"})
PUBLIC_PACKAGE_FIELDS = (
    "id", "tracking_code", "remitente_nombre", "remitente_pais", "destinatario_nombre",
    "destinatario_ciudad", "tipo_paquete", "peso_kg", "estado_actual", "etiqueta_actual",
    "fecha_recepcion", "fecha_despacho", "fecha_entrega", "imagen_url", "created_at",
    "fecha_prometida", "modalidad_entrega", "categoria_importacion",
)
PUBLIC_TRACKING_FIELDS = (
    "id", "paquete_id", "etiqueta", "descripcion", "ubicacion", "foto_url", "es_automatico",
    "created_at",
)

_LOGIN_FAILURES: dict[str, list[float]] = {}
_LOGIN_LOCK = Lock()
_LOGIN_WINDOW_SECONDS = 60
_LOGIN_MAX_FAILURES = 5


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET debe tener al menos 32 caracteres")
    return secret


def _only(data: Any, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items() if key in fields}


def _pagination(default: int = 20, maximum: int = 100) -> tuple[int, int]:
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = request.args.get("per_page", default, type=int) or default
    return page, min(max(per_page, 1), maximum)


def _login_limited(key: str) -> bool:
    cutoff = time.monotonic() - _LOGIN_WINDOW_SECONDS
    with _LOGIN_LOCK:
        failures = [attempt for attempt in _LOGIN_FAILURES.get(key, []) if attempt >= cutoff]
        if failures:
            _LOGIN_FAILURES[key] = failures
        else:
            _LOGIN_FAILURES.pop(key, None)
        return len(failures) >= _LOGIN_MAX_FAILURES


def _record_login_failure(key: str) -> None:
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.setdefault(key, []).append(time.monotonic())


def _csv_cell(value: Any) -> Any:
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _business_due_date(days: int = 10) -> str:
    current = datetime.now(BUSINESS_TZ).date()
    remaining = days
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current.isoformat()


def _valid_iso_date(value: Any) -> bool:
    if not value:
        return True
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def _normalize_number(data: dict[str, Any], field: str, *, positive: bool = False) -> None:
    if field not in data or data[field] in (None, ""):
        data.pop(field, None)
        return
    try:
        value = round(float(data[field]), 2)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} debe ser numerico") from exc
    if not math.isfinite(value):
        raise ValueError(f"{field} debe ser numerico")
    if value < 0 or (positive and value == 0):
        qualifier = "mayor a cero" if positive else "cero o mayor"
        raise ValueError(f"{field} debe ser {qualifier}")
    data[field] = value


def _valid_http_url(value: Any) -> bool:
    if not value:
        return True
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error_response("Token requerido", 401)
        token = auth.split(" ", 1)[1]
        try:
            payload = pyjwt.decode(
                token,
                _jwt_secret(),
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "iat"]},
            )
            g.current_user = payload
        except pyjwt.ExpiredSignatureError:
            return error_response("Token expirado", 401)
        except pyjwt.InvalidTokenError:
            return error_response("Token invalido", 401)
        return f(*args, **kwargs)
    return decorated


def require_roles(*roles: str):
    def decorator(f):
        @wraps(f)
        def authorized(*args, **kwargs):
            if g.current_user.get("rol") not in roles:
                return error_response("Permisos insuficientes", 403)
            return f(*args, **kwargs)
        return require_auth(authorized)
    return decorator


def repo():
    return get_repo()


def json_response(data: Any, status: int = 200):
    return jsonify({"ok": status < 400, "data": data}), status


def error_response(msg: str, status: int = 400):
    return jsonify({"ok": False, "error": msg}), status


# ============================================
# AUTH
# ============================================

@api.route("/auth/login", methods=["POST"])
def login():
    key = request.remote_addr or "unknown"
    if _login_limited(key):
        return error_response("Demasiados intentos. Intenta de nuevo en un minuto", 429)

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()[:254]
    password = str(data.get("password", ""))
    if not email or not password:
        return error_response("Email y password requeridos")
    auth_service = AuthService(repo())
    usuario = auth_service.login(email, password)
    if not usuario:
        _record_login_failure(key)
        return error_response("Credenciales invalidas", 401)
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(key, None)
    token = auth_service.generar_token(usuario, _jwt_secret())
    return json_response({
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "email": usuario["email"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
        }
    })


# ============================================
# DASHBOARD
# ============================================

@api.route("/dashboard", methods=["GET"])
@require_auth
def dashboard():
    try:
        stats = repo().get_dashboard_stats()
        return json_response(stats)
    except Exception:
        logger.exception("No se pudo cargar el dashboard")
        return error_response("No se pudo cargar el dashboard", 500)


# ============================================
# CLIENTES
# ============================================

@api.route("/clientes", methods=["GET"])
@require_auth
def listar_clientes():
    page, per_page = _pagination()
    filtros = {k: v for k, v in request.args.items() if k in ("busqueda", "tipo_cliente")}
    result = repo().listar_clientes(page, per_page, filtros)
    return json_response(result)


@api.route("/clientes", methods=["POST"])
@require_roles(*OPERATIONS_ROLES)
def crear_cliente():
    data = _only(request.get_json(silent=True), CLIENT_FIELDS)
    required = ("cedula", "nombre_completo", "telefono")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    existing = repo().buscar_cliente_por_cedula(data["cedula"])
    if existing:
        return error_response("Ya existe un cliente con esa cedula")
    cliente = repo().crear_cliente(data)
    if not cliente:
        return error_response("Error al crear cliente", 500)
    return json_response(cliente, 201)


@api.route("/clientes/<cliente_id>", methods=["GET"])
@require_auth
def obtener_cliente(cliente_id):
    clientes = repo().listar_clientes(filtros={"busqueda": cliente_id})
    for c in clientes.get("data", []):
        if c["id"] == cliente_id:
            return json_response(c)
    return error_response("Cliente no encontrado", 404)


@api.route("/clientes/<cliente_id>", methods=["PUT"])
@require_roles(*OPERATIONS_ROLES)
def actualizar_cliente(cliente_id):
    data = _only(request.get_json(silent=True), CLIENT_FIELDS)
    if not data:
        return error_response("No hay campos validos para actualizar")
    cliente = repo().actualizar_cliente(cliente_id, data)
    if not cliente:
        return error_response("Cliente no encontrado", 404)
    return json_response(cliente)


@api.route("/clientes/<cliente_id>", methods=["DELETE"])
@require_roles("admin", "supervisor")
def eliminar_cliente(cliente_id):
    if repo().eliminar_cliente(cliente_id):
        return json_response({"mensaje": "Cliente eliminado"})
    return error_response("Cliente no encontrado", 404)


# ============================================
# PAQUETES
# ============================================

@api.route("/paquetes", methods=["GET"])
@require_auth
def listar_paquetes():
    page, per_page = _pagination()
    filtros = {k: v for k, v in request.args.items() if k in ("estado", "cliente_id", "busqueda")}
    result = repo().listar_paquetes(page, per_page, filtros)
    return json_response(result)


@api.route("/paquetes", methods=["POST"])
@require_roles(*OPERATIONS_ROLES)
def crear_paquete():
    data = _only(request.get_json(silent=True), PACKAGE_FIELDS)
    if not data.get("cliente_id"):
        return error_response("cliente_id es requerido")
    paquete = repo().crear_paquete(data)
    if not paquete:
        return error_response("Error al crear paquete", 500)
    repo().actualizar_estado_paquete(
        paquete_id=paquete["id"],
        etiqueta="Recibido en USA",
        descripcion="Paquete registrado en sistema",
    )
    return json_response(paquete, 201)


@api.route("/paquetes/<paquete_id>", methods=["GET"])
@require_auth
def obtener_paquete(paquete_id):
    paquete = repo().buscar_paquete_por_tracking(paquete_id)
    if not paquete:
        paquetes = repo().listar_paquetes(filtros={"busqueda": paquete_id})
        for p in paquetes.get("data", []):
            if p["id"] == paquete_id:
                return json_response(p)
        return error_response("Paquete no encontrado", 404)
    return json_response(paquete)


@api.route("/paquetes/buscar", methods=["GET"])
def buscar_paquete():
    tracking = request.args.get("tracking", "").strip().upper()[:64]
    if not tracking:
        return error_response("tracking es requerido")
    paquete = repo().buscar_paquete_por_tracking(tracking)
    if not paquete:
        return error_response("Paquete no encontrado", 404)
    return json_response({field: paquete.get(field) for field in PUBLIC_PACKAGE_FIELDS})


@api.route("/paquetes/<paquete_id>/estado", methods=["PUT"])
@require_roles(*OPERATIONS_ROLES)
def actualizar_estado_paquete(paquete_id):
    data = request.get_json(silent=True) or {}
    etiqueta = data.get("etiqueta", "")
    if not etiqueta:
        return error_response("etiqueta es requerida")
    paquete = repo().actualizar_estado_paquete(
        paquete_id=paquete_id,
        etiqueta=etiqueta,
        descripcion=data.get("descripcion", ""),
        ubicacion=data.get("ubicacion", ""),
        foto_url=data.get("foto_url", ""),
    )
    if not paquete:
        return error_response("Paquete no encontrado", 404)
    return json_response(paquete)


# ============================================
# RECEPCIONES EN USA / CONSOLIDACION
# ============================================

@api.route("/recepciones", methods=["GET"])
@require_auth
def listar_recepciones():
    page, per_page = _pagination(default=30)
    filtros = {
        key: value
        for key, value in request.args.items()
        if key in ("estado", "cliente_id", "busqueda", "sin_despacho")
    }
    if filtros.get("estado") and filtros["estado"] not in RECEPTION_STATES:
        return error_response("Estado operativo invalido")
    filtros["sin_despacho"] = filtros.get("sin_despacho", "").lower() in {"1", "true", "si"}
    try:
        return json_response(repo().listar_recepciones(page, per_page, filtros))
    except Exception:
        logger.exception("No se pudieron listar las recepciones")
        return error_response("No se pudieron listar las recepciones. Aplica la migracion 005.", 500)


@api.route("/recepciones", methods=["POST"])
@require_roles(*OPERATIONS_ROLES)
def crear_recepcion():
    data = _only(request.get_json(silent=True), RECEPTION_FIELDS)
    missing = [field for field in ("cliente_id", "tracking_externo") if not data.get(field)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    data["tracking_externo"] = str(data["tracking_externo"]).strip().upper()[:120]
    if not data["tracking_externo"]:
        return error_response("tracking_externo es requerido")
    state = str(data.get("estado_operativo") or "por_procesar")
    if state not in RECEPTION_STATES - {"consolidado"}:
        return error_response("Estado operativo invalido")
    data["estado_operativo"] = state
    for field, limit in {
        "transportista": 100,
        "tienda": 120,
        "contenido": 500,
        "foto_url": 1000,
        "notas": 1000,
    }.items():
        if field in data:
            data[field] = str(data[field]).strip()[:limit]
    if not _valid_http_url(data.get("foto_url")):
        return error_response("foto_url debe ser un enlace http o https")
    try:
        _normalize_number(data, "peso_kg")
        reception = repo().crear_recepcion(data, g.current_user.get("sub", ""))
    except ValueError as exc:
        return error_response(str(exc))
    except Exception as exc:
        logger.exception("No se pudo crear la recepcion")
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            return error_response("Ese tracking externo ya esta registrado", 409)
        return error_response("No se pudo crear la recepcion", 500)
    if not reception:
        return error_response("No se pudo crear la recepcion", 500)
    return json_response(reception, 201)


@api.route("/recepciones/<recepcion_id>", methods=["PUT"])
@require_roles(*OPERATIONS_ROLES)
def actualizar_recepcion(recepcion_id):
    data = _only(request.get_json(silent=True), RECEPTION_FIELDS)
    data.pop("cliente_id", None)
    data.pop("grupo_id", None)
    if not data:
        return error_response("No hay campos validos para actualizar")
    if data.get("estado_operativo") not in (None, *RECEPTION_STATES):
        return error_response("Estado operativo invalido")
    if data.get("estado_operativo") == "consolidado":
        return error_response("Consolida la recepcion desde la accion Crear despacho")
    if not _valid_http_url(data.get("foto_url")):
        return error_response("foto_url debe ser un enlace http o https")
    try:
        _normalize_number(data, "peso_kg")
        reception = repo().actualizar_recepcion(
            recepcion_id,
            data,
            g.current_user.get("sub", ""),
        )
    except ValueError as exc:
        return error_response(str(exc))
    except Exception:
        logger.exception("No se pudo actualizar la recepcion")
        return error_response("No se pudo actualizar la recepcion", 500)
    if not reception:
        return error_response("Recepcion no encontrada", 404)
    return json_response(reception)


@api.route("/recepciones/consolidar", methods=["POST"])
@require_roles(*OPERATIONS_ROLES)
def consolidar_recepciones():
    body = request.get_json(silent=True) or {}
    ids = body.get("recepcion_ids")
    if not isinstance(ids, list) or not ids or len(ids) > 100:
        return error_response("recepcion_ids debe contener entre 1 y 100 elementos")
    ids = [str(item) for item in ids if item]
    package_data = _only(body.get("paquete"), PACKAGE_FIELDS)
    if not package_data.get("cliente_id"):
        return error_response("cliente_id es requerido")
    package_data.setdefault("remitente_nombre", "Bodega USA")
    package_data.setdefault("remitente_pais", "Estados Unidos")
    required = ("destinatario_nombre", "destinatario_direccion")
    missing = [field for field in required if not package_data.get(field)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    category = package_data.get("categoria_importacion")
    if category and category not in {"B", "C", "G"}:
        return error_response("categoria_importacion debe ser B, C o G")
    delivery = package_data.get("modalidad_entrega")
    if delivery and delivery not in {"retiro", "domicilio"}:
        return error_response("modalidad_entrega invalida")
    if not _valid_iso_date(package_data.get("fecha_prometida")):
        return error_response("fecha_prometida debe usar formato YYYY-MM-DD")
    package_data.setdefault("fecha_prometida", _business_due_date())
    try:
        for field in ("peso_kg", "valor_declarado", "valor_flete"):
            _normalize_number(package_data, field)
        result = repo().consolidar_recepciones(
            ids,
            package_data,
            g.current_user.get("sub", ""),
        )
    except ValueError as exc:
        return error_response(str(exc), 409)
    except Exception:
        logger.exception("No se pudieron consolidar las recepciones")
        return error_response("No se pudo crear el despacho", 500)
    return json_response(result, 201)


# ============================================
# COBROS
# ============================================

@api.route("/cobros", methods=["GET"])
@require_roles(*OPERATIONS_ROLES)
def listar_cobros():
    state = request.args.get("estado", "", type=str)
    if state and state not in {"pendiente", "abono", "pagado"}:
        return error_response("Estado de cobro invalido")
    try:
        return json_response(repo().listar_cobros(state))
    except Exception:
        logger.exception("No se pudieron listar los cobros")
        return error_response("No se pudieron listar los cobros. Aplica la migracion 005.", 500)


@api.route("/pagos", methods=["POST"])
@require_roles(*OPERATIONS_ROLES)
def registrar_pago():
    data = _only(request.get_json(silent=True), PAYMENT_FIELDS)
    if not data.get("paquete_id") or data.get("monto") in (None, ""):
        return error_response("paquete_id y monto son requeridos")
    method = str(data.get("metodo") or "transferencia")
    if method not in PAYMENT_METHODS:
        return error_response("Metodo de pago invalido")
    data["metodo"] = method
    requested_state = str(data.get("estado") or "pendiente")
    if requested_state not in PAYMENT_STATES:
        return error_response("Estado de pago invalido")
    if g.current_user.get("rol") not in {"admin", "supervisor"}:
        requested_state = "pendiente"
    data["estado"] = requested_state
    for field, limit in {"referencia": 160, "comprobante_url": 1000}.items():
        if field in data:
            data[field] = str(data[field]).strip()[:limit]
    if not _valid_http_url(data.get("comprobante_url")):
        return error_response("comprobante_url debe ser un enlace http o https")
    try:
        _normalize_number(data, "monto", positive=True)
        payment = repo().registrar_pago(data, g.current_user.get("sub", ""))
    except ValueError as exc:
        return error_response(str(exc))
    except Exception:
        logger.exception("No se pudo registrar el pago")
        return error_response("No se pudo registrar el pago", 500)
    if not payment:
        return error_response("No se pudo registrar el pago", 500)
    return json_response(payment, 201)


@api.route("/pagos/<pago_id>/estado", methods=["PUT"])
@require_roles("admin", "supervisor")
def verificar_pago(pago_id):
    state = str((request.get_json(silent=True) or {}).get("estado") or "")
    if state not in {"verificado", "rechazado"}:
        return error_response("El estado debe ser verificado o rechazado")
    try:
        payment = repo().actualizar_estado_pago(
            pago_id,
            state,
            g.current_user.get("sub", ""),
        )
    except ValueError as exc:
        return error_response(str(exc))
    except Exception:
        logger.exception("No se pudo verificar el pago")
        return error_response("No se pudo verificar el pago", 500)
    if not payment:
        return error_response("Pago no encontrado", 404)
    return json_response(payment)


@api.route("/operaciones/resumen", methods=["GET"])
@require_auth
def resumen_operativo():
    include_money = g.current_user.get("rol") in {"admin", "supervisor"}
    return json_response(repo().get_operational_summary(include_money=include_money))


# ============================================
# TRACKING
# ============================================

@api.route("/paquetes/<paquete_id>/tracking", methods=["GET"])
def historial_tracking(paquete_id):
    eventos = repo().obtener_historial_tracking(paquete_id)
    return json_response([
        {field: evento.get(field) for field in PUBLIC_TRACKING_FIELDS}
        for evento in eventos
    ])


# ============================================
# ETIQUETAS / ESTADOS
# ============================================

@api.route("/etiquetas", methods=["GET"])
@require_auth
def listar_etiquetas():
    return json_response(repo().listar_etiquetas())


# ============================================
# PROSPECTOS
# ============================================

@api.route("/prospectos", methods=["GET"])
@require_auth
def listar_prospectos():
    page, per_page = _pagination()
    return json_response(repo().listar_prospectos(page, per_page))


# ============================================
# SESIONES WHATSAPP
# ============================================

@api.route("/sesiones", methods=["GET"])
@require_auth
def listar_sesiones():
    try:
        res = repo().client.table("sesiones_whatsapp").select("*, clientes!left(nombre_completo)").order("updated_at", desc=True).limit(50).execute()
        return json_response(res.data)
    except Exception:
        logger.exception("No se pudieron listar las sesiones")
        return error_response("No se pudieron listar las sesiones", 500)


# ============================================
# NOTIFICACIONES
# ============================================

@api.route("/notificaciones", methods=["GET"])
@require_auth
def listar_notificaciones():
    page, per_page = _pagination()
    try:
        res = repo().client.table("notificaciones").select("*", count="exact").order("created_at", desc=True).range((page-1)*per_page, page*per_page-1).execute()
        return json_response({
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        })
    except Exception:
        logger.exception("No se pudieron listar las notificaciones")
        return error_response("No se pudieron listar las notificaciones", 500)


# ============================================
# CONFIGURACION
# ============================================

@api.route("/config", methods=["GET"])
@require_roles("admin")
def listar_config():
    return json_response(repo().listar_config())


@api.route("/config/<clave>", methods=["GET"])
@require_roles("admin")
def obtener_config(clave):
    valor = repo().obtener_config(clave)
    if valor is None:
        return error_response("Configuracion no encontrada", 404)
    return json_response({"clave": clave, "valor": valor})


@api.route("/config/<clave>", methods=["PUT"])
@require_roles("admin")
def actualizar_config(clave):
    data = request.get_json(silent=True) or {}
    valor = data.get("valor", "")
    if not repo().actualizar_config(clave, str(valor)):
        return error_response("Configuracion no encontrada", 404)
    return json_response({"clave": clave, "valor": valor})


# ============================================
# USUARIOS (admin)
# ============================================

@api.route("/usuarios", methods=["GET"])
@require_roles("admin")
def listar_usuarios():
    return json_response(repo().listar_usuarios())


@api.route("/usuarios", methods=["POST"])
@require_roles("admin")
def crear_usuario():
    data = request.get_json(silent=True) or {}
    required = ("email", "password", "nombre")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    email = str(data["email"]).strip().lower()[:254]
    password = str(data["password"])
    role = str(data.get("rol", "agente"))
    if len(password) < 12:
        return error_response("El password debe tener al menos 12 caracteres")
    if role not in VALID_ROLES:
        return error_response("Rol invalido")
    existing = repo().buscar_usuario_por_email(email)
    if existing:
        return error_response("Ya existe un usuario con ese email")
    usuario = {
        "email": email,
        "password_hash": generate_password_hash(password),
        "nombre": str(data["nombre"]).strip()[:200],
        "telefono": str(data.get("telefono", ""))[:32],
        "rol": role,
    }
    res = repo().client.table("usuarios").insert(usuario).execute()
    if not res.data:
        return error_response("Error al crear usuario", 500)
    return json_response(res.data[0], 201)


# ============================================
# REPORTES (CSV export)
# ============================================

@api.route("/reportes/paquetes", methods=["GET"])
@require_roles("admin", "supervisor")
def reporte_paquetes():
    now = datetime.now(timezone.utc)
    fecha_desde = request.args.get("desde", now.replace(day=1).isoformat())
    fecha_hasta = request.args.get("hasta", now.isoformat())
    data = repo().generar_reporte_paquetes(fecha_desde, fecha_hasta)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tracking", "Estado", "Remitente", "Pais Origen", "Peso (kg)", "Valor", "Fecha Recepcion", "Fecha Entrega"])
    for r in data:
        writer.writerow([_csv_cell(value) for value in [
            r.get("tracking_code", ""),
            r.get("estado_actual", ""),
            r.get("remitente_nombre", ""),
            r.get("remitente_pais", ""),
            r.get("peso_kg", 0),
            r.get("valor_declarado", 0),
            r.get("fecha_recepcion", ""),
            r.get("fecha_entrega", ""),
        ]])

    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reporte_paquetes_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
    )


@api.route("/reportes/clientes", methods=["GET"])
@require_roles("admin", "supervisor")
def reporte_clientes():
    data = repo().generar_reporte_clientes()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Cedula", "Nombre", "Telefono", "Tipo", "Ciudad", "Registrado"])
    for r in data:
        writer.writerow([_csv_cell(value) for value in [
            r.get("cedula", ""),
            r.get("nombre_completo", ""),
            r.get("telefono", ""),
            r.get("tipo_cliente", ""),
            r.get("ciudad", ""),
            r.get("created_at", ""),
        ]])
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reporte_clientes_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
    )


# ============================================
# AUDITORIA
# ============================================

@api.route("/audit", methods=["GET"])
@require_roles("admin", "supervisor")
def listar_audit():
    page, per_page = _pagination(default=30)
    tabla = request.args.get("tabla", "", type=str)[:64]
    return json_response(repo().listar_audit_logs(page=page, per_page=per_page, tabla=tabla))


# ============================================
# CHECKS DE SALUD
# ============================================

@api.route("/health", methods=["GET"])
def health():
    # Public endpoint - no auth required
    estado = {"servidor": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        repo().client.table("etiquetas_estado").select("id").limit(1).execute()
        estado["supabase"] = "ok"
    except Exception:
        estado["supabase"] = "error"
    return json_response(estado)


# ============================================
# FRONTEND ESTATICO
# ============================================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")


def serve_frontend():
    """Registra rutas para servir el frontend."""

    def _serve(path=""):
        if not path or path == "index.html":
            return send_from_directory(FRONTEND_DIR, "index.html")
        try:
            return send_from_directory(FRONTEND_DIR, path)
        except Exception:
            return send_from_directory(FRONTEND_DIR, "index.html")

    return _serve
