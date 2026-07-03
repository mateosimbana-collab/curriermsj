import os

from dotenv import load_dotenv


load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = _env_bool("DEBUG", True)

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "CurrierMsj")
BOT_NAME = os.getenv("BOT_NAME", "Rex")
ROUTE_LABEL = os.getenv("ROUTE_LABEL", "EE.UU. -> Ecuador")
SUPPORT_HOURS = os.getenv("SUPPORT_HOURS", "Lunes a Sábado, 8:00 - 18:00")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "curriermsj_secret")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SUPABASE_TABLE_CLIENTES = "clientes"
SUPABASE_TABLE_ENVIOS = "envios"
SUPABASE_TABLE_ESTADO = "estado_usuario"
SUPABASE_TABLE_FAQ = "faq"
SUPABASE_TABLE_REPORTES = "reportes"

WELCOME_IMAGE_URL = os.getenv("WELCOME_IMAGE_URL", "")
URL_GOOGLE_SHEETS = os.getenv("URL_GOOGLE_SHEETS", "")

WHATSAPP_API_URL = "https://graph.facebook.com/v20.0"
