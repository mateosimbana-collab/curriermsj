import logging
import re
from datetime import datetime
from typing import Any, Callable

import config
from bot.messages import LINE, Buttons, MessageTemplates, build_quote_options
from domain.constants import (
    INSTRUCTIONS,
    PACKAGE_TYPES,
    REPORT_CATEGORIES,
    SHIPPING_SERVICES,
    Step,
    normalize_action,
    resolve_package_type,
    resolve_weight,
)
from domain.models import IncomingMessage
from services.supabase_repository import SupabaseRepository
from services.whatsapp_client import WhatsAppClient


logger = logging.getLogger(__name__)


class CourierBot:
    def __init__(self, repository: SupabaseRepository, whatsapp: WhatsAppClient) -> None:
        self.repository = repository
        self.whatsapp = whatsapp
        self.handlers: dict[str, Callable[[IncomingMessage, str, dict[str, Any]], None]] = {
            Step.WELCOME: self.handle_welcome,
            Step.WELCOME_REGISTER: self.handle_welcome_register,
            Step.WELCOME_APELLIDO: self.handle_welcome_apellido,
            Step.WELCOME_CIUDAD: self.handle_welcome_ciudad,
            Step.WELCOME_PHONE: self.handle_welcome_phone,
            Step.TRACKING_CODE: self.handle_tracking_code,
            Step.QUOTE_ORIGIN: self.handle_quote_origin,
            Step.QUOTE_DESTINATION: self.handle_quote_destination,
            Step.QUOTE_PACKAGE_TYPE: self.handle_quote_package_type,
            Step.QUOTE_WEIGHT: self.handle_quote_weight,
            Step.QUOTE_SERVICE: self.handle_quote_service,
            Step.QUOTE_SUMMARY: self.handle_quote_summary,
            Step.REPORT_TYPE: self.handle_report_type,
            Step.REPORT_DESCRIPTION: self.handle_report_description,
            Step.NEW_SHIPMENT_NAME: self.handle_new_shipment_name,
            Step.NEW_SHIPMENT_PHONE: self.handle_new_shipment_phone,
            Step.NEW_SHIPMENT_RECIPIENT: self.handle_new_shipment_recipient,
            Step.NEW_SHIPMENT_RECIPIENT_PHONE: self.handle_new_shipment_recipient_phone,
            Step.NEW_SHIPMENT_DESTINATION: self.handle_new_shipment_destination,
            Step.NEW_SHIPMENT_PACKAGE_TYPE: self.handle_new_shipment_package_type,
            Step.NEW_SHIPMENT_INSTRUCTIONS: self.handle_new_shipment_instructions,
            Step.NEW_SHIPMENT_CONFIRM: self.handle_new_shipment_confirm,
        }

    def process(self, event: IncomingMessage) -> None:
        state = self.repository.get_user_state(event.phone_number)
        if not state:
            client = self.repository.get_client(event.phone_number)
            if client:
                self.repository.create_user_state(event.phone_number, Step.MENU, {})
                self.send_menu(event.phone_number)
            else:
                self.repository.create_user_state(event.phone_number, Step.WELCOME, {})
                self.send_welcome(event.phone_number)
            return

        action = normalize_action(event.text)
        if action == "volver_menu":
            self.repository.reset_user_state(event.phone_number)
            self.send_menu(event.phone_number)
            return

        step = state.get("paso_actual") or Step.MENU
        data = self.repository.extract_temp_data(state)

        if step == Step.MENU:
            self.handle_menu(event, action, data)
            return

        handler = self.handlers.get(step)
        if not handler:
            logger.warning("Paso no reconocido '%s' para %s", step, event.phone_number)
            self.repository.reset_user_state(event.phone_number)
            self.send_menu(event.phone_number)
            return

        handler(event, action, data)

    def send_welcome(self, phone_number: str) -> None:
        if config.WELCOME_IMAGE_URL:
            self.whatsapp.send_image(phone_number, config.WELCOME_IMAGE_URL, "")
        self.whatsapp.send_buttons(
            phone_number,
            MessageTemplates.welcome(),
            Buttons.WELCOME,
            header="Bienvenido",
            footer="Estamos para servirte",
        )

    def handle_welcome(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        if action == "quiero_info":
            self.whatsapp.send_buttons(
                phone,
                MessageTemplates.welcome_info(),
                Buttons.WELCOME,
                header="CurrierMsj",
                footer="Elige qué hacer",
            )
            return

        if action == "iniciar_pedido":
            self.repository.update_user_state(phone, Step.WELCOME_REGISTER, {})
            self.whatsapp.send_buttons(
                phone,
                MessageTemplates.ask_welcome_name(),
                Buttons.BACK,
            )
            return

        self.repository.reset_user_state(phone)
        self.send_menu(phone)

    def handle_welcome_register(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        data["nombre"] = event.text.strip()
        self.repository.update_user_state(phone, Step.WELCOME_APELLIDO, data)
        self.whatsapp.send_buttons(
            phone,
            MessageTemplates.ask_welcome_apellido(),
            Buttons.BACK,
        )

    def handle_welcome_apellido(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        data["apellido"] = event.text.strip()
        self.repository.update_user_state(phone, Step.WELCOME_CIUDAD, data)
        self.whatsapp.send_buttons(
            phone,
            MessageTemplates.ask_welcome_ciudad(),
            Buttons.BACK,
        )

    def handle_welcome_ciudad(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        data["ciudad"] = event.text.strip()
        self.repository.update_user_state(phone, Step.WELCOME_PHONE, data)
        self.whatsapp.send_buttons(
            phone,
            MessageTemplates.ask_welcome_phone(),
            Buttons.BACK,
        )

    def handle_welcome_phone(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        data["telefono_contacto"] = event.text.strip() or event.phone_number
        self.repository.save_client(
            phone_number=phone,
            nombre=data.get("nombre", ""),
            apellido=data.get("apellido", ""),
            ciudad=data.get("ciudad", ""),
            telefono_contacto=data["telefono_contacto"],
        )
        if config.WELCOME_IMAGE_URL:
            self.whatsapp.send_image(phone, config.WELCOME_IMAGE_URL, "")
        self.repository.reset_user_state(phone)
        self.whatsapp.send_text(
            phone,
            MessageTemplates.welcome_complete(data.get("nombre", ""), data.get("apellido", "")),
        )
        self.send_menu(phone)

    def send_menu(self, phone_number: str) -> None:
        self.whatsapp.send_buttons(
            phone_number,
            MessageTemplates.menu(),
            Buttons.MENU_PRIMARY,
            header="CurrierMsj",
            footer="Atención 24/7",
        )
        self.whatsapp.send_buttons(
            phone_number,
            "También puedo ayudarte con soporte o volver al menú principal.",
            Buttons.MENU_SECONDARY,
            footer="Elige una opción",
        )

    def handle_menu(self, event: IncomingMessage, action: str, data: dict[str, Any]) -> None:
        phone = event.phone_number
        if action == "rastrear":
            self.repository.update_user_state(phone, Step.TRACKING_CODE, {})
            self.whatsapp.send_buttons(phone, MessageTemplates.ask_tracking(), Buttons.BACK)
            return

        if action == "cotizar":
            self.repository.update_user_state(phone, Step.QUOTE_ORIGIN, {})
            self.whatsapp.send_buttons(phone, MessageTemplates.ask_quote_origin(), Buttons.ORIGIN)
            return

        if action == "mis_envios":
            self.handle_shipments_list(phone)
            return

        if action == "reportar":
            self.repository.update_user_state(phone, Step.REPORT_TYPE, {})
            self.whatsapp.send_buttons(
                phone,
                MessageTemplates.report_categories(),
                Buttons.REPORT_TYPES,
                footer="Elige tu caso",
            )
            return

        if action == "agente":
            self.whatsapp.send_buttons(phone, MessageTemplates.agent(), Buttons.BACK)
            return

        if action in {"ver_ubicacion", "reagendar"}:
            self.whatsapp.send_buttons(phone, MessageTemplates.agent(), Buttons.BACK)
            return

        faq_response = self.repository.search_faq(event.text)
        if faq_response:
            self.whatsapp.send_text(phone, f"💬 *Respuesta rápida*\n━━━━━━━━━━━━━━━━━━\n{faq_response}")
        else:
            self.whatsapp.send_text(phone, MessageTemplates.unknown())
        self.send_menu(phone)

    def handle_tracking_code(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        code = self._normalize_tracking_code(event.text)
        if not code:
            self.whatsapp.send_buttons(
                event.phone_number,
                "❌ Formato incorrecto. Usa *CUR-00001* o solo el número.",
                Buttons.BACK,
            )
            return

        shipment = self.repository.get_shipment_by_tracking(code)
        if not shipment:
            self.whatsapp.send_buttons(
                event.phone_number,
                MessageTemplates.tracking_not_found(code),
                Buttons.BACK,
            )
            self.repository.update_user_state(event.phone_number, Step.MENU)
            return

        tracking_code = shipment.get("tracking_code") or f"CUR-{int(shipment['id']):05d}"
        card = MessageTemplates.tracking_card(shipment, tracking_code)
        image_url = shipment.get("imagen_url")
        if image_url:
            self.whatsapp.send_image(event.phone_number, image_url, card)
        else:
            self.whatsapp.send_text(event.phone_number, card)

        self.whatsapp.send_buttons(
            event.phone_number,
            "¿Qué quieres hacer ahora?",
            Buttons.AFTER_TRACKING,
        )
        self.repository.update_user_state(event.phone_number, Step.MENU)

    def handle_quote_origin(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        if action == "ubicacion_origen":
            self.whatsapp.send_text(event.phone_number, MessageTemplates.location_help())
            self.whatsapp.send_location_request(event.phone_number, "Comparte tu ubicacion actual")
            return

        if action == "escribir_origen":
            self.whatsapp.send_buttons(
                event.phone_number,
                "✏️ Escribe la dirección de origen en Estados Unidos.",
                Buttons.BACK,
            )
            return

        data["origen"] = self._location_or_text(event)
        self.repository.update_user_state(event.phone_number, Step.QUOTE_DESTINATION, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.ask_quote_destination(),
            Buttons.DESTINATION,
        )

    def handle_quote_destination(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        if action == "ubicacion_destino":
            self.whatsapp.send_text(event.phone_number, MessageTemplates.location_help())
            self.whatsapp.send_location_request(event.phone_number, "Comparte la ubicacion de destino")
            return

        if action == "escribir_destino":
            self.whatsapp.send_buttons(
                event.phone_number,
                "✏️ Escribe la ciudad o dirección de destino en Ecuador.",
                Buttons.BACK,
            )
            return

        data["destino"] = self._location_or_text(event)
        self.repository.update_user_state(event.phone_number, Step.QUOTE_PACKAGE_TYPE, data)
        self.whatsapp.send_list(
            event.phone_number,
            MessageTemplates.ask_package_type(),
            "Elegir paquete",
            MessageTemplates.package_type_sections(),
            footer="Más de 3 opciones usan lista de WhatsApp",
        )

    def handle_quote_package_type(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        value = action if action in PACKAGE_TYPES else event.text
        data["tipo_paquete"] = resolve_package_type(value)
        self.repository.update_user_state(event.phone_number, Step.QUOTE_WEIGHT, data)
        self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_weight(), Buttons.WEIGHTS)

    def handle_quote_weight(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        value = action if action.startswith("peso_") else event.text
        data["peso"] = resolve_weight(value)

        options = build_quote_options(data.get("tipo_paquete", ""), data.get("peso", ""))
        data["opciones_envio"] = options
        self.repository.update_user_state(event.phone_number, Step.QUOTE_SERVICE, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.quote_options(data, options),
            Buttons.SERVICES,
            footer="Valor por confirmar",
        )

    def handle_quote_service(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        service_id = self._service_id(event.text, action)
        options = data.get("opciones_envio") or build_quote_options(
            data.get("tipo_paquete", ""),
            data.get("peso", ""),
        )

        if service_id not in SHIPPING_SERVICES:
            self.whatsapp.send_buttons(
                event.phone_number,
                MessageTemplates.quote_options(data, options),
                Buttons.SERVICES,
            )
            return

        service = SHIPPING_SERVICES[service_id]
        data["servicio_envio"] = service["label"]
        data["entrega_estimada"] = service["eta"]
        data["cotizacion"] = None
        self.repository.update_user_state(event.phone_number, Step.QUOTE_SUMMARY, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.quote_summary(data),
            Buttons.CONFIRM_QUOTE,
        )

    def handle_quote_summary(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        if action != "confirmar_envio":
            self.repository.reset_user_state(event.phone_number)
            self.whatsapp.send_text(event.phone_number, "Cotización cancelada.")
            self.send_menu(event.phone_number)
            return

        client = self.repository.get_client(event.phone_number)
        if client:
            data["remitente"] = f"{client.get('nombre', '')} {client.get('apellido', '')}".strip()
            data["telefono_remitente"] = client.get("telefono_contacto") or event.phone_number

        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_NAME, data)

        if client and data.get("remitente"):
            self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_RECIPIENT, data)
            self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_recipient_name(), Buttons.BACK)
        else:
            self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_sender_name(), Buttons.BACK)

    def handle_shipments_list(self, phone_number: str) -> None:
        shipments = self.repository.get_shipments_by_phone(phone_number)
        self.whatsapp.send_text(phone_number, MessageTemplates.shipments_list(shipments))
        self.whatsapp.send_buttons(
            phone_number,
            "¿Qué quieres hacer ahora?",
            [
                {"id": "rastrear", "title": "📦 Rastrear"},
                {"id": "cotizar", "title": "🧾 Cotizar"},
                {"id": "volver_menu", "title": "🏠 Menú"},
            ],
        )
        self.repository.update_user_state(phone_number, Step.MENU)

    def handle_report_type(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        category_id = self._report_category_id(event.text, action)
        category = REPORT_CATEGORIES.get(category_id, event.text.strip() or "Otro")
        data["reporte_categoria"] = category
        self.repository.update_user_state(event.phone_number, Step.REPORT_DESCRIPTION, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.ask_report_description(category),
            Buttons.BACK,
        )

    def handle_report_description(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        category = data.get("reporte_categoria", "Otro")
        description = event.text.strip()
        tracking_code = self._extract_tracking_code(description)
        report_id = self.repository.save_report(
            event.phone_number,
            description,
            category=category,
            tracking_code=tracking_code,
        )
        self.repository.reset_user_state(event.phone_number)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.report_created(report_id, category, tracking_code),
            Buttons.AFTER_REPORT,
        )

    def handle_new_shipment_name(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["remitente"] = event.text.strip()
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_PHONE, data)
        self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_sender_phone(), Buttons.BACK)

    def handle_new_shipment_phone(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["telefono_remitente"] = event.text.strip() or event.phone_number
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_RECIPIENT, data)
        self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_recipient_name(), Buttons.BACK)

    def handle_new_shipment_recipient(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["destinatario"] = event.text.strip()
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_RECIPIENT_PHONE, data)
        self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_recipient_phone(), Buttons.BACK)

    def handle_new_shipment_recipient_phone(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["telefono_destinatario"] = event.text.strip()
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_DESTINATION, data)
        self.whatsapp.send_buttons(event.phone_number, MessageTemplates.ask_exact_destination(), Buttons.BACK)

    def handle_new_shipment_destination(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["direccion_destino"] = self._location_or_text(event)
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_INSTRUCTIONS, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.ask_instructions(),
            Buttons.INSTRUCTIONS,
        )

    def handle_new_shipment_package_type(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        value = action if action in PACKAGE_TYPES else event.text
        data["tipo_paquete"] = resolve_package_type(value)
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_INSTRUCTIONS, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.ask_instructions(),
            Buttons.INSTRUCTIONS,
        )

    def handle_new_shipment_instructions(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        data["instrucciones"] = INSTRUCTIONS.get(action, event.text.strip())
        self.repository.update_user_state(event.phone_number, Step.NEW_SHIPMENT_CONFIRM, data)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.shipment_summary(data),
            Buttons.CONFIRM_SHIPMENT,
        )

    def handle_new_shipment_confirm(
        self,
        event: IncomingMessage,
        action: str,
        data: dict[str, Any],
    ) -> None:
        if action != "si_confirmar":
            self.repository.reset_user_state(event.phone_number)
            self.whatsapp.send_text(event.phone_number, "❌ Envío cancelado.")
            self.send_menu(event.phone_number)
            return

        session = self.repository.get_user_state(event.phone_number)
        payload = self._shipment_payload(data)
        if session and session.get("cliente_id"):
            payload["cliente_id"] = session["cliente_id"]
        tracking_code = self.repository.save_shipment(payload)
        self.repository.reset_user_state(event.phone_number)
        self.whatsapp.send_buttons(
            event.phone_number,
            MessageTemplates.shipment_created(tracking_code, data),
            Buttons.AFTER_TRACKING,
        )

    def _shipment_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "cliente_id": data.get("cliente_id"),
            "remitente_nombre": data.get("remitente", ""),
            "remitente_telefono": data.get("telefono_remitente", ""),
            "remitente_pais": data.get("pais_origen", "Estados Unidos"),
            "destinatario_nombre": data.get("destinatario", ""),
            "destinatario_telefono": data.get("telefono_destinatario", ""),
            "destinatario_direccion": data.get("direccion_destino") or data.get("destino") or "",
            "contenido": data.get("tipo_paquete", ""),
            "peso_kg": data.get("peso"),
            "instrucciones": data.get("instrucciones"),
            "estado_actual": "recibido_en_usa",
        }

    @staticmethod
    def _location_or_text(event: IncomingMessage) -> str:
        if event.has_location:
            return f"Ubicación: {event.latitude}, {event.longitude}"
        return event.text.strip()

    @staticmethod
    def _normalize_tracking_code(text: str) -> str | None:
        raw = (text or "").strip().upper().replace("#", "")
        if raw.startswith("CUR-"):
            return raw
        if raw.isdigit():
            return f"CUR-{int(raw):05d}"
        match = re.search(r"CUR-\d+", raw)
        if match:
            value = match.group(0)
            try:
                return f"CUR-{int(value.replace('CUR-', '')):05d}"
            except ValueError:
                return value
        return None

    @staticmethod
    def _extract_tracking_code(text: str) -> str | None:
        match = re.search(r"CUR-\d+", (text or "").upper())
        if not match:
            return None
        try:
            return f"CUR-{int(match.group(0).replace('CUR-', '')):05d}"
        except ValueError:
            return match.group(0)

    @staticmethod
    def _service_id(raw_text: str, action: str) -> str:
        aliases = {
            "1": "servicio_express",
            "2": "servicio_estandar",
            "3": "servicio_economico",
        }
        return aliases.get((raw_text or "").strip().lower(), action)

    @staticmethod
    def _report_category_id(raw_text: str, action: str) -> str:
        aliases = {
            "1": "rep_danado",
            "2": "rep_no_llego",
            "3": "rep_incompleto",
        }
        return aliases.get((raw_text or "").strip().lower(), action)
