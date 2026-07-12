# ruff: noqa: E402
import logging
import sys
from pathlib import Path

# Running this file directly requires the repository root before shared imports.
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import config
from bot.courier_bot import CourierBot
from services.supabase_repository import SupabaseRepository
from services.whatsapp_client import WhatsAppClient
from web.routes import create_app


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


repository = SupabaseRepository()
whatsapp = WhatsAppClient()
bot = CourierBot(repository=repository, whatsapp=whatsapp)
app = create_app(bot)


if __name__ == "__main__":
    logger.info("CurrierMsj iniciado en puerto %s", config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
