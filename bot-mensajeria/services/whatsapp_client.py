import logging
from typing import Any, Optional

import requests

import config


logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(
        self,
        token: str = config.WHATSAPP_TOKEN,
        phone_number_id: str = config.PHONE_NUMBER_ID,
        api_url: str = config.WHATSAPP_API_URL,
    ) -> None:
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_url = api_url.rstrip("/")

    @property
    def messages_url(self) -> str:
        return f"{self.api_url}/{self.phone_number_id}/messages"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def send_text(self, to: str, text: str) -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        return self._post(payload, f"texto a {to}")

    def send_buttons(
        self,
        to: str,
        text: str,
        buttons: list[dict[str, str]],
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> bool:
        interactive: dict[str, Any] = {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": button["id"],
                            "title": self._button_title(button["title"]),
                        },
                    }
                    for button in buttons[:3]
                ]
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header[:60]}
        if footer:
            interactive["footer"] = {"text": footer[:60]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        return self._post(payload, f"botones a {to}")

    def send_list(
        self,
        to: str,
        text: str,
        button_text: str,
        sections: list[dict[str, Any]],
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> bool:
        interactive: dict[str, Any] = {
            "type": "list",
            "body": {"text": text},
            "action": {
                "button": button_text[:20],
                "sections": sections,
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header[:60]}
        if footer:
            interactive["footer"] = {"text": footer[:60]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        return self._post(payload, f"lista a {to}")

    def send_image(self, to: str, image_url: str, caption: str = "") -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption[:1024],
            },
        }
        return self._post(payload, f"imagen a {to}")

    def _post(self, payload: dict[str, Any], description: str) -> bool:
        if not self.token or not self.phone_number_id:
            logger.error("WhatsApp no configurado: faltan WHATSAPP_TOKEN o PHONE_NUMBER_ID")
            return False

        try:
            response = requests.post(
                self.messages_url,
                headers=self.headers,
                json=payload,
                timeout=10,
            )
            logger.info("WhatsApp %s: %s", description, response.status_code)
            if response.status_code >= 400:
                logger.warning("Error WhatsApp %s: %s", response.status_code, response.text[:500])
            return 200 <= response.status_code < 300
        except requests.RequestException as exc:
            logger.error("Error enviando %s: %s", description, exc)
            return False

    @staticmethod
    def _button_title(title: str) -> str:
        title = title.strip()
        return title[:20] if len(title) > 20 else title
