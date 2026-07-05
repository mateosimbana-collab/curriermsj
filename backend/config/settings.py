import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET", "curriermsj-secret-change-in-prod")
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1238571072668582")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_API_VERSION = "v20.0"
    WHATSAPP_BASE_URL = "https://graph.facebook.com/v20.0"
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
