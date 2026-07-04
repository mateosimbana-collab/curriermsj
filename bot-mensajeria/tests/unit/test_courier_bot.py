from unittest.mock import MagicMock, patch

import pytest

from bot.courier_bot import CourierBot
from domain.constants import Step
from domain.models import IncomingMessage


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_user_state.return_value = None
    repo.get_client.return_value = None
    repo.extract_temp_data.return_value = {}
    return repo


@pytest.fixture
def mock_whatsapp():
    wa = MagicMock()
    wa.send_text.return_value = True
    wa.send_buttons.return_value = True
    wa.send_list.return_value = True
    wa.send_image.return_value = True
    wa.send_location_request.return_value = True
    return wa


@pytest.fixture
def bot(mock_repo, mock_whatsapp):
    return CourierBot(repository=mock_repo, whatsapp=mock_whatsapp)


@pytest.fixture
def text_event():
    return IncomingMessage(phone_number="593991234567", text="hola", message_type="text")


class TestCourierBotInit:
    def test_handlers_registered(self, bot):
        assert Step.WELCOME in bot.handlers
        assert Step.WELCOME_REGISTER in bot.handlers
        assert Step.WELCOME_APELLIDO in bot.handlers
        assert Step.WELCOME_CIUDAD in bot.handlers
        assert Step.WELCOME_PHONE in bot.handlers
        assert Step.TRACKING_CODE in bot.handlers
        assert Step.QUOTE_ORIGIN in bot.handlers
        assert Step.QUOTE_DESTINATION in bot.handlers
        assert Step.QUOTE_PACKAGE_TYPE in bot.handlers
        assert Step.QUOTE_WEIGHT in bot.handlers
        assert Step.QUOTE_SERVICE in bot.handlers
        assert Step.QUOTE_SUMMARY in bot.handlers
        assert Step.REPORT_TYPE in bot.handlers
        assert Step.REPORT_DESCRIPTION in bot.handlers
        assert Step.NEW_SHIPMENT_NAME in bot.handlers
        assert Step.NEW_SHIPMENT_PHONE in bot.handlers
        assert Step.NEW_SHIPMENT_RECIPIENT in bot.handlers
        assert Step.NEW_SHIPMENT_RECIPIENT_PHONE in bot.handlers
        assert Step.NEW_SHIPMENT_DESTINATION in bot.handlers
        assert Step.NEW_SHIPMENT_PACKAGE_TYPE in bot.handlers
        assert Step.NEW_SHIPMENT_INSTRUCTIONS in bot.handlers
        assert Step.NEW_SHIPMENT_CONFIRM in bot.handlers


class TestProcess:
    def test_new_user_creates_welcome_state(self, bot, mock_repo, mock_whatsapp, text_event):
        mock_repo.get_user_state.return_value = None
        mock_repo.get_client.return_value = None
        bot.process(text_event)
        mock_repo.create_user_state.assert_called_once()
        mock_whatsapp.send_buttons.assert_called_once()

    def test_existing_client_goes_to_menu(self, bot, mock_repo, mock_whatsapp, text_event):
        mock_repo.get_user_state.return_value = None
        mock_repo.get_client.return_value = {"phone_number": "593991234567", "nombre": "Juan"}
        bot.process(text_event)
        mock_repo.create_user_state.assert_called_once()
        args = mock_repo.create_user_state.call_args[0]
        assert args[1] == Step.MENU

    def test_existing_state_routes_to_handler(self, bot, mock_repo, mock_whatsapp, text_event):
        mock_repo.get_user_state.return_value = {
            "phone_number": "593991234567",
            "paso_actual": Step.TRACKING_CODE,
        }
        mock_handler = MagicMock()
        bot.handlers[Step.TRACKING_CODE] = mock_handler
        bot.process(text_event)
        mock_handler.assert_called_once()

    def test_volver_menu_resets(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="volver", message_type="text")
        mock_repo.get_user_state.return_value = {
            "phone_number": "593991234567",
            "paso_actual": Step.QUOTE_ORIGIN,
        }
        bot.process(event)
        mock_repo.reset_user_state.assert_called_once()

    def test_menu_step_calls_handle_menu(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="rastrear", message_type="text")
        mock_repo.get_user_state.return_value = {
            "phone_number": "593991234567",
            "paso_actual": Step.MENU,
        }
        with patch.object(bot, "handle_menu") as mock_handler:
            bot.process(event)
            mock_handler.assert_called_once()

    def test_unknown_step_resets_to_menu(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="x", message_type="text")
        mock_repo.get_user_state.return_value = {
            "phone_number": "593991234567",
            "paso_actual": "paso_inexistente",
        }
        bot.process(event)
        mock_repo.reset_user_state.assert_called_once()


class TestSendWelcome:
    def test_welcome_sends_buttons(self, bot, mock_whatsapp):
        bot.send_welcome("593991234567")
        assert mock_whatsapp.send_buttons.called

    def test_welcome_with_image(self, bot, mock_whatsapp):
        with patch("config.WELCOME_IMAGE_URL", "https://img.test/welcome.jpg"):
            bot.send_welcome("593991234567")
            mock_whatsapp.send_image.assert_called_once()


class TestHandleWelcome:
    def test_quiero_info(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="quiero_info", message_type="text")
        bot.handle_welcome(event, "quiero_info", {})
        mock_whatsapp.send_buttons.assert_called_once()

    def test_iniciar_pedido(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="iniciar_pedido", message_type="text")
        bot.handle_welcome(event, "iniciar_pedido", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.WELCOME_REGISTER


class TestHandleWelcomeRegister:
    def test_saves_name_and_asks_apellido(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Juan", message_type="text")
        bot.handle_welcome_register(event, "Juan", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.WELCOME_APELLIDO
        assert args[2]["nombre"] == "Juan"


class TestHandleWelcomeApellido:
    def test_saves_apellido_and_asks_ciudad(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Perez", message_type="text")
        data = {"nombre": "Juan"}
        bot.handle_welcome_apellido(event, "Perez", data)
        assert data["apellido"] == "Perez"
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.WELCOME_CIUDAD


class TestHandleWelcomeCiudad:
    def test_saves_ciudad_and_asks_phone(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Guayaquil", message_type="text")
        data = {"nombre": "Juan", "apellido": "Perez"}
        bot.handle_welcome_ciudad(event, "Guayaquil", data)
        assert data["ciudad"] == "Guayaquil"
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.WELCOME_PHONE


class TestHandleWelcomePhone:
    def test_completes_registration(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="0991234567", message_type="text")
        data = {"nombre": "Juan", "apellido": "Perez", "ciudad": "Gye"}
        bot.handle_welcome_phone(event, "0991234567", data)
        mock_repo.save_client.assert_called_once()
        mock_repo.reset_user_state.assert_called_once()
        assert mock_whatsapp.send_text.called

    def test_uses_phone_number_if_no_input(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="", message_type="text")
        data = {"nombre": "Juan"}
        bot.handle_welcome_phone(event, "", data)
        mock_repo.save_client.assert_called_once()
        args = mock_repo.save_client.call_args[1]
        assert args["telefono_contacto"] == "593991234567"


class TestSendMenu:
    def test_sends_two_button_messages(self, bot, mock_whatsapp):
        bot.send_menu("593991234567")
        assert mock_whatsapp.send_buttons.call_count == 2


class TestHandleMenu:
    def test_rastrear_updates_state(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="rastrear", message_type="text")
        bot.handle_menu(event, "rastrear", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.TRACKING_CODE

    def test_cotizar_starts_quote(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="cotizar", message_type="text")
        bot.handle_menu(event, "cotizar", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.QUOTE_ORIGIN

    def test_mis_envios_calls_list(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="mis_envios", message_type="text")
        with patch.object(bot, "handle_shipments_list") as mock_handler:
            bot.handle_menu(event, "mis_envios", {})
            mock_handler.assert_called_once_with("593991234567")

    def test_reportar_starts_report(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="reportar", message_type="text")
        bot.handle_menu(event, "reportar", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.REPORT_TYPE

    def test_agente_sends_agent_message(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="agente", message_type="text")
        bot.handle_menu(event, "agente", {})
        mock_whatsapp.send_buttons.assert_called_once()


class TestHandleTrackingCode:
    def test_invalid_format_asks_again(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="abc", message_type="text")
        bot.handle_tracking_code(event, "abc", {})
        mock_whatsapp.send_buttons.assert_called_once()

    def test_not_found_sends_not_found(self, bot, mock_repo, mock_whatsapp):
        mock_repo.get_shipment_by_tracking.return_value = None
        event = IncomingMessage(phone_number="593991234567", text="CUR-99999", message_type="text")
        bot.handle_tracking_code(event, "CUR-99999", {})
        mock_whatsapp.send_buttons.assert_called_once()

    def test_found_sends_card(self, bot, mock_repo, mock_whatsapp):
        mock_repo.get_shipment_by_tracking.return_value = {
            "id": 1, "estado": "pendiente", "remitente": "Juan", "destinatario": "Maria",
        }
        event = IncomingMessage(phone_number="593991234567", text="CUR-00001", message_type="text")
        bot.handle_tracking_code(event, "CUR-00001", {})
        assert mock_whatsapp.send_text.called or mock_whatsapp.send_image.called
        mock_whatsapp.send_buttons.assert_called_once()


class TestHandleQuoteOrigin:
    def test_ubicacion_origen(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="ubicacion_origen", message_type="text")
        bot.handle_quote_origin(event, "ubicacion_origen", {})
        mock_whatsapp.send_text.assert_called_once()
        mock_whatsapp.send_location_request.assert_called_once()

    def test_escribir_origen(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="escribir_origen", message_type="text")
        bot.handle_quote_origin(event, "escribir_origen", {})
        mock_whatsapp.send_buttons.assert_called_once()

    def test_text_saves_origin(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Miami, FL", message_type="text")
        data = {}
        bot.handle_quote_origin(event, "Miami, FL", data)
        assert data["origen"] == "Miami, FL"
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.QUOTE_DESTINATION


class TestHandleQuoteDestination:
    def test_text_saves_destination(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Quito", message_type="text")
        data = {"origen": "NY"}
        bot.handle_quote_destination(event, "Quito", data)
        assert data["destino"] == "Quito"
        mock_whatsapp.send_list.assert_called_once()


class TestHandleQuoteService:
    def test_invalid_service_retries(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="invalido", message_type="text")
        bot.handle_quote_service(event, "invalido", {"opciones_envio": {}})
        mock_whatsapp.send_buttons.assert_called_once()

    def test_valid_service_saves_and_shows_summary(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="1", message_type="text")
        bot.handle_quote_service(event, "1", {"opciones_envio": {}})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.QUOTE_SUMMARY


class TestHandleQuoteSummary:
    def test_cancel_returns_to_menu(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="volver_menu", message_type="text")
        bot.handle_quote_summary(event, "volver_menu", {})
        mock_repo.reset_user_state.assert_called_once()

    def test_confirm_starts_shipment(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="confirmar_envio", message_type="text")
        bot.handle_quote_summary(event, "confirmar_envio", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.NEW_SHIPMENT_NAME


class TestHandleReportType:
    def test_saves_category_and_asks_description(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="rep_danado", message_type="text")
        bot.handle_report_type(event, "rep_danado", {})
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.REPORT_DESCRIPTION


class TestHandleReportDescription:
    def test_saves_report_and_returns_to_menu(self, bot, mock_repo, mock_whatsapp):
        mock_repo.save_report.return_value = 1
        event = IncomingMessage(phone_number="593991234567", text="llego roto", message_type="text")
        bot.handle_report_description(event, "llego roto", {"reporte_categoria": "Danado"})
        mock_repo.save_report.assert_called_once()
        mock_repo.reset_user_state.assert_called_once()


class TestHandleNewShipmentName:
    def test_saves_name_and_asks_phone(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="Juan Perez", message_type="text")
        data = {}
        bot.handle_new_shipment_name(event, "Juan Perez", data)
        assert data["remitente"] == "Juan Perez"
        mock_repo.update_user_state.assert_called_once()
        args = mock_repo.update_user_state.call_args[0]
        assert args[1] == Step.NEW_SHIPMENT_PHONE


class TestHandleNewShipmentConfirm:
    def test_cancel_returns_to_menu(self, bot, mock_repo, mock_whatsapp):
        event = IncomingMessage(phone_number="593991234567", text="no_cancelar", message_type="text")
        bot.handle_new_shipment_confirm(event, "no_cancelar", {})
        mock_repo.reset_user_state.assert_called_once()

    def test_confirm_saves_shipment(self, bot, mock_repo, mock_whatsapp):
        mock_repo.save_shipment.return_value = 1
        event = IncomingMessage(phone_number="593991234567", text="si_confirmar", message_type="text")
        data = {"remitente": "Juan", "destinatario": "Maria"}
        bot.handle_new_shipment_confirm(event, "si_confirmar", data)
        mock_repo.save_shipment.assert_called_once()
        mock_repo.reset_user_state.assert_called_once()


class TestHelpers:
    def test_normalize_tracking_code_cur_format(self, bot):
        result = bot._normalize_tracking_code("CUR-00001")
        assert result == "CUR-00001"

    def test_normalize_tracking_code_digits_only(self, bot):
        result = bot._normalize_tracking_code("1")
        assert result == "CUR-00001"

    def test_normalize_tracking_code_invalid(self, bot):
        result = bot._normalize_tracking_code("abc")
        assert result is None

    def test_extract_tracking_code_found(self, bot):
        result = bot._extract_tracking_code("el codigo es CUR-00001")
        assert result == "CUR-00001"

    def test_extract_tracking_code_not_found(self, bot):
        result = bot._extract_tracking_code("no hay codigo aqui")
        assert result is None

    def test_service_id_by_number(self, bot):
        assert bot._service_id("1", "") == "servicio_express"
        assert bot._service_id("2", "") == "servicio_estandar"
        assert bot._service_id("3", "") == "servicio_economico"

    def test_service_id_by_action(self, bot):
        assert bot._service_id("texto", "servicio_express") == "servicio_express"

    def test_report_category_id_by_number(self, bot):
        assert bot._report_category_id("1", "") == "rep_danado"
        assert bot._report_category_id("2", "") == "rep_no_llego"
        assert bot._report_category_id("3", "") == "rep_incompleto"

    def test_location_or_text_text(self, bot):
        event = IncomingMessage(phone_number="593991234567", text="Miami, FL", message_type="text")
        assert bot._location_or_text(event) == "Miami, FL"

    def test_location_or_text_location(self, bot):
        event = IncomingMessage(
            phone_number="593991234567", text="", message_type="location",
            latitude=-0.23, longitude=-78.52,
        )
        result = bot._location_or_text(event)
        assert "Ubicación" in result or "Ubicacion" in result
        assert "-0.23" in result

    def test_shipment_payload_contains_required_keys(self, bot):
        data = {
            "remitente": "Juan", "telefono_remitente": "123",
            "destinatario": "Maria", "telefono_destinatario": "456",
            "origen": "NY", "destino": "UIO",
            "tipo_paquete": "Docs", "peso": "1kg",
            "instrucciones": "Fragil",
            "servicio_envio": "Express",
            "entrega_estimada": "24h",
        }
        payload = bot._shipment_payload(data)
        assert payload["remitente"] == "Juan"
        assert payload["destinatario"] == "Maria"
        assert payload["estado"] == "pendiente"
        assert payload["valor_cotizado"] is None
