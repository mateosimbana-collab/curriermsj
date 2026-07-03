from unittest.mock import MagicMock, patch

import pytest
import requests

from services.whatsapp_client import WhatsAppClient


@pytest.fixture
def client():
    return WhatsAppClient(
        token="test_token_123",
        phone_number_id="123456789",
        api_url="https://graph.facebook.com/v20.0",
    )


@pytest.fixture
def client_no_config():
    return WhatsAppClient(token="", phone_number_id="")


class TestInit:
    def test_messages_url(self, client):
        assert client.messages_url == "https://graph.facebook.com/v20.0/123456789/messages"

    def test_headers(self, client):
        h = client.headers
        assert h["Authorization"] == "Bearer test_token_123"
        assert h["Content-Type"] == "application/json"

    def test_no_config_returns_false_on_send(self, client_no_config):
        assert client_no_config.send_text("593991234567", "Hola") is False


class TestSendText:
    def test_builds_payload(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            result = client.send_text("593991234567", "Hola mundo")
            assert result is True
            mock_post.assert_called_once()
            payload = mock_post.call_args[0][0]
            assert payload["to"] == "593991234567"
            assert payload["type"] == "text"
            assert payload["text"]["body"] == "Hola mundo"

    def test_empty_text(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_text("593991234567", "")
            payload = mock_post.call_args[0][0]
            assert payload["text"]["body"] == ""


class TestSendButtons:
    def test_builds_interactive_payload(self, client):
        buttons = [{"id": "opt1", "title": "Opcion 1"}, {"id": "opt2", "title": "Opcion 2"}]
        with patch.object(client, "_post", return_value=True) as mock_post:
            result = client.send_buttons("593991234567", "Elige:", buttons)
            assert result is True
            payload = mock_post.call_args[0][0]
            assert payload["type"] == "interactive"
            assert payload["interactive"]["type"] == "button"
            assert len(payload["interactive"]["action"]["buttons"]) == 2

    def test_max_three_buttons(self, client):
        buttons = [{"id": f"b{i}", "title": f"B{i}"} for i in range(5)]
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_buttons("593991234567", "texto", buttons)
            payload = mock_post.call_args[0][0]
            assert len(payload["interactive"]["action"]["buttons"]) == 3

    def test_with_header(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_buttons("593991234567", "texto", [], header="Titulo")
            payload = mock_post.call_args[0][0]
            assert payload["interactive"]["header"]["text"] == "Titulo"

    def test_with_footer(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_buttons("593991234567", "texto", [], footer="Footer")
            payload = mock_post.call_args[0][0]
            assert payload["interactive"]["footer"]["text"] == "Footer"

    def test_long_header_truncated(self, client):
        long_header = "H" * 100
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_buttons("593991234567", "texto", [], header=long_header)
            payload = mock_post.call_args[0][0]
            assert len(payload["interactive"]["header"]["text"]) == 60


class TestSendList:
    def test_builds_list_payload(self, client):
        sections = [{"title": "Sec1", "rows": [{"id": "r1", "title": "Row1"}]}]
        with patch.object(client, "_post", return_value=True) as mock_post:
            result = client.send_list("593991234567", "texto", "Ver", sections)
            assert result is True
            payload = mock_post.call_args[0][0]
            assert payload["interactive"]["type"] == "list"
            assert payload["interactive"]["action"]["button"] == "Ver"

    def test_with_header_and_footer(self, client):
        sections = [{"title": "Sec1", "rows": [{"id": "r1", "title": "Row1"}]}]
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_list("593991234567", "texto", "Btn", sections, header="H", footer="F")
            payload = mock_post.call_args[0][0]
            assert payload["interactive"]["header"]["text"] == "H"
            assert payload["interactive"]["footer"]["text"] == "F"


class TestSendLocationRequest:
    def test_builds_payload(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            result = client.send_location_request("593991234567", "Envia tu ubicacion")
            assert result is True
            payload = mock_post.call_args[0][0]
            assert payload["interactive"]["type"] == "location_request_message"
            assert payload["interactive"]["action"]["name"] == "send_location"


class TestSendImage:
    def test_builds_image_payload(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            result = client.send_image("593991234567", "https://img.test/photo.jpg", "Mi foto")
            assert result is True
            payload = mock_post.call_args[0][0]
            assert payload["type"] == "image"
            assert payload["image"]["link"] == "https://img.test/photo.jpg"
            assert payload["image"]["caption"] == "Mi foto"

    def test_without_caption(self, client):
        with patch.object(client, "_post", return_value=True) as mock_post:
            client.send_image("593991234567", "https://img.test/photo.jpg")
            payload = mock_post.call_args[0][0]
            assert payload["image"]["caption"] == ""


class TestPost:
    def test_successful_post_returns_true(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("requests.post", return_value=mock_response):
            result = client._post({"test": "payload"}, "test")
            assert result is True

    def test_failed_post_returns_false(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error":"bad request"}'
        with patch("requests.post", return_value=mock_response):
            result = client._post({"test": "payload"}, "test")
            assert result is False

    def test_http_error_returns_false(self, client):
        with patch("requests.post", side_effect=requests.exceptions.RequestException("Connection error")):
            result = client._post({"test": "payload"}, "test")
            assert result is False

    def test_missing_config_returns_false(self, client_no_config):
        result = client_no_config._post({"test": "payload"}, "test")
        assert result is False


class TestButtonTitle:
    def test_short_title_unchanged(self, client):
        assert client._button_title("Info") == "Info"

    def test_long_title_truncated(self, client):
        long_title = "A" * 30
        result = client._button_title(long_title)
        assert len(result) == 20

    def test_title_stripped(self, client):
        assert client._button_title("  Hola  ") == "Hola"
