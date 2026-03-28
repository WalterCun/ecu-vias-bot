"""Tests for ViasEcuadorAPI."""
import pytest
from unittest.mock import patch, MagicMock

from bot.services.api import ViasEcuadorAPI


def test_api_initialization():
    """API should initialize with correct URL."""
    api = ViasEcuadorAPI()
    assert "ecu911.gob.ec" in api.url
    assert "ViasWeb.php" in api.url


def test_api_url_contains_filters():
    """URL should contain proper query filters."""
    api = ViasEcuadorAPI()
    assert "estado=A" in api.url
    limit=200
    assert "limit=200" in api.url


@patch("bot.services.api.ViasEcuadorAPI.session")
def test_get_states_vias_success(mock_session):
    """Should return data list on successful response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": 200,
        "data": [
            {"descripcion": "via 1", "Provincia": {"descripcion": "AZUAY"}},
            {"descripcion": "via 2", "Provincia": {"descripcion": "LOJA"}},
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    api = ViasEcuadorAPI()
    result = api.get_states_vias()

    assert isinstance(result, list)
    assert len(result) == 2


@patch("bot.services.api.ViasEcuadorAPI.session")
def test_get_states_vias_empty_response(mock_session):
    """Should return empty list when API returns no data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 200, "data": []}
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    api = ViasEcuadorAPI()
    result = api.get_states_vias()

    assert result == []


@patch("bot.services.api.ViasEcuadorAPI.session")
def test_get_states_vias_network_error(mock_session):
    """Should return empty list on network error."""
    import requests
    mock_session.get.side_effect = requests.ConnectionError("Connection refused")

    api = ViasEcuadorAPI()
    result = api.get_states_vias()

    assert result == []


@patch("bot.services.api.ViasEcuadorAPI.session")
def test_get_states_vias_invalid_json(mock_session):
    """Should return empty list on invalid JSON."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_session.get.return_value = mock_response

    api = ViasEcuadorAPI()
    result = api.get_states_vias()

    assert result == []


@patch("bot.services.api.ViasEcuadorAPI.session")
def test_get_states_vias_non_list_data(mock_session):
    """Should return empty list when data is not a list."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 200, "data": "not a list"}
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    api = ViasEcuadorAPI()
    result = api.get_states_vias()

    assert result == []
