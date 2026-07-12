import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
os.environ.setdefault("WEBHOOK_VERIFY_TOKEN", "verify-token")
os.environ.setdefault("META_APP_SECRET", "meta-app-secret")

from backend.config.app import create_app
from backend.interfaces import api as api_module
from database.create_admin import validate_password


def _token(role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": "user-1", "rol": role, "iat": now, "exp": now + timedelta(minutes=5)},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_create_app_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError, match="32 caracteres"):
        create_app()


def test_admin_route_rejects_non_admin(client):
    response = client.get("/api/usuarios", headers={"Authorization": f"Bearer {_token('agente')}"})
    assert response.status_code == 403


def test_public_tracking_does_not_expose_customer_or_internal_fields(client, monkeypatch):
    class Repo:
        def buscar_paquete_por_tracking(self, tracking):
            assert tracking == "CUR-01000"
            return {
                "id": "package-1",
                "tracking_code": tracking,
                "estado_actual": "en_transito",
                "notas_internas": "no publicar",
                "clientes": {"cedula": "secret", "telefono": "secret"},
            }

    monkeypatch.setattr(api_module, "repo", lambda: Repo())
    response = client.get("/api/paquetes/buscar?tracking=cur-01000")
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["tracking_code"] == "CUR-01000"
    assert "clientes" not in data
    assert "notas_internas" not in data


def test_client_payload_is_allowlisted(client, monkeypatch):
    class Repo:
        saved = None

        def buscar_cliente_por_cedula(self, cedula):
            return None

        def crear_cliente(self, data):
            self.saved = data
            return {"id": "client-1", **data}

    fake = Repo()
    monkeypatch.setattr(api_module, "repo", lambda: fake)
    response = client.post(
        "/api/clientes",
        headers={"Authorization": f"Bearer {_token('agente')}"},
        json={
            "cedula": "123",
            "nombre_completo": "Cliente",
            "telefono": "0999999999",
            "rol": "admin",
            "deleted_at": "2020-01-01",
        },
    )
    assert response.status_code == 201
    assert "rol" not in fake.saved
    assert "deleted_at" not in fake.saved


def test_webhook_requires_a_valid_meta_signature(client):
    payload = {"object": "whatsapp_business_account", "entry": []}
    body = json.dumps(payload).encode()
    invalid = client.post("/webhook", data=body, content_type="application/json")
    assert invalid.status_code == 401

    signature = "sha256=" + hmac.new(
        os.environ["META_APP_SECRET"].encode(), body, hashlib.sha256
    ).hexdigest()
    valid = client.post(
        "/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Hub-Signature-256": signature},
    )
    assert valid.status_code == 200


def test_security_headers_are_added(client):
    response = client.get("/missing")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_admin_password_policy():
    with pytest.raises(ValueError):
        validate_password("too-short")
    validate_password("a-secure-password")
