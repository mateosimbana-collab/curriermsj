import importlib
import os

import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)
    for var in [
        "WHATSAPP_TOKEN", "PHONE_NUMBER_ID", "WEBHOOK_VERIFY_TOKEN",
        "SUPABASE_URL", "SUPABASE_KEY", "URL_GOOGLE_SHEETS",
        "HOST", "PORT", "DEBUG", "BUSINESS_NAME", "BOT_NAME",
        "ROUTE_LABEL", "SUPPORT_HOURS", "WELCOME_IMAGE_URL",
    ]:
        monkeypatch.delenv(var, raising=False)


def reload_config():
    import config
    importlib.reload(config)
    return config


class TestConfigDefaults:
    def test_host_default(self, clean_env):
        cfg = reload_config()
        assert cfg.HOST == "0.0.0.0"

    def test_port_default(self, clean_env):
        cfg = reload_config()
        assert cfg.PORT == 5000

    def test_debug_default_true(self, clean_env):
        cfg = reload_config()
        assert cfg.DEBUG is True

    def test_business_name_default(self, clean_env):
        cfg = reload_config()
        assert cfg.BUSINESS_NAME == "CurrierMsj"

    def test_bot_name_default(self, clean_env):
        cfg = reload_config()
        assert cfg.BOT_NAME == "Rex"

    def test_route_label_default(self, clean_env):
        cfg = reload_config()
        assert cfg.ROUTE_LABEL == "EE.UU. -> Ecuador"

    def test_support_hours_default(self, clean_env):
        cfg = reload_config()
        assert cfg.SUPPORT_HOURS == "Lunes a Sábado, 8:00 - 18:00"

    def test_webhook_verify_token_default(self, clean_env):
        cfg = reload_config()
        assert cfg.WEBHOOK_VERIFY_TOKEN == "curriermsj_secret"

    def test_whatsapp_token_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.WHATSAPP_TOKEN == ""

    def test_phone_number_id_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.PHONE_NUMBER_ID == ""

    def test_supabase_url_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.SUPABASE_URL == ""

    def test_supabase_key_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.SUPABASE_KEY == ""

    def test_welcome_image_url_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.WELCOME_IMAGE_URL == ""

    def test_url_google_sheets_default_empty(self, clean_env):
        cfg = reload_config()
        assert cfg.URL_GOOGLE_SHEETS == ""

    def test_whatsapp_api_url_fixed(self, clean_env):
        cfg = reload_config()
        assert cfg.WHATSAPP_API_URL == "https://graph.facebook.com/v20.0"

    def test_table_names(self, clean_env):
        cfg = reload_config()
        assert cfg.SUPABASE_TABLE_ENVIOS == "envios"
        assert cfg.SUPABASE_TABLE_ESTADO == "estado_usuario"
        assert cfg.SUPABASE_TABLE_CLIENTES == "clientes"
        assert cfg.SUPABASE_TABLE_FAQ == "faq"
        assert cfg.SUPABASE_TABLE_REPORTES == "reportes"


class TestConfigEnvOverrides:
    def test_all_vars_from_env(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_TOKEN", "wa_test")
        monkeypatch.setenv("PHONE_NUMBER_ID", "123456")
        monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "my_verify")
        monkeypatch.setenv("SUPABASE_URL", "https://test.co")
        monkeypatch.setenv("SUPABASE_KEY", "key_test")
        monkeypatch.setenv("HOST", "127.0.0.1")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("BUSINESS_NAME", "TestCorp")
        monkeypatch.setenv("BOT_NAME", "TestBot")
        monkeypatch.setenv("ROUTE_LABEL", "Test Route")
        monkeypatch.setenv("SUPPORT_HOURS", "9-5")
        monkeypatch.setenv("WELCOME_IMAGE_URL", "https://img.test/1.jpg")
        monkeypatch.setenv("URL_GOOGLE_SHEETS", "https://sheets.test")

        cfg = reload_config()
        assert cfg.WHATSAPP_TOKEN == "wa_test"
        assert cfg.PHONE_NUMBER_ID == "123456"
        assert cfg.WEBHOOK_VERIFY_TOKEN == "my_verify"
        assert cfg.SUPABASE_URL == "https://test.co"
        assert cfg.SUPABASE_KEY == "key_test"
        assert cfg.HOST == "127.0.0.1"
        assert cfg.PORT == 9000
        assert cfg.DEBUG is False
        assert cfg.BUSINESS_NAME == "TestCorp"
        assert cfg.BOT_NAME == "TestBot"
        assert cfg.ROUTE_LABEL == "Test Route"
        assert cfg.SUPPORT_HOURS == "9-5"
        assert cfg.WELCOME_IMAGE_URL == "https://img.test/1.jpg"
        assert cfg.URL_GOOGLE_SHEETS == "https://sheets.test"


class TestConfigDebugVariants:
    @pytest.mark.parametrize("val,expected", [
        ("true", True), ("True", True), ("1", True), ("yes", True), ("on", True),
        ("false", False), ("False", False), ("0", False), ("no", False), ("off", False),
        ("", True),
    ])
    def test_debug_variants(self, monkeypatch, val, expected):
        monkeypatch.setenv("DEBUG", val)
        cfg = reload_config()
        assert cfg.DEBUG is expected


class TestConfigPortVariants:
    @pytest.mark.parametrize("val,expected", [
        ("5000", 5000), ("8080", 8080), ("80", 80),
    ])
    def test_port_variants(self, monkeypatch, val, expected):
        monkeypatch.setenv("PORT", val)
        cfg = reload_config()
        assert cfg.PORT == expected

    def test_port_invalid_defaults(self, monkeypatch):
        monkeypatch.setenv("PORT", "abc")
        with pytest.raises(ValueError):
            reload_config()
