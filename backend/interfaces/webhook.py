import os
import sys
import logging

# Add old bot-mensajeria to path
BOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bot-mensajeria")
sys.path.insert(0, BOT_DIR)

from flask import Blueprint, request
from bot.courier_bot import CourierBot
from services.whatsapp_client import WhatsAppClient
from services.supabase_repository import SupabaseRepository as OldSupabaseRepo
from web.routes import WhatsAppWebhookParser

logger = logging.getLogger(__name__)

webhook_bp = Blueprint("webhook", __name__)

# Initialize bot with old repo (still works with existing tables)
_repo = None
_whatsapp = None
_bot = None


def _get_bot():
    global _repo, _whatsapp, _bot
    if _bot is None:
        _repo = OldSupabaseRepo()
        _whatsapp = WhatsAppClient()
        _bot = CourierBot(repository=_repo, whatsapp=_whatsapp)
        logger.info("WhatsApp bot initialized")
    return _bot


@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "curriermsj_secret")
    if mode == "subscribe" and token == verify_token:
        return challenge or "", 200
    return "Forbidden", 403


@webhook_bp.route("/webhook", methods=["POST"])
def receive_message():
    payload = request.get_json(silent=True) or {}
    if payload.get("object") != "whatsapp_business_account":
        return "Not Found", 404
    # Skip status updates
    if payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"):
        return "OK", 200
    try:
        bot = _get_bot()
        events = WhatsAppWebhookParser.parse(payload)
        for event in events:
            bot.process(event)
    except Exception as e:
        logger.error("Webhook error: %s", e)
    return "OK", 200
