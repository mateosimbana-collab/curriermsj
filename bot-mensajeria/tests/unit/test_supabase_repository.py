import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from domain.constants import Step
from services.supabase_repository import SupabaseRepository


@pytest.fixture
def repo():
    with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test_key"}):
        return SupabaseRepository()


class TestInit:
    def test_default_table_names(self, repo):
        assert repo.table_envios == "envios"
        assert repo.table_estado == "estado_usuario"
        assert repo.table_faq == "faq"
        assert repo.table_reportes == "reportes"
        assert repo.table_clientes == "clientes"

    def test_url_trailing_slash_stripped(self):
        with patch.dict("os.environ", {"SUPABASE_URL": "https://test.co", "SUPABASE_KEY": "k"}):
            r = SupabaseRepository()
            assert r.supabase_url == "https://test.co"
            assert r.supabase_url.endswith("/") is False

    def test_headers_have_auth(self, repo):
        h = repo.headers
        assert h["apikey"] == "test_key"
        assert h["Authorization"] == "Bearer test_key"
        assert h["Content-Type"] == "application/json"

    def test_raises_without_config(self):
        with patch.dict("os.environ", {"SUPABASE_URL": "", "SUPABASE_KEY": ""}):
            with pytest.raises(ValueError, match="SUPABASE_URL y SUPABASE_KEY son requeridos"):
                SupabaseRepository()


class TestTableUrl:
    def test_returns_full_url(self, repo):
        assert repo._table_url("clientes") == "https://test.supabase.co/rest/v1/clientes"


def _mock_execute(repo, return_data):
    repo.client = MagicMock()
    mock_res = MagicMock()
    mock_res.data = return_data
    chain = MagicMock()
    chain.execute.return_value = mock_res
    repo.client.table.return_value = chain
    return chain


class TestGetClient:
    def test_returns_client(self, repo):
        chain = _mock_execute(repo, [{"telefono": "593991234567", "nombre_completo": "Juan"}])
        result = repo.get_client("593991234567")
        assert result["nombre_completo"] == "Juan"
        chain.select.assert_called_with("*")
        chain.eq.assert_called_with("telefono", "593991234567")

    def test_returns_none_when_not_found(self, repo):
        _mock_execute(repo, [])
        result = repo.get_client("593991234567")
        assert result is None


class TestSaveClient:
    def test_creates_client(self, repo):
        _mock_execute(repo, [])
        with patch.object(repo, "crear_cliente", return_value={"telefono": "593991234567", "nombre_completo": "Juan Perez"}) as mock:
            result = repo.save_client("593991234567", "Juan", "Perez")
            assert result["nombre_completo"] == "Juan Perez"
            mock.assert_called_once()

    def test_updates_existing(self, repo):
        existing = {"id": "uuid-1", "telefono": "593991234567", "nombre_completo": "Juan"}
        _mock_execute(repo, [existing])
        with patch.object(repo, "actualizar_cliente") as mock_update:
            repo.save_client("593991234567", "Juan", "Perez")
            mock_update.assert_called_once()

    def test_empty_data_returns_empty_dict(self, repo):
        _mock_execute(repo, [])
        with patch.object(repo, "crear_cliente", return_value=None):
            result = repo.save_client("593991234567", "Juan")
            assert result == {}


class TestGetUserState:
    def test_returns_state(self, repo):
        chain = _mock_execute(repo, [{"telefono": "593991234567", "paso_actual": "menu"}])
        result = repo.get_user_state("593991234567")
        assert result["paso_actual"] == "menu"

    def test_returns_none(self, repo):
        _mock_execute(repo, [])
        result = repo.get_user_state("593991234567")
        assert result is None


class TestCreateUserState:
    def test_creates_new_state(self, repo):
        with patch.object(repo, "guardar_sesion") as mock_guardar:
            with patch.object(repo, "obtener_sesion", return_value={"telefono": "593991234567", "paso_actual": "menu"}):
                result = repo.create_user_state("593991234567", "menu", {"key": "val"})
                assert result["paso_actual"] == "menu"
                mock_guardar.assert_called_once_with("593991234567", "menu", {"key": "val"})

    def test_existing_session_no_update(self, repo):
        with patch.object(repo, "obtener_sesion", return_value={"telefono": "593991234567", "paso_actual": "otro_paso"}):
            with patch.object(repo, "guardar_sesion") as mock_guardar:
                result = repo.create_user_state("593991234567", "menu", {})
                assert result["paso_actual"] == "otro_paso"
                mock_guardar.assert_not_called()

    def test_409_fallback(self, repo):
        mock_response = MagicMock()
        mock_response.status_code = 409
        with patch.object(repo, "get_user_state", side_effect=[None, {"phone_number": "593991234567", "paso_actual": "menu"}]):
            with patch.object(repo, "update_user_state") as mock_update:
                with patch.object(repo, "_request", side_effect=httpx.HTTPStatusError("Conflict", request=MagicMock(), response=mock_response)):
                    result = repo.create_user_state("593991234567", "menu", {})
                    assert result["paso_actual"] == "menu"


class TestUpdateUserState:
    def test_updates_step(self, repo):
        chain = _mock_execute(repo, [{"telefono": "593991234567", "paso_actual": "menu"}])
        repo.update_user_state("593991234567", step="nuevo_paso")
        chain.update.assert_called_once()

    def test_updates_data(self, repo):
        chain = _mock_execute(repo, [{"telefono": "593991234567"}])
        repo.update_user_state("593991234567", data={"clave": "valor"})
        chain.update.assert_called_once()

    def test_reset_state(self, repo):
        with patch.object(repo, "update_user_state") as mock:
            repo.reset_user_state("593991234567")
            mock.assert_called_once_with("593991234567", Step.MENU, {})


class TestSearchFAQ:
    def test_finds_answer(self, repo):
        with patch.object(repo, "_request", return_value=[{"respuesta": "Respuesta de prueba"}]) as mock:
            result = repo.search_faq("horario")
            assert result == "Respuesta de prueba"

    def test_returns_none_when_not_found(self, repo):
        with patch.object(repo, "_request", return_value=[]):
            result = repo.search_faq("xyz")
            assert result is None

    def test_empty_question_returns_none(self, repo):
        result = repo.search_faq("")
        assert result is None

    def test_none_question_returns_none(self, repo):
        result = repo.search_faq(None)
        assert result is None


class TestSaveReport:
    def test_saves_and_returns_id(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 42}]) as mock:
            result = repo.save_report("593991234567", "descripcion", category="Danado", tracking_code="CUR-00001")
            assert result == 42
            args = mock.call_args[0]
            assert args[0] == "POST"

    def test_saves_without_category(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 1}]):
            result = repo.save_report("593991234567", "descripcion")
            assert result == 1

    def test_list_response_handling(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 99}]):
            assert repo.save_report("593991234567", "test") == 99

    def test_dict_response_handling(self, repo):
        with patch.object(repo, "_request", return_value={"id": 55}):
            assert repo.save_report("593991234567", "test") == 55


class TestSaveShipment:
    def test_saves_and_returns_id(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 1}]) as mock:
            result = repo.save_shipment({"remitente": "Juan"})
            assert result == 1
            args = mock.call_args
            assert args[0][0] == "POST"
            assert "creado_en" in args.kwargs["json"]


class TestGetShipmentsByPhone:
    def test_returns_shipments(self, repo):
        mock_data = [{"id": 1, "tracking_code": "CUR-00001", "remitente": "Juan", "destinatario": "Maria", "direccion_destino": "UIO", "estado": "pendiente"}]
        with patch.object(repo, "_request", return_value=mock_data):
            result = repo.get_shipments_by_phone("593991234567")
            assert len(result) == 1
            assert result[0]["tracking_code"] == "CUR-00001"

    def test_returns_empty(self, repo):
        with patch.object(repo, "_request", return_value=[]):
            result = repo.get_shipments_by_phone("593991234567")
            assert result == []


class TestGetShipmentByTracking:
    def test_by_tracking_code(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 1, "tracking_code": "CUR-00001"}]) as mock:
            result = repo.get_shipment_by_tracking("CUR-00001")
            assert result["id"] == 1

    def test_by_tracking_code_with_hash(self, repo):
        with patch.object(repo, "_request", return_value=[{"id": 1}]) as mock:
            result = repo.get_shipment_by_tracking("#cur-00001")
            assert result["id"] == 1

    def test_by_numeric_id(self, repo):
        with patch.object(repo, "_request", return_value=[]):
            with patch.object(repo, "get_shipment_by_id", return_value={"id": 5}) as mock:
                result = repo.get_shipment_by_tracking("5")
                assert result["id"] == 5

    def test_not_found_returns_none(self, repo):
        with patch.object(repo, "_request", return_value=[]):
            result = repo.get_shipment_by_tracking("CUR-99999")
            assert result is None


class TestExtractTempData:
    def test_none_state_returns_empty(self, repo):
        assert repo.extract_temp_data(None) == {}

    def test_empty_state_returns_empty(self, repo):
        assert repo.extract_temp_data({}) == {}

    def test_missing_datos_temp_returns_empty(self, repo):
        assert repo.extract_temp_data({"phone_number": "123"}) == {}

    def test_dict_datos_temp(self, repo):
        state = {"datos_temp": {"nombre": "Juan"}}
        assert repo.extract_temp_data(state) == {"nombre": "Juan"}

    def test_json_string_datos_temp(self, repo):
        state = {"datos_temp": '{"nombre": "Juan"}'}
        assert repo.extract_temp_data(state) == {"nombre": "Juan"}

    def test_invalid_json_returns_empty(self, repo):
        state = {"datos_temp": "not-json"}
        assert repo.extract_temp_data(state) == {}


class TestParseDatetime:
    def test_iso_format_with_z(self, repo):
        result = repo._parse_datetime("2026-07-03T12:00:00Z")
        assert result is not None
        assert result.hour == 12

    def test_iso_format_with_offset(self, repo):
        result = repo._parse_datetime("2026-07-03T12:00:00+00:00")
        assert result is not None

    def test_no_timezone(self, repo):
        result = repo._parse_datetime("2026-07-03T12:00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_none_value(self, repo):
        assert repo._parse_datetime(None) is None

    def test_empty_value(self, repo):
        assert repo._parse_datetime("") is None

    def test_invalid_value(self, repo):
        assert repo._parse_datetime("not-a-date") is None


class TestBuildDailyCounts:
    def test_all_zeros_with_no_rows(self, repo):
        start = datetime(2026, 7, 1, tzinfo=timezone.utc)
        result = repo._build_daily_counts(start, 3, [])
        assert len(result) == 3
        assert all(d["count"] == 0 for d in result)
        assert result[0]["date"] == "2026-07-01"
        assert result[1]["date"] == "2026-07-02"
        assert result[2]["date"] == "2026-07-03"

    def test_counts_rows(self, repo):
        start = datetime(2026, 7, 1, tzinfo=timezone.utc)
        rows = [
            {"creado_en": "2026-07-01T10:00:00Z"},
            {"creado_en": "2026-07-01T15:00:00Z"},
            {"creado_en": "2026-07-03T12:00:00Z"},
        ]
        result = repo._build_daily_counts(start, 5, rows)
        counts = {d["date"]: d["count"] for d in result}
        assert counts["2026-07-01"] == 2
        assert counts["2026-07-03"] == 1


class TestRequest:
    def test_get_request(self, repo):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'[{"id":1}]'
        mock_response.json.return_value = [{"id": 1}]
        with patch("httpx.Client.request", return_value=mock_response) as mock:
            result = repo._request("GET", "https://test.supabase.co/rest/v1/test")
            assert result == [{"id": 1}]

    def test_empty_response(self, repo):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b""
        with patch("httpx.Client.request", return_value=mock_response):
            result = repo._request("GET", "https://test.supabase.co/rest/v1/test")
            assert result == []
