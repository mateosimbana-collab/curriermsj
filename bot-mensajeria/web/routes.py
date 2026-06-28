import logging
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request

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
