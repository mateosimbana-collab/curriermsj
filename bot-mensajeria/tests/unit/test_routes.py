from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from domain.models import IncomingMessage
from web.routes import WhatsAppWebhookParser, create_app


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
        resp = client.post("/webhook", json={"object": "not_whatsapp"})
        assert resp.status_code == 404

    def test_post_statuses_only(self, client):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"statuses": [{"id": "s1"}]}}]}],
        }
        resp = client.post("/webhook", json=payload)
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
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        bot.process.assert_called_once()

    def test_post_empty_payload(self, client):
        resp = client.post("/webhook", json={})
        assert resp.status_code == 404


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
    def test_dashboard_owner_served(self, app, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Due" in resp.data or b"Dueno" in resp.data or b"owner" in resp.data.lower()

    def test_dashboard_soporte_served(self, app, client):
        resp = client.get("/dashboard/soporte")
        assert resp.status_code == 200
        assert b"Soporte" in resp.data or b"soporte" in resp.data.lower()

    def test_api_envios_returns_json(self, app, client, bot):
        bot.repository._table.return_value = "https://test.co/rest/v1/envios"
        bot.repository._request.return_value = [{"id": 1, "remitente": "Juan"}]
        resp = client.get("/api/envios")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1

    def test_api_system_stats(self, app, client, bot):
        bot.repository._table.return_value = "https://test.co/rest/v1/test"
        bot.repository._request.return_value = []
        resp = client.get("/api/system-stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "clientes" in data

    def test_api_logs_returns_list(self, app, client):
        resp = client.get("/api/logs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_api_dashboard_returns_stats(self, client, bot):
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
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "currier_bot"

    def test_api_earnings_returns_json(self, client, bot):
        bot.repository._table.return_value = "https://test.co/rest/v1/envios"
        bot.repository._request.return_value = []
        resp = client.get("/api/earnings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total" in data
        assert data["total"] == 0

    def test_api_finance_summary(self, app, client, bot):
        bot.repository._table.return_value = "https://test.co/rest/v1/test"
        bot.repository._request.return_value = []
        resp = client.get("/api/finance-summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "income_today" in data


class TestCORS:
    def test_cors_headers_present(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    def test_cors_on_post(self, client):
        resp = client.post("/webhook", json={"object": "not_whatsapp"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"
