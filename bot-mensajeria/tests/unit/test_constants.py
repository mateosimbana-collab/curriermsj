from domain.constants import (
    INSTRUCTIONS, MENU_ACTIONS, PACKAGE_TYPES, PACKAGE_TYPE_ALIASES,
    REPORT_CATEGORIES, SHIPPING_SERVICES, STATUS_STEPS, Step, WEIGHTS,
    WEIGHT_ALIASES, WELCOME_ACTIONS, BASE_QUOTES_USD,
    normalize_action, resolve_package_type, resolve_weight,
)


class TestStep:
    def test_menu(self):
        assert Step.MENU == "menu"

    def test_welcome(self):
        assert Step.WELCOME == "bienvenida"

    def test_welcome_register(self):
        assert Step.WELCOME_REGISTER == "bienvenida_registro"

    def test_welcome_apellido(self):
        assert Step.WELCOME_APELLIDO == "bienvenida_apellido"

    def test_welcome_ciudad(self):
        assert Step.WELCOME_CIUDAD == "bienvenida_ciudad"

    def test_welcome_phone(self):
        assert Step.WELCOME_PHONE == "bienvenida_telefono"

    def test_tracking_code(self):
        assert Step.TRACKING_CODE == "rastrear_codigo"

    def test_quote_origin(self):
        assert Step.QUOTE_ORIGIN == "cotizar_origen"

    def test_quote_destination(self):
        assert Step.QUOTE_DESTINATION == "cotizar_destino"

    def test_quote_package_type(self):
        assert Step.QUOTE_PACKAGE_TYPE == "cotizar_tipo"

    def test_quote_weight(self):
        assert Step.QUOTE_WEIGHT == "cotizar_peso"

    def test_quote_service(self):
        assert Step.QUOTE_SERVICE == "cotizar_servicio"

    def test_quote_summary(self):
        assert Step.QUOTE_SUMMARY == "cotizar_resumen"

    def test_report_type(self):
        assert Step.REPORT_TYPE == "reportar_tipo"

    def test_report_description(self):
        assert Step.REPORT_DESCRIPTION == "reportar_descripcion"

    def test_new_shipment_name(self):
        assert Step.NEW_SHIPMENT_NAME == "nuevo_envio_nombre"

    def test_new_shipment_phone(self):
        assert Step.NEW_SHIPMENT_PHONE == "nuevo_envio_telefono"

    def test_new_shipment_recipient(self):
        assert Step.NEW_SHIPMENT_RECIPIENT == "nuevo_envio_destinatario"

    def test_new_shipment_recipient_phone(self):
        assert Step.NEW_SHIPMENT_RECIPIENT_PHONE == "nuevo_envio_telefono_dest"

    def test_new_shipment_destination(self):
        assert Step.NEW_SHIPMENT_DESTINATION == "nuevo_envio_dir_destino"

    def test_new_shipment_package_type(self):
        assert Step.NEW_SHIPMENT_PACKAGE_TYPE == "nuevo_envio_tipo"

    def test_new_shipment_instructions(self):
        assert Step.NEW_SHIPMENT_INSTRUCTIONS == "nuevo_envio_instrucciones"

    def test_new_shipment_confirm(self):
        assert Step.NEW_SHIPMENT_CONFIRM == "nuevo_envio_confirmar"

    def test_all_steps_unique(self):
        steps = [v for k, v in vars(Step).items() if k.isupper() or k.startswith("NEW_") or "_" in k]
        assert len(set(steps)) == len(steps)


class TestWelcomeActions:
    def test_quiero_info_variants(self):
        assert WELCOME_ACTIONS["quiero_informacion"] == "quiero_info"
        assert WELCOME_ACTIONS["quiero informacion"] == "quiero_info"
        assert WELCOME_ACTIONS["quiero_info"] == "quiero_info"

    def test_iniciar_pedido_variants(self):
        assert WELCOME_ACTIONS["iniciar_pedido"] == "iniciar_pedido"
        assert WELCOME_ACTIONS["iniciar pedido"] == "iniciar_pedido"

    def test_count(self):
        assert len(WELCOME_ACTIONS) == 5


class TestMenuActions:
    def test_number_shortcuts(self):
        assert MENU_ACTIONS["1"] == "rastrear"
        assert MENU_ACTIONS["2"] == "cotizar"
        assert MENU_ACTIONS["3"] == "mis_envios"
        assert MENU_ACTIONS["4"] == "reportar"
        assert MENU_ACTIONS["5"] == "agente"

    def test_return_variants(self):
        assert MENU_ACTIONS["menu"] == "volver_menu"
        assert MENU_ACTIONS["menu principal"] == "volver_menu"
        assert MENU_ACTIONS["volver"] == "volver_menu"
        assert MENU_ACTIONS["volver_menu"] == "volver_menu"

    def test_text_actions(self):
        assert MENU_ACTIONS["rastrear"] == "rastrear"
        assert MENU_ACTIONS["cotizar"] == "cotizar"
        assert MENU_ACTIONS["mis_envios"] == "mis_envios"
        assert MENU_ACTIONS["reportar"] == "reportar"
        assert MENU_ACTIONS["agente"] == "agente"

    def test_extra_actions(self):
        assert MENU_ACTIONS["ver_ubicacion"] == "ver_ubicacion"
        assert MENU_ACTIONS["reagendar"] == "reagendar"

    def test_count(self):
        assert len(MENU_ACTIONS) == 16


class TestPackageTypes:
    def test_four_types(self):
        assert len(PACKAGE_TYPES) == 4

    def test_values(self):
        assert PACKAGE_TYPES["tipo_documento"] == "Documentos"
        assert PACKAGE_TYPES["tipo_pequeno"] == "Paquete pequeno"
        assert PACKAGE_TYPES["tipo_mediano"] == "Paquete mediano"
        assert PACKAGE_TYPES["tipo_grande"] == "Paquete grande"


class TestPackageTypeAliases:
    def test_number_aliases(self):
        assert PACKAGE_TYPE_ALIASES["1"] == "tipo_documento"
        assert PACKAGE_TYPE_ALIASES["2"] == "tipo_pequeno"
        assert PACKAGE_TYPE_ALIASES["3"] == "tipo_mediano"
        assert PACKAGE_TYPE_ALIASES["4"] == "tipo_grande"

    def test_text_aliases(self):
        assert PACKAGE_TYPE_ALIASES["documentos"] == "tipo_documento"
        assert PACKAGE_TYPE_ALIASES["paquete pequeno"] == "tipo_pequeno"
        assert PACKAGE_TYPE_ALIASES["paquete mediano"] == "tipo_mediano"
        assert PACKAGE_TYPE_ALIASES["paquete grande"] == "tipo_grande"

    def test_count(self):
        assert len(PACKAGE_TYPE_ALIASES) == 8


class TestWeights:
    def test_three_weights(self):
        assert len(WEIGHTS) == 3

    def test_values(self):
        assert WEIGHTS["peso_ligero"] == "Menos de 1 kg"
        assert WEIGHTS["peso_medio"] == "1 - 5 kg"
        assert WEIGHTS["peso_pesado"] == "Mas de 5 kg"


class TestWeightAliases:
    def test_number_aliases(self):
        assert WEIGHT_ALIASES["1"] == "peso_ligero"
        assert WEIGHT_ALIASES["2"] == "peso_medio"
        assert WEIGHT_ALIASES["3"] == "peso_pesado"

    def test_text_aliases(self):
        assert WEIGHT_ALIASES["menos de 1 kg"] == "peso_ligero"
        assert WEIGHT_ALIASES["1 - 5 kg"] == "peso_medio"
        assert WEIGHT_ALIASES["mas de 5 kg"] == "peso_pesado"

    def test_count(self):
        assert len(WEIGHT_ALIASES) == 6


class TestInstructions:
    def test_all(self):
        assert INSTRUCTIONS["inst_fragil"] == "Fragil"
        assert INSTRUCTIONS["inst_urgente"] == "Urgente"
        assert INSTRUCTIONS["inst_ninguna"] == "Ninguna"

    def test_count(self):
        assert len(INSTRUCTIONS) == 3


class TestReportCategories:
    def test_all(self):
        assert REPORT_CATEGORIES["rep_danado"] == "Paquete danado"
        assert REPORT_CATEGORIES["rep_no_llego"] == "No llego en fecha"
        assert REPORT_CATEGORIES["rep_incompleto"] == "Contenido incompleto"

    def test_count(self):
        assert len(REPORT_CATEGORIES) == 3


class TestStatusSteps:
    def test_five_steps(self):
        assert len(STATUS_STEPS) == 5

    def test_order(self):
        assert STATUS_STEPS[0] == ("pendiente", "Solicitud registrada")
        assert STATUS_STEPS[1] == ("recibido", "Paquete recibido")
        assert STATUS_STEPS[2] == ("en_transito", "En camino al hub")
        assert STATUS_STEPS[3] == ("en_ruta", "En ruta de entrega")
        assert STATUS_STEPS[4] == ("entregado", "Entregado")

    def test_all_statuses_have_two_elements(self):
        for s in STATUS_STEPS:
            assert len(s) == 2
            assert isinstance(s[0], str)
            assert isinstance(s[1], str)


class TestBaseQuotesUSD:
    def test_all_combinations_present(self):
        expected = 12
        assert len(BASE_QUOTES_USD) == expected

    def test_documentos_prices(self):
        assert BASE_QUOTES_USD[("Documentos", "Menos de 1 kg")] == 3.50
        assert BASE_QUOTES_USD[("Documentos", "1 - 5 kg")] == 5.00
        assert BASE_QUOTES_USD[("Documentos", "Mas de 5 kg")] == 8.00

    def test_paquete_pequeno_prices(self):
        assert BASE_QUOTES_USD[("Paquete pequeno", "Menos de 1 kg")] == 5.00
        assert BASE_QUOTES_USD[("Paquete pequeno", "1 - 5 kg")] == 7.50
        assert BASE_QUOTES_USD[("Paquete pequeno", "Mas de 5 kg")] == 12.00

    def test_paquete_mediano_prices(self):
        assert BASE_QUOTES_USD[("Paquete mediano", "Menos de 1 kg")] == 7.00
        assert BASE_QUOTES_USD[("Paquete mediano", "1 - 5 kg")] == 10.00
        assert BASE_QUOTES_USD[("Paquete mediano", "Mas de 5 kg")] == 15.00

    def test_paquete_grande_prices(self):
        assert BASE_QUOTES_USD[("Paquete grande", "Menos de 1 kg")] == 10.00
        assert BASE_QUOTES_USD[("Paquete grande", "1 - 5 kg")] == 15.00
        assert BASE_QUOTES_USD[("Paquete grande", "Mas de 5 kg")] == 22.00

    def test_prices_are_positive(self):
        for price in BASE_QUOTES_USD.values():
            assert price > 0

    def test_all_package_types_covered(self):
        covered = {ptype for (ptype, _) in BASE_QUOTES_USD}
        for ptype in PACKAGE_TYPES.values():
            assert ptype in covered

    def test_all_weights_covered(self):
        covered = {w for (_, w) in BASE_QUOTES_USD}
        for w in WEIGHTS.values():
            assert w in covered


class TestShippingServices:
    def test_three_services(self):
        assert len(SHIPPING_SERVICES) == 3

    def test_express(self):
        svc = SHIPPING_SERVICES["servicio_express"]
        assert svc["label"] == "Express 24-48h"
        assert svc["multiplier"] == 2.00
        assert "24" in svc["eta"]
        assert svc["icon"] == "Express"

    def test_estandar(self):
        svc = SHIPPING_SERVICES["servicio_estandar"]
        assert svc["label"] == "Estandar 3-5 dias"
        assert svc["multiplier"] == 1.45
        assert "3" in svc["eta"]
        assert svc["icon"] == "Estandar"

    def test_economico(self):
        svc = SHIPPING_SERVICES["servicio_economico"]
        assert svc["label"] == "Economico 5-8 dias"
        assert svc["multiplier"] == 1.00
        assert "5" in svc["eta"]
        assert svc["icon"] == "Economico"

    def test_multipliers_positive(self):
        for svc in SHIPPING_SERVICES.values():
            assert svc["multiplier"] > 0

    def test_all_have_required_keys(self):
        for svc in SHIPPING_SERVICES.values():
            assert "label" in svc
            assert "multiplier" in svc
            assert "eta" in svc
            assert "icon" in svc


class TestNormalizeAction:
    def test_welcome_action(self):
        assert normalize_action("quiero informacion") == "quiero_info"

    def test_welcome_action_underscore(self):
        assert normalize_action("quiero_info") == "quiero_info"

    def test_menu_number(self):
        assert normalize_action("1") == "rastrear"
        assert normalize_action("5") == "agente"

    def test_menu_text(self):
        assert normalize_action("rastrear") == "rastrear"
        assert normalize_action("cotizar") == "cotizar"

    def test_volver_menu(self):
        assert normalize_action("volver") == "volver_menu"
        assert normalize_action("menu") == "volver_menu"

    def test_unknown_action_passthrough(self):
        assert normalize_action("algo_inesperado") == "algo_inesperado"

    def test_empty_string(self):
        assert normalize_action("") == ""

    def test_none_string(self):
        assert normalize_action("None") == "none"

    def test_whitespace_stripped(self):
        assert normalize_action("  Rastrear  ") == "rastrear"

    def test_case_insensitive(self):
        assert normalize_action("INICIAR_PEDIDO") == "iniciar_pedido"


class TestResolvePackageType:
    def test_by_number(self):
        assert resolve_package_type("1") == "Documentos"

    def test_by_text_alias(self):
        assert resolve_package_type("documentos") == "Documentos"
        assert resolve_package_type("paquete pequeno") == "Paquete pequeno"

    def test_by_raw_name(self):
        assert resolve_package_type("Documentos") == "Documentos"

    def test_unknown_returns_original(self):
        assert resolve_package_type("Algo Raro") == "Algo Raro"

    def test_empty_returns_empty(self):
        assert resolve_package_type("") == ""

    def test_whitespace_stripped(self):
        assert resolve_package_type("  Documentos  ") == "Documentos"


class TestResolveWeight:
    def test_by_number(self):
        assert resolve_weight("1") == "Menos de 1 kg"

    def test_by_text_alias(self):
        assert resolve_weight("menos de 1 kg") == "Menos de 1 kg"
        assert resolve_weight("1 - 5 kg") == "1 - 5 kg"

    def test_by_raw_name(self):
        assert resolve_weight("Mas de 5 kg") == "Mas de 5 kg"

    def test_unknown_returns_original(self):
        assert resolve_weight("Pesadisimo") == "Pesadisimo"

    def test_empty_returns_empty(self):
        assert resolve_weight("") == ""
