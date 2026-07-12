import base64
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

from web.routes import WhatsAppWebhookParser, create_app


LEGACY_USER = "legacy-admin"
LEGACY_PASSWORD = "legacy-password-123"
META_APP_SECRET = "meta-app-secret"


@pytest.fixture
def bot():
    bot = MagicMock()
    bot.repository = MagicMock()
    return bot


@pytest.fixture
def app(bot):
    return create_app(bot)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def security_env(monkeypatch):
    monkeypatch.setenv("LEGACY_DASHBOARD_USER", LEGACY_USER)
    monkeypatch.setenv("LEGACY_DASHBOARD_PASSWORD", LEGACY_PASSWORD)
    monkeypatch.setenv("META_APP_SECRET", META_APP_SECRET)
    monkeypatch.setenv("CORS_ORIGINS", "https://dashboard.test")


@pytest.fixture
def auth_headers():
    token = base64.b64encode(f"{LEGACY_USER}:{LEGACY_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def signed_post(client, payload, headers=None):
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(META_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Hub-Signature-256": signature, **(headers or {})},
    )


class TestWhatsAppWebhookParser:
    def test_parse_text_message(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.1",
                            "type": "text",
                            "text": {"body": "Hola"},
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].phone_number == "593991234567"
        assert events[0].text == "Hola"
        assert events[0].message_type == "text"

    def test_parse_button_reply(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.2",
                            "type": "interactive",
                            "interactive": {
                                "type": "button_reply",
                                "button_reply": {
                                    "id": "cotizar",
                                    "title": "Cotizar",
                                },
                            },
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].text == "cotizar"
        assert events[0].message_type == "interactive_button"

    def test_parse_list_reply(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.3",
                            "type": "interactive",
                            "interactive": {
                                "type": "list_reply",
                                "list_reply": {
                                    "id": "tipo_documento",
                                    "title": "Documentos",
                                },
                            },
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].text == "tipo_documento"
        assert events[0].message_type == "interactive_list"

    def test_parse_location_message(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.4",
                            "type": "location",
                            "location": {
                                "latitude": -0.22985,
                                "longitude": -78.52495,
                            },
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].message_type == "location"
        assert events[0].latitude == -0.22985
        assert events[0].longitude == -78.52495
        assert events[0].has_location is True

    def test_parse_reaction(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.5",
                            "type": "reaction",
                            "reaction": {"emoji": "👍"},
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].message_type == "reaction"
        assert "👍" in events[0].text

    def test_parse_unknown_type(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.6",
                            "type": "unsupported",
                        }],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert len(events) == 1
        assert events[0].message_type == "unsupported"

    def test_parse_no_messages_returns_empty(self):
        payload = {"object": "whatsapp_business_account", "entry": [{"changes": [{"value": {}}]}]}
        events = WhatsAppWebhookParser.parse(payload)
        assert events == []

    def test_parse_no_entry(self):
        events = WhatsAppWebhookParser.parse({})
        assert events == []

    def test_parse_no_from_skips(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{"id": "w1", "type": "text", "text": {"body": "Hola"}}],
                    },
                }],
            }],
        }
        events = WhatsAppWebhookParser.parse(payload)
        assert events == []


class TestWebhookEndpoint:
    def test_get_verify_success(self, client):
        with patch("config.WEBHOOK_VERIFY_TOKEN", "verify_token"):
            resp = client.get("/webhook?hub.mode=subscribe&hub.verify_token=verify_token&hub.challenge=challenge123")
            assert resp.status_code == 200
            assert resp.data.decode() == "challenge123"

    def test_get_verify_fail(self, client):
        with patch("config.WEBHOOK_VERIFY_TOKEN", "real_token"):
            resp = client.get("/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=c")
            assert resp.status_code == 403

    def test_get_verify_no_mode(self, client):
        resp = client.get("/webhook")
        assert resp.status_code == 403

    def test_post_invalid_object(self, client):
        resp = signed_post(client, {"object": "not_whatsapp"})
        assert resp.status_code == 404

    def test_post_statuses_only(self, client):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"statuses": [{"id": "s1"}]}}]}],
        }
        resp = signed_post(client, payload)
        assert resp.status_code == 200

    def test_post_valid_message(self, client, bot):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "593991234567",
                            "id": "w1",
                            "type": "text",
                            "text": {"body": "Hola"},
                        }],
                    },
                }],
            }],
        }
        resp = signed_post(client, payload)
        assert resp.status_code == 200
        bot.process.assert_called_once()

    def test_post_empty_payload(self, client):
        resp = signed_post(client, {})
        assert resp.status_code == 404

    def test_post_rejects_invalid_signature(self, client):
        resp = client.post("/webhook", json={"object": "whatsapp_business_account"})
        assert resp.status_code == 401


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "currier_bot"

    def test_health_has_timestamp(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert "time" in data


class TestDashboardEndpoints:
    def test_dashboard_owner_served(self, app, client, auth_headers):
        resp = client.get("/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        assert b"Due" in resp.data or b"Dueno" in resp.data or b"owner" in resp.data.lower()

    def test_dashboard_soporte_served(self, app, client, auth_headers):
        resp = client.get("/dashboard/soporte", headers=auth_headers)
        assert resp.status_code == 200
        assert b"Soporte" in resp.data or b"soporte" in resp.data.lower()

    def test_dashboard_security_asset_served(self, client, auth_headers):
        resp = client.get("/dashboard-assets/safe-html.js", headers=auth_headers)
        assert resp.status_code == 200
        assert b"setSafeHtml" in resp.data

    def test_dashboard_security_asset_requires_auth(self, client):
        resp = client.get("/dashboard-assets/safe-html.js")
        assert resp.status_code == 401

    def test_api_envios_returns_json(self, app, client, bot, auth_headers):
        bot.repository._table.return_value = "https://test.co/rest/v1/envios"
        bot.repository._request.return_value = [{"id": 1, "remitente": "Juan"}]
        resp = client.get("/api/envios", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1

    def test_api_system_stats(self, app, client, bot, auth_headers):
        bot.repository._table.return_value = "https://test.co/rest/v1/test"
        bot.repository._request.return_value = []
        resp = client.get("/api/system-stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "clientes" in data

    def test_api_logs_returns_list(self, app, client, auth_headers):
        resp = client.get("/api/logs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_api_dashboard_returns_stats(self, client, bot, auth_headers):
        bot.repository.get_dashboard_stats.return_value = {
            "total_shipments": 0,
            "shipments_today": 0,
            "active_users": 0,
            "total_reports": 0,
            "open_reports": 0,
            "recent_shipments": [],
            "active_sessions": [],
            "shipments_by_day": [],
        }
        resp = client.get("/api/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "currier_bot"

    def test_api_earnings_returns_json(self, client, bot, auth_headers):
        bot.repository._table.return_value = "https://test.co/rest/v1/envios"
        bot.repository._request.return_value = []
        resp = client.get("/api/earnings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total" in data
        assert data["total"] == 0

    def test_api_finance_summary(self, app, client, bot, auth_headers):
        bot.repository._table.return_value = "https://test.co/rest/v1/test"
        bot.repository._request.return_value = []
        resp = client.get("/api/finance-summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "income_today" in data


class TestCORS:
    def test_cors_headers_present(self, client):
        resp = client.get("/health", headers={"Origin": "https://dashboard.test"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://dashboard.test"
        assert resp.headers.get("Access-Control-Allow-Credentials") == "true"
        assert resp.headers.get("Access-Control-Allow-Headers") == "Authorization, Content-Type"
        assert resp.headers.get("Access-Control-Allow-Methods") == "GET, OPTIONS"

    def test_cors_on_post(self, client):
        resp = signed_post(
            client,
            {"object": "not_whatsapp"},
            headers={"Origin": "https://dashboard.test"},
        )
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://dashboard.test"

    def test_cors_rejects_unknown_origin(self, client):
        resp = client.get("/health", headers={"Origin": "https://attacker.test"})
        assert "Access-Control-Allow-Origin" not in resp.headers
