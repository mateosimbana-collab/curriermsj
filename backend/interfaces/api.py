import os
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

import jwt as pyjwt
from flask import Blueprint, jsonify, request, send_file, send_from_directory, g
from werkzeug.security import generate_password_hash

from backend.infrastructure.supabase_repository import get_repo
from backend.application.services import (ClienteService, PaqueteService, TrackingService,
                                          NotificacionService, ProspectoService, DashboardService,
                                          ConfigService, AuthService)


api = Blueprint("api", __name__, url_prefix="/api")

JWT_SECRET = os.getenv("JWT_SECRET", "curriermsj-super-secret-key-change-in-prod")


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error_response("Token requerido", 401)
        token = auth.split(" ", 1)[1]
        try:
            payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.current_user = payload
        except pyjwt.ExpiredSignatureError:
            return error_response("Token expirado", 401)
        except pyjwt.InvalidTokenError:
            return error_response("Token invalido", 401)
        return f(*args, **kwargs)
    return decorated


_svc_instance = None


def svc(name=None):
    global _svc_instance
    if _svc_instance is None:
        r = get_repo()
        _svc_instance = {
            "repo": r,
            "cliente": ClienteService(r),
            "paquete": PaqueteService(r),
            "tracking": TrackingService(r),
            "notif": NotificacionService(r),
            "prospecto": ProspectoService(r),
            "dashboard": DashboardService(r),
            "config": ConfigService(r),
            "auth": AuthService(r),
        }
    return _svc_instance if name is None else _svc_instance.get(name)


def json_response(data: Any, status: int = 200):
    return jsonify({"ok": status < 400, "data": data}), status


def error_response(msg: str, status: int = 400):
    return jsonify({"ok": False, "error": msg}), status


# ============================================
# AUTH
# ============================================

@api.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "")
    password = data.get("password", "")
    if not email or not password:
        return error_response("Email y password requeridos")
    usuario = svc("auth").login(email, password)
    if not usuario:
        return error_response("Credenciales invalidas", 401)
    token = svc("auth").generar_token(usuario)
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
        stats = svc("dashboard").obtener_stats()
        return json_response(stats)
    except Exception as e:
        return error_response(str(e), 500)


# ============================================
# CLIENTES
# ============================================

@api.route("/clientes", methods=["GET"])
@require_auth
def listar_clientes():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    filtros = {k: v for k, v in request.args.items() if k in ("busqueda", "tipo_cliente")}
    result = svc("cliente").listar(page, per_page, filtros)
    return json_response(result)


@api.route("/clientes", methods=["POST"])
@require_auth
def crear_cliente():
    data = request.get_json() or {}
    required = ("cedula", "nombre_completo", "telefono")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    existing = svc("repo").buscar_cliente_por_cedula(data["cedula"])
    if existing:
        return error_response("Ya existe un cliente con esa cedula")
    cliente = svc("repo").crear_cliente(data)
    if not cliente:
        return error_response("Error al crear cliente", 500)
    return json_response(cliente, 201)


@api.route("/clientes/<cliente_id>", methods=["GET"])
@require_auth
def obtener_cliente(cliente_id):
    clientes = svc("repo").listar_clientes(filtros={"busqueda": cliente_id})
    for c in clientes.get("data", []):
        if c["id"] == cliente_id:
            return json_response(c)
    return error_response("Cliente no encontrado", 404)


@api.route("/clientes/<cliente_id>", methods=["PUT"])
@require_auth
def actualizar_cliente(cliente_id):
    data = request.get_json() or {}
    cliente = svc("repo").actualizar_cliente(cliente_id, data)
    if not cliente:
        return error_response("Cliente no encontrado", 404)
    return json_response(cliente)


@api.route("/clientes/<cliente_id>", methods=["DELETE"])
@require_auth
def eliminar_cliente(cliente_id):
    if svc("repo").eliminar_cliente(cliente_id):
        return json_response({"mensaje": "Cliente eliminado"})
    return error_response("Cliente no encontrado", 404)


# ============================================
# PAQUETES
# ============================================

@api.route("/paquetes", methods=["GET"])
@require_auth
def listar_paquetes():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    filtros = {k: v for k, v in request.args.items() if k in ("estado", "cliente_id", "busqueda")}
    result = svc("paquete").listar(page, per_page, filtros)
    return json_response(result)


@api.route("/paquetes", methods=["POST"])
@require_auth
def crear_paquete():
    data = request.get_json() or {}
    if not data.get("cliente_id"):
        return error_response("cliente_id es requerido")
    paquete = svc("repo").crear_paquete(data)
    if not paquete:
        return error_response("Error al crear paquete", 500)
    svc("repo").actualizar_estado_paquete(
        paquete_id=paquete["id"],
        etiqueta="Recibido en USA",
        descripcion="Paquete registrado en sistema",
    )
    return json_response(paquete, 201)


@api.route("/paquetes/<paquete_id>", methods=["GET"])
@require_auth
def obtener_paquete(paquete_id):
    paquete = svc("repo").buscar_paquete_por_tracking(paquete_id)
    if not paquete:
        paquetes = svc("repo").listar_paquetes(filtros={"busqueda": paquete_id})
        for p in paquetes.get("data", []):
            if p["id"] == paquete_id:
                return json_response(p)
        return error_response("Paquete no encontrado", 404)
    return json_response(paquete)


@api.route("/paquetes/buscar", methods=["GET"])
def buscar_paquete():
    tracking = request.args.get("tracking", "")
    if not tracking:
        return error_response("tracking es requerido")
    paquete = svc("paquete").buscar_por_tracking(tracking)
    if not paquete:
        return error_response("Paquete no encontrado", 404)
    return json_response(paquete)


@api.route("/paquetes/<paquete_id>/estado", methods=["PUT"])
@require_auth
def actualizar_estado_paquete(paquete_id):
    data = request.get_json() or {}
    etiqueta = data.get("etiqueta", "")
    if not etiqueta:
        return error_response("etiqueta es requerida")
    paquete = svc("paquete").actualizar_estado(
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
# TRACKING
# ============================================

@api.route("/paquetes/<paquete_id>/tracking", methods=["GET"])
def historial_tracking(paquete_id):
    # Public endpoint - no auth required (used by public tracking)
    eventos = svc("tracking").obtener_historial(paquete_id)
    return json_response(eventos)


# ============================================
# ETIQUETAS / ESTADOS
# ============================================

@api.route("/etiquetas", methods=["GET"])
@require_auth
def listar_etiquetas():
    return json_response(svc("repo").listar_etiquetas())


# ============================================
# PROSPECTOS
# ============================================

@api.route("/prospectos", methods=["GET"])
@require_auth
def listar_prospectos():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return json_response(svc("repo").listar_prospectos(page, per_page))


# ============================================
# SESIONES WHATSAPP
# ============================================

@api.route("/sesiones", methods=["GET"])
@require_auth
def listar_sesiones():
    try:
        res = svc("repo").client.table("sesiones_whatsapp").select("*, clientes!left(nombre_completo)").order("updated_at", desc=True).limit(50).execute()
        return json_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)


# ============================================
# NOTIFICACIONES
# ============================================

@api.route("/notificaciones", methods=["GET"])
@require_auth
def listar_notificaciones():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    try:
        res = svc("repo").client.table("notificaciones").select("*", count="exact").order("created_at", desc=True).range((page-1)*per_page, page*per_page-1).execute()
        return json_response({
            "data": res.data,
            "total": res.count if hasattr(res, "count") else len(res.data),
            "page": page,
            "per_page": per_page,
        })
    except Exception as e:
        return error_response(str(e), 500)


# ============================================
# CONFIGURACION
# ============================================

@api.route("/config", methods=["GET"])
@require_auth
def listar_config():
    return json_response(svc("config").listar())


@api.route("/config/<clave>", methods=["GET"])
@require_auth
def obtener_config(clave):
    valor = svc("config").obtener(clave)
    if valor is None:
        return error_response("Configuracion no encontrada", 404)
    return json_response({"clave": clave, "valor": valor})


@api.route("/config/<clave>", methods=["PUT"])
@require_auth
def actualizar_config(clave):
    data = request.get_json() or {}
    valor = data.get("valor", "")
    if not svc("config").actualizar(clave, valor):
        return error_response("Configuracion no encontrada", 404)
    return json_response({"clave": clave, "valor": valor})


# ============================================
# USUARIOS (admin)
# ============================================

@api.route("/usuarios", methods=["GET"])
@require_auth
def listar_usuarios():
    return json_response(svc("repo").listar_usuarios())


@api.route("/usuarios", methods=["POST"])
@require_auth
def crear_usuario():
    data = request.get_json() or {}
    required = ("email", "password", "nombre")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Campos requeridos: {', '.join(missing)}")
    existing = svc("repo").buscar_usuario_por_email(data["email"])
    if existing:
        return error_response("Ya existe un usuario con ese email")
    usuario = {
        "email": data["email"],
        "password_hash": generate_password_hash(data["password"]),
        "nombre": data["nombre"],
        "telefono": data.get("telefono", ""),
        "rol": data.get("rol", "agente"),
    }
    res = svc("repo").client.table("usuarios").insert(usuario).execute()
    if not res.data:
        return error_response("Error al crear usuario", 500)
    return json_response(res.data[0], 201)


# ============================================
# REPORTES (CSV export)
# ============================================

@api.route("/reportes/paquetes", methods=["GET"])
@require_auth
def reporte_paquetes():
    fecha_desde = request.args.get("desde", datetime.utcnow().replace(day=1).isoformat())
    fecha_hasta = request.args.get("hasta", datetime.utcnow().isoformat())
    data = svc("repo").generar_reporte_paquetes(fecha_desde, fecha_hasta)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tracking", "Estado", "Remitente", "Pais Origen", "Peso (kg)", "Valor", "Fecha Recepcion", "Fecha Entrega"])
    for r in data:
        writer.writerow([
            r.get("tracking_code", ""),
            r.get("estado_actual", ""),
            r.get("remitente_nombre", ""),
            r.get("remitente_pais", ""),
            r.get("peso_kg", 0),
            r.get("valor_declarado", 0),
            r.get("fecha_recepcion", ""),
            r.get("fecha_entrega", ""),
        ])

    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reporte_paquetes_{datetime.utcnow().strftime('%Y%m%d')}.csv",
    )


@api.route("/reportes/clientes", methods=["GET"])
@require_auth
def reporte_clientes():
    data = svc("repo").generar_reporte_clientes()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Cedula", "Nombre", "Telefono", "Tipo", "Ciudad", "Registrado"])
    for r in data:
        writer.writerow([
            r.get("cedula", ""),
            r.get("nombre_completo", ""),
            r.get("telefono", ""),
            r.get("tipo_cliente", ""),
            r.get("ciudad", ""),
            r.get("created_at", ""),
        ])
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reporte_clientes_{datetime.utcnow().strftime('%Y%m%d')}.csv",
    )


# ============================================
# AUDITORIA
# ============================================

@api.route("/audit", methods=["GET"])
@require_auth
def listar_audit():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 30, type=int), 100)
    tabla = request.args.get("tabla", "", type=str)
    return json_response(svc("repo").listar_audit_logs(page=page, per_page=per_page, tabla=tabla))


# ============================================
# CHECKS DE SALUD
# ============================================

@api.route("/health", methods=["GET"])
def health():
    # Public endpoint - no auth required
    estado = {"servidor": "ok", "timestamp": datetime.utcnow().isoformat()}
    try:
        svc("repo").client.table("etiquetas_estado").select("id").limit(1).execute()
        estado["supabase"] = "ok"
    except Exception as e:
        estado["supabase"] = f"error: {str(e)}"
    return json_response(estado)


# ============================================
# FRONTEND ESTATICO
# ============================================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")


def serve_frontend():
    """Registra rutas para servir el frontend."""

    from flask import Flask

    def _serve(path=""):
        if not path or path == "index.html":
            return send_from_directory(FRONTEND_DIR, "index.html")
        try:
            return send_from_directory(FRONTEND_DIR, path)
        except Exception:
            return send_from_directory(FRONTEND_DIR, "index.html")

    return _serve
