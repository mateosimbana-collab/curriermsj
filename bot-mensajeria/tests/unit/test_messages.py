from bot.messages import Buttons, LINE, MessageTemplates, build_quote_options


class TestLine:
    def test_line_length(self):
        assert len(LINE) > 10
        assert "-" in LINE


class TestButtons:
    def test_welcome_has_two(self):
        assert len(Buttons.WELCOME) == 2
        assert Buttons.WELCOME[0]["id"] == "quiero_info"
        assert Buttons.WELCOME[1]["id"] == "iniciar_pedido"

    def test_welcome_titles(self):
        titles = [b["title"] for b in Buttons.WELCOME]
        assert "Info" in titles
        assert "Iniciar pedido" in titles

    def test_menu_primary_has_three(self):
        assert len(Buttons.MENU_PRIMARY) == 3
        assert Buttons.MENU_PRIMARY[0]["id"] == "rastrear"
        assert Buttons.MENU_PRIMARY[1]["id"] == "cotizar"
        assert Buttons.MENU_PRIMARY[2]["id"] == "mis_envios"

    def test_menu_secondary_has_three(self):
        assert len(Buttons.MENU_SECONDARY) == 3
        assert Buttons.MENU_SECONDARY[0]["id"] == "reportar"
        assert Buttons.MENU_SECONDARY[1]["id"] == "agente"
        assert Buttons.MENU_SECONDARY[2]["id"] == "volver_menu"

    def test_back_button(self):
        assert len(Buttons.BACK) == 1
        assert Buttons.BACK[0]["id"] == "volver_menu"

    def test_origin_buttons(self):
        assert len(Buttons.ORIGIN) == 3
        assert Buttons.ORIGIN[0]["id"] == "ubicacion_origen"
        assert Buttons.ORIGIN[1]["id"] == "escribir_origen"

    def test_destination_buttons(self):
        assert len(Buttons.DESTINATION) == 3
        assert Buttons.DESTINATION[0]["id"] == "ubicacion_destino"
        assert Buttons.DESTINATION[1]["id"] == "escribir_destino"

    def test_weights_buttons(self):
        assert len(Buttons.WEIGHTS) == 3
        assert Buttons.WEIGHTS[0]["id"] == "peso_ligero"
        assert Buttons.WEIGHTS[1]["id"] == "peso_medio"
        assert Buttons.WEIGHTS[2]["id"] == "peso_pesado"

    def test_weights_titles(self):
        titles = [b["title"] for b in Buttons.WEIGHTS]
        assert "Menos 1 kg" in titles
        assert "1 - 5 kg" in titles
        assert "Mas 5 kg" in titles

    def test_services_buttons(self):
        assert len(Buttons.SERVICES) == 3
        assert Buttons.SERVICES[0]["id"] == "servicio_express"
        assert Buttons.SERVICES[1]["id"] == "servicio_estandar"
        assert Buttons.SERVICES[2]["id"] == "servicio_economico"

    def test_confirm_quote(self):
        assert len(Buttons.CONFIRM_QUOTE) == 2
        assert Buttons.CONFIRM_QUOTE[0]["id"] == "confirmar_envio"

    def test_confirm_shipment(self):
        assert len(Buttons.CONFIRM_SHIPMENT) == 2
        assert Buttons.CONFIRM_SHIPMENT[0]["id"] == "si_confirmar"
        assert Buttons.CONFIRM_SHIPMENT[1]["id"] == "no_cancelar"

    def test_instructions_buttons(self):
        assert len(Buttons.INSTRUCTIONS) == 3
        assert Buttons.INSTRUCTIONS[0]["id"] == "inst_fragil"
        assert Buttons.INSTRUCTIONS[1]["id"] == "inst_urgente"
        assert Buttons.INSTRUCTIONS[2]["id"] == "inst_ninguna"

    def test_report_types(self):
        assert len(Buttons.REPORT_TYPES) == 3
        assert Buttons.REPORT_TYPES[0]["id"] == "rep_danado"
        assert Buttons.REPORT_TYPES[1]["id"] == "rep_no_llego"
        assert Buttons.REPORT_TYPES[2]["id"] == "rep_incompleto"

    def test_after_tracking(self):
        assert len(Buttons.AFTER_TRACKING) == 3

    def test_after_report(self):
        assert len(Buttons.AFTER_REPORT) == 2


class TestMessageTemplates:
    def test_welcome_has_business_name(self):
        text = MessageTemplates.welcome()
        assert "CURRIERMSJ" in text or "CurrierMsj" in text
        assert "Rex" in text

    def test_welcome_has_route(self):
        text = MessageTemplates.welcome()
        assert "Ecuador" in text

    def test_welcome_has_button_hint(self):
        text = MessageTemplates.welcome()
        assert "boton" in text.lower()

    def test_welcome_info_has_service_info(self):
        text = MessageTemplates.welcome_info()
        assert "Express" in text
        assert "Estandar" in text
        assert "Economico" in text
        assert "CUR-" in text
        assert "RASTREO" in text

    def test_ask_welcome_name(self):
        text = MessageTemplates.ask_welcome_name()
        assert "REGISTRO" in text
        assert "nombre" in text.lower()

    def test_ask_welcome_apellido(self):
        text = MessageTemplates.ask_welcome_apellido()
        assert "apellido" in text.lower()

    def test_ask_welcome_ciudad(self):
        text = MessageTemplates.ask_welcome_ciudad()
        assert "ciudad" in text.lower()

    def test_ask_welcome_phone(self):
        text = MessageTemplates.ask_welcome_phone()
        assert "telefono" in text.lower()

    def test_welcome_complete_with_name_only(self):
        text = MessageTemplates.welcome_complete("Juan")
        assert "Juan" in text
        assert "REGISTRO COMPLETADO" in text

    def test_welcome_complete_with_full_name(self):
        text = MessageTemplates.welcome_complete("Juan", "Perez")
        assert "Juan" in text
        assert "Perez" in text

    def test_welcome_complete_empty_name(self):
        text = MessageTemplates.welcome_complete("")
        assert "registrado" in text.lower()

    def test_menu_has_options(self):
        text = MessageTemplates.menu()
        assert "CURRIERMSJ" in text or "CurrierMsj" in text
        assert "Rastrear" in text or "rastrear" in text
        assert "1." in text

    def test_ask_tracking(self):
        text = MessageTemplates.ask_tracking()
        assert "RASTREAR" in text
        assert "CUR-" in text

    def test_tracking_card_basic(self):
        envio = {"estado": "pendiente", "remitente": "Juan", "destinatario": "Maria"}
        card = MessageTemplates.tracking_card(envio, "CUR-00001")
        assert "CUR-00001" in card
        assert "Maria" in card
        assert "[...]" in card

    def test_tracking_card_full(self):
        envio = {
            "estado": "en_transito",
            "remitente": "Juan",
            "destinatario": "Maria",
            "direccion_destino": "Quito",
            "peso": "1 kg",
            "servicio_envio": "Express",
            "entrega_estimada": "2 dias",
        }
        card = MessageTemplates.tracking_card(envio, "CUR-00002")
        assert "CUR-00002" in card
        assert "Quito" in card
        assert "Express" in card

    def test_tracking_card_delivered(self):
        envio = {"estado": "entregado", "remitente": "A", "destinatario": "B"}
        card = MessageTemplates.tracking_card(envio, "CUR-00003")
        assert "[OK]" in card
        assert "Entregado" in card or "entregado" in card

    def test_tracking_not_found(self):
        text = MessageTemplates.tracking_not_found("CUR-99999")
        assert "CUR-99999" in text
        assert "NO ENCONTRE" in text

    def test_ask_quote_origin(self):
        text = MessageTemplates.ask_quote_origin()
        assert "CONSULTAR" in text
        assert "Estados Unidos" in text

    def test_ask_quote_destination(self):
        text = MessageTemplates.ask_quote_destination()
        assert "DESTINO" in text
        assert "Ecuador" in text

    def test_ask_package_type(self):
        text = MessageTemplates.ask_package_type()
        assert "TIPO" in text
        assert "PAQUETE" in text

    def test_package_type_sections(self):
        sections = MessageTemplates.package_type_sections()
        assert len(sections) == 1
        rows = sections[0]["rows"]
        assert len(rows) == 4
        assert rows[0]["id"] == "tipo_documento"
        assert rows[-1]["id"] == "tipo_grande"

    def test_ask_weight(self):
        text = MessageTemplates.ask_weight()
        assert "PESO" in text

    def test_quote_options_empty(self):
        data = {"tipo_paquete": "Documentos", "peso": "< 1 kg"}
        result = MessageTemplates.quote_options(data, {})
        assert isinstance(result, str)
        assert len(result) > 20

    def test_quote_options_with_services(self):
        data = {"origen": "NY", "destino": "UIO", "tipo_paquete": "Docs", "peso": "1kg"}
        options = {
            "servicio_express": {"label": "Express 24h", "eta": "24h"},
            "servicio_estandar": {"label": "Estandar 3d", "eta": "3d"},
        }
        result = MessageTemplates.quote_options(data, options)
        assert "Express 24-48h" in result
        assert "NY" in result

    def test_quote_summary_all_fields(self):
        data = {
            "origen": "New York",
            "destino": "Quito",
            "tipo_paquete": "Documentos",
            "peso": "< 1 kg",
            "servicio_envio": "Express 24-48h",
            "entrega_estimada": "24 a 48 horas",
        }
        summary = MessageTemplates.quote_summary(data)
        assert "New York" in summary
        assert "Quito" in summary
        assert "Documentos" in summary

    def test_quote_request_is_explicitly_manual(self):
        text = MessageTemplates.quote_request_created(
            12,
            {"destino": "Cuenca", "tipo_paquete": "Ropa", "peso": "1 - 5 kg"},
        )
        assert "#COT-0012" in text
        assert "Una persona" in text
        assert "Cuenca" in text

    def test_ask_sender_name(self):
        text = MessageTemplates.ask_sender_name()
        assert "nombre" in text.lower()

    def test_ask_sender_phone(self):
        text = MessageTemplates.ask_sender_phone()
        assert "telefono" in text.lower()

    def test_ask_recipient_name(self):
        text = MessageTemplates.ask_recipient_name()
        assert "destinatario" in text.lower()

    def test_ask_recipient_phone(self):
        text = MessageTemplates.ask_recipient_phone()
        assert "telefono" in text.lower()

    def test_ask_exact_destination(self):
        text = MessageTemplates.ask_exact_destination()
        assert "DIRECCION" in text

    def test_ask_instructions(self):
        text = MessageTemplates.ask_instructions()
        assert "INSTRUCCIONES" in text

    def test_shipment_summary_all_fields(self):
        data = {
            "remitente": "Juan Perez",
            "telefono_remitente": "0991234567",
            "destinatario": "Maria Lopez",
            "telefono_destinatario": "0997654321",
            "direccion_destino": "Calle 123, Quito",
            "tipo_paquete": "Documentos",
            "peso": "1 kg",
            "servicio_envio": "Express",
            "instrucciones": "Fragil",
        }
        summary = MessageTemplates.shipment_summary(data)
        assert "Juan Perez" in summary
        assert "Maria Lopez" in summary
        assert "Documentos" in summary
        assert "Express" in summary
        assert "Fragil" in summary

    def test_shipment_created(self):
        text = MessageTemplates.shipment_created("CUR-00001", {"destinatario": "Maria"})
        assert "CUR-00001" in text
        assert "Maria" in text
        assert "ENVIO REGISTRADO" in text

    def test_shipments_list_empty(self):
        text = MessageTemplates.shipments_list([])
        assert "No tienes envios" in text

    def test_shipments_list_with_data(self):
        shipments = [
            {"id": 1, "tracking_code": "CUR-00001", "destinatario": "Maria", "direccion_destino": "Quito", "estado": "pendiente"},
            {"id": 2, "destinatario": "Luis", "direccion_destino": "Gye", "estado": "entregado"},
        ]
        text = MessageTemplates.shipments_list(shipments)
        assert "CUR-00001" in text
        assert "Maria" in text
        assert "Luis" in text

    def test_report_categories(self):
        text = MessageTemplates.report_categories()
        assert "REPORTAR" in text
        assert "PROBLEMA" in text

    def test_ask_report_description(self):
        text = MessageTemplates.ask_report_description("Danado")
        assert "DANADO" in text
        assert "CUR-" in text

    def test_report_created_with_tracking(self):
        text = MessageTemplates.report_created(1, "Danado", "CUR-00001")
        assert "INC-0001" in text
        assert "Danado" in text
        assert "CUR-00001" in text

    def test_report_created_without_tracking(self):
        text = MessageTemplates.report_created(42, "No llego")
        assert "INC-0042" in text
        assert "No llego" in text

    def test_agent_message(self):
        text = MessageTemplates.agent()
        assert "AGENTE" in text
        assert "soporte" in text.lower()

    def test_location_help(self):
        text = MessageTemplates.location_help()
        assert "UBICACION" in text
        assert "Google Maps" in text
        assert "Apple Maps" in text

    def test_unknown_message(self):
        text = MessageTemplates.unknown()
        assert "entendi" in text.lower()
        assert "menu" in text.lower()

    def test_build_quote_options_returns_dict(self):
        result = build_quote_options("Documentos", "1 kg")
        assert isinstance(result, dict)
        assert "servicio_express" in result
        assert "servicio_estandar" in result
        assert "servicio_economico" in result

    def test_build_quote_options_has_labels(self):
        result = build_quote_options("Paquete pequeno", "Menos 1 kg")
        express = result["servicio_express"]
        assert "label" in express
        assert "eta" in express
