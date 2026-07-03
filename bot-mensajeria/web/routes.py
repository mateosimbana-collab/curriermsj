import logging
import os
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

import config
from bot.courier_bot import CourierBot
from domain.models import IncomingMessage


logger = logging.getLogger(__name__)


class WhatsAppWebhookParser:
    @staticmethod
    def parse(payload: dict[str, Any]) -> list[IncomingMessage]:
        events: list[IncomingMessage] = []

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    event = WhatsAppWebhookParser._parse_message(message)
                    if event:
                        events.append(event)

        return events

    @staticmethod
    def _parse_message(message: dict[str, Any]) -> IncomingMessage | None:
        phone_number = message.get("from")
        if not phone_number:
            return None

        message_type = message.get("type", "text")
        if message_type == "text":
            return IncomingMessage(
                phone_number=phone_number,
                text=message.get("text", {}).get("body", ""),
                message_type="text",
                raw=message,
            )

        if message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                reply = interactive.get("button_reply", {})
                return IncomingMessage(
                    phone_number=phone_number,
                    text=reply.get("id") or reply.get("title", ""),
                    message_type="interactive_button",
                    raw=message,
                )
            if interactive.get("type") == "list_reply":
                reply = interactive.get("list_reply", {})
                return IncomingMessage(
                    phone_number=phone_number,
                    text=reply.get("id") or reply.get("title", ""),
                    message_type="interactive_list",
                    raw=message,
                )

        if message_type == "location":
            location = message.get("location", {})
            return IncomingMessage(
                phone_number=phone_number,
                text="ubicacion_recibida",
                message_type="location",
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                raw=message,
            )

        if message_type == "reaction":
            reaction = message.get("reaction", {})
            return IncomingMessage(
                phone_number=phone_number,
                text=f"Reacción: {reaction.get('emoji', '')}",
                message_type="reaction",
                raw=message,
            )

        return IncomingMessage(
            phone_number=phone_number,
            text="",
            message_type=message_type,
            raw=message,
        )


def create_app(bot: CourierBot) -> Flask:
    app = Flask(__name__)

    @app.get("/webhook")
    def verify_webhook():
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == config.WEBHOOK_VERIFY_TOKEN:
            logger.info("Webhook verificado correctamente")
            return challenge or "", 200

        logger.warning("Intento de verificación fallido")
        return "Forbidden", 403

    @app.post("/webhook")
    def receive_message():
        payload = request.get_json(silent=True) or {}
        if payload.get("object") != "whatsapp_business_account":
            return "Not Found", 404

        if payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"):
            return "OK", 200

        try:
            events = WhatsAppWebhookParser.parse(payload)
            logger.info("Webhook recibido: %d mensajes", len(events))
            for event in events:
                logger.info("Procesando mensaje de %s: %s", event.phone_number, event.text[:50])
                try:
                    bot.process(event)
                except Exception as exc:
                    logger.exception("Error procesando mensaje de %s: %s", event.phone_number, exc)
        except Exception as exc:
            logger.exception("Error parseando webhook: %s", exc)

        return "OK", 200

    @app.get("/api/dashboard")
    def api_dashboard():
        stats = bot.repository.get_dashboard_stats()

        try:
            import requests as _r
            wa_resp = _r.get(
                f"{config.WHATSAPP_API_URL}/{config.PHONE_NUMBER_ID}",
                headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
                timeout=5,
            )
            whatsapp_ok = 200 <= wa_resp.status_code < 300
        except Exception:
            whatsapp_ok = False

        try:
            import httpx as _hx
            su_resp = _hx.get(
                f"{config.SUPABASE_URL}/rest/v1/envios?select=id&limit=1",
                headers={
                    "apikey": config.SUPABASE_KEY,
                    "Authorization": f"Bearer {config.SUPABASE_KEY}",
                },
                timeout=5,
            )
            supabase_ok = su_resp.status_code < 300
        except Exception:
            supabase_ok = False

        return jsonify({
            "status": "ok",
            "service": "currier_bot",
            "time": datetime.now().isoformat(),
            "total_shipments": stats["total_shipments"],
            "shipments_today": stats["shipments_today"],
            "active_users": stats["active_users"],
            "total_reports": stats["total_reports"],
            "open_reports": stats["open_reports"],
            "recent_shipments": stats["recent_shipments"],
            "active_sessions": stats["active_sessions"],
            "services": {
                "bot": True,
                "whatsapp": whatsapp_ok,
                "supabase": supabase_ok,
            },
        }), 200

    @app.get("/dashboard")
    def dashboard():
        dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard")
        return send_from_directory(dashboard_dir, "index.html")

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "currier_bot",
                "time": datetime.now().isoformat(),
            }
        ), 200

    return app
