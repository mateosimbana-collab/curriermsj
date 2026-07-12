# ruff: noqa: E402
import os
import sys
import logging

# Add old bot-mensajeria to path (now extends backend repo)
BOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bot-mensajeria")
sys.path.insert(0, BOT_DIR)

from flask import Blueprint, request
from bot.courier_bot import CourierBot
from services.whatsapp_client import WhatsAppClient
from services.supabase_repository import SupabaseRepository
from web.routes import WhatsAppWebhookParser
from backend.security import secrets_match, verify_meta_signature

logger = logging.getLogger(__name__)

webhook_bp = Blueprint("webhook", __name__)

_repo = None
_whatsapp = None
_bot = None


def _get_bot():
    global _repo, _whatsapp, _bot
    if _bot is None:
        _repo = SupabaseRepository()
        _whatsapp = WhatsAppClient()
        _bot = CourierBot(repository=_repo, whatsapp=_whatsapp)
        logger.info("WhatsApp bot initialized with unified repository")
    return _bot


@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
    if mode == "subscribe" and secrets_match(token, verify_token):
        return challenge or "", 200
    return "Forbidden", 403


@webhook_bp.route("/webhook", methods=["POST"])
def receive_message():
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = request.get_data(cache=True)
    if not verify_meta_signature(body, signature):
        return "Unauthorized", 401

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return "Bad Request", 400
    if payload.get("object") != "whatsapp_business_account":
        return "Not Found", 404
    entries = payload.get("entry") or []
    if any(
        change.get("value", {}).get("statuses")
        for entry in entries if isinstance(entry, dict)
        for change in (entry.get("changes") or []) if isinstance(change, dict)
    ):
        return "OK", 200
    try:
        bot = _get_bot()
        events = WhatsAppWebhookParser.parse(payload)
        for event in events:
            bot.process(event)
    except Exception:
        logger.exception("Webhook processing failed")
        return "Internal Server Error", 500
    return "OK", 200
