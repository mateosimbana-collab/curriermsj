import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
os.environ.setdefault("WEBHOOK_VERIFY_TOKEN", "verify-token")
os.environ.setdefault("META_APP_SECRET", "meta-app-secret")

from backend.config.app import create_app
from backend.infrastructure.supabase_repository import SupabaseRepository
from backend.interfaces import api as api_module


def _token(role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": "user-1", "rol": role, "iat": now, "exp": now + timedelta(minutes=5)},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def _headers(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(role)}"}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_create_reception_normalizes_and_allowlists_payload(client, monkeypatch):
    class Repo:
        saved = None

        def crear_recepcion(self, data, usuario_id):
            self.saved = {**data, "usuario_id": usuario_id}
            return {"id": "receipt-1", **data}

    fake = Repo()
    monkeypatch.setattr(api_module, "repo", lambda: fake)
    response = client.post(
        "/api/recepciones",
        headers=_headers("agente"),
        json={
            "cliente_id": "client-1",
            "tracking_externo": " 1zabc123 ",
            "peso_kg": "2.5",
            "tienda": "Amazon",
            "despacho_id": "forbidden",
            "created_by": "forbidden",
        },
    )

    assert response.status_code == 201
    assert fake.saved["tracking_externo"] == "1ZABC123"
    assert fake.saved["peso_kg"] == 2.5
    assert fake.saved["usuario_id"] == "user-1"
    assert "despacho_id" not in fake.saved
    assert "created_by" not in fake.saved


def test_consolidation_sets_manual_delivery_fields_and_deadline(client, monkeypatch):
    class Repo:
        saved = None

        def consolidar_recepciones(self, ids, package, usuario_id):
            self.saved = (ids, package, usuario_id)
            return {"paquete": {"id": "package-1"}, "recepciones": []}

    fake = Repo()
    monkeypatch.setattr(api_module, "repo", lambda: fake)
    monkeypatch.setattr(api_module, "_business_due_date", lambda: "2026-07-17")
    response = client.post(
        "/api/recepciones/consolidar",
        headers=_headers("agente"),
        json={
            "recepcion_ids": ["receipt-1", "receipt-2"],
            "paquete": {
                "cliente_id": "client-1",
                "destinatario_nombre": "Maria Perez",
                "destinatario_direccion": "Cuenca",
                "categoria_importacion": "B",
                "modalidad_entrega": "retiro",
                "valor_flete": "45.90",
            },
        },
    )

    assert response.status_code == 201
    ids, package, usuario_id = fake.saved
    assert ids == ["receipt-1", "receipt-2"]
    assert package["fecha_prometida"] == "2026-07-17"
    assert package["valor_flete"] == 45.9
    assert package["remitente_nombre"] == "Bodega USA"
    assert usuario_id == "user-1"


def test_agent_cannot_self_verify_payment(client, monkeypatch):
    class Repo:
        saved = None

        def registrar_pago(self, data, usuario_id):
            self.saved = {**data, "usuario_id": usuario_id}
            return {"id": "payment-1", **data}

    fake = Repo()
    monkeypatch.setattr(api_module, "repo", lambda: fake)
    response = client.post(
        "/api/pagos",
        headers=_headers("agente"),
        json={
            "paquete_id": "package-1",
            "monto": 20,
            "estado": "verificado",
            "metodo": "transferencia",
        },
    )

    assert response.status_code == 201
    assert fake.saved["estado"] == "pendiente"


def test_payment_rejects_non_finite_amount(client, monkeypatch):
    monkeypatch.setattr(api_module, "repo", MagicMock())
    response = client.post(
        "/api/pagos",
        headers=_headers("agente"),
        json={"paquete_id": "package-1", "monto": "NaN"},
    )

    assert response.status_code == 400
    assert "numerico" in response.get_json()["error"]


def test_operational_summary_only_exposes_money_to_owner_roles(client, monkeypatch):
    class Repo:
        flags = []

        def get_operational_summary(self, include_money):
            self.flags.append(include_money)
            result = {"por_procesar": 2}
            if include_money:
                result["cartera_pendiente"] = 120
            return result

    fake = Repo()
    monkeypatch.setattr(api_module, "repo", lambda: fake)

    agent = client.get("/api/operaciones/resumen", headers=_headers("agente"))
    owner = client.get("/api/operaciones/resumen", headers=_headers("admin"))

    assert "cartera_pendiente" not in agent.get_json()["data"]
    assert owner.get_json()["data"]["cartera_pendiente"] == 120
    assert fake.flags == [False, True]


def _repository_with_receptions(rows):
    repository = object.__new__(SupabaseRepository)
    repository.client = MagicMock()
    query = MagicMock()
    query.select.return_value = query
    query.in_.return_value = query
    query.is_.return_value = query
    query.execute.return_value = SimpleNamespace(data=rows)
    repository.client.table.return_value = query
    repository.crear_paquete = MagicMock()
    return repository


def test_consolidation_rejects_unrelated_package_client():
    repository = _repository_with_receptions([
        {"id": "r1", "cliente_id": "client-1", "grupo_id": "group-1", "estado_operativo": "armado"},
        {"id": "r2", "cliente_id": "client-2", "grupo_id": "group-1", "estado_operativo": "armado"},
    ])

    with pytest.raises(ValueError, match="cliente seleccionado"):
        repository.consolidar_recepciones(["r1", "r2"], {"cliente_id": "client-3"})

    repository.crear_paquete.assert_not_called()


def test_consolidation_rejects_reception_before_dispatch_stage():
    repository = _repository_with_receptions([
        {"id": "r1", "cliente_id": "client-1", "grupo_id": None, "estado_operativo": "por_procesar"},
    ])

    with pytest.raises(ValueError, match="estado despachar o armado"):
        repository.consolidar_recepciones(["r1"], {"cliente_id": "client-1"})

    repository.crear_paquete.assert_not_called()
