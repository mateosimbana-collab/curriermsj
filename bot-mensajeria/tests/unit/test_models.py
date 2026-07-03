from domain.models import IncomingMessage


class TestIncomingMessage:
    def test_create_text_message(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="Hola",
            message_type="text",
        )
        assert msg.phone_number == "593991234567"
        assert msg.text == "Hola"
        assert msg.message_type == "text"
        assert msg.has_location is False
        assert msg.latitude is None
        assert msg.longitude is None
        assert msg.raw is None

    def test_create_location_message(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="ubicacion_recibida",
            message_type="location",
            latitude=-0.22985,
            longitude=-78.52495,
        )
        assert msg.message_type == "location"
        assert msg.has_location is True
        assert msg.latitude == -0.22985
        assert msg.longitude == -78.52495

    def test_create_interactive_button(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="cotizar",
            message_type="interactive_button",
        )
        assert msg.message_type == "interactive_button"
        assert msg.text == "cotizar"

    def test_create_interactive_list(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="tipo_documento",
            message_type="interactive_list",
        )
        assert msg.message_type == "interactive_list"
        assert msg.text == "tipo_documento"

    def test_create_reaction_message(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="Reacción: 👍",
            message_type="reaction",
        )
        assert msg.message_type == "reaction"
        assert "👍" in msg.text

    def test_default_has_location_false(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="test",
            message_type="text",
        )
        assert msg.has_location is False

    def test_empty_text(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="",
            message_type="text",
        )
        assert msg.text == ""

    def test_long_phone_number(self):
        msg = IncomingMessage(
            phone_number="593991234567890",
            text="test",
            message_type="text",
        )
        assert msg.phone_number == "593991234567890"

    def test_has_location_without_coords(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="",
            message_type="location",
        )
        assert msg.has_location is False
        assert msg.latitude is None
        assert msg.longitude is None

    def test_raw_payload_stored(self):
        raw = {"from": "593991234567", "type": "text"}
        msg = IncomingMessage(
            phone_number="593991234567",
            text="hola",
            message_type="text",
            raw=raw,
        )
        assert msg.raw == raw

    def test_repr_contains_phone_and_text(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="hola",
            message_type="text",
        )
        r = repr(msg)
        assert "593991234567" in r
        assert "hola" in r

    def test_repr_with_location(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="",
            message_type="location",
            latitude=-0.23,
            longitude=-78.52,
        )
        r = repr(msg)
        assert "593991234567" in r
        assert "location" in r.lower() or "Location" in r

    def test_frozen_dataclass(self):
        msg = IncomingMessage(
            phone_number="593991234567",
            text="hola",
            message_type="text",
        )
        import dataclasses
        assert dataclasses.is_dataclass(msg)
        assert dataclasses.fields(msg)
