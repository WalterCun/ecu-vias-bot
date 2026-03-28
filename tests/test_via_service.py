"""Tests for ViaService."""
import pytest
from unittest.mock import MagicMock

from bot.services.via_service import ViaService


@pytest.fixture
def mock_client():
    """Create a mock client that has only get_states_vias method."""
    data = [
        {
            "descripcion": "CUENCA - MACHALA",
            "estado": "A",
            "EstadoActual": {"nombre": "ABIERTA"},
            "Provincia": {"descripcion": "AZUAY"},
        },
        {
            "descripcion": "QUITO - AMBATO",
            "estado": "A",
            "EstadoActual": {"nombre": "PARCIALMENTE HABILITADA"},
            "Provincia": {"descripcion": "PICHINCHA"},
        },
    ]

    class MockClient:
        def get_states_vias(self):
            return data

    return MockClient()


@pytest.fixture
def via_service(mock_client):
    return ViaService(http_client=mock_client, cache_ttl=60)


def test_extract_province_dict():
    """Should extract province from nested dict."""
    row = {"Provincia": {"descripcion": "AZUAY"}}
    assert ViaService._extract_province(row) == "azuay"


def test_extract_province_string():
    """Should extract province from string field."""
    row = {"province": "Azuay"}
    assert ViaService._extract_province(row) == "azuay"


def test_extract_province_missing():
    """Should return None when no province info."""
    row = {"descripcion": "some via"}
    assert ViaService._extract_province(row) is None


def test_extract_rows_list():
    """Should extract rows from list."""
    payload = [{"id": 1}, {"id": 2}]
    result = ViaService._extract_rows(payload)
    assert len(result) == 2


def test_extract_rows_dict():
    """Should extract rows from dict with 'data' key."""
    payload = {"data": [{"id": 1}, {"id": 2}]}
    result = ViaService._extract_rows(payload)
    assert len(result) == 2


def test_extract_rows_empty():
    """Should return empty list for invalid payload."""
    assert ViaService._extract_rows(None) == []
    assert ViaService._extract_rows("invalid") == []
    assert ViaService._extract_rows({}) == []


@pytest.mark.asyncio
async def test_get_latest_vias_groups_by_province(via_service):
    """get_latest_vias should group rows by province."""
    result = await via_service.get_latest_vias()

    assert "azuay" in result
    assert "pichincha" in result
    assert len(result["azuay"]) == 1
    assert len(result["pichincha"]) == 1


@pytest.mark.asyncio
async def test_get_latest_vias_caches(mock_client):
    """Subsequent calls should use cache."""
    # Track call count
    call_count = 0
    original_method = mock_client.get_states_vias

    def counting_method():
        nonlocal call_count
        call_count += 1
        return original_method()

    mock_client.get_states_vias = counting_method

    service = ViaService(http_client=mock_client, cache_ttl=60)
    result1 = await service.get_latest_vias()
    result2 = await service.get_latest_vias()

    # Client should only be called once (cache hit on second call)
    assert call_count == 1
    assert result1 == result2


@pytest.mark.asyncio
async def test_get_latest_vias_client_error():
    """Should handle client errors gracefully."""

    class ErrorClient:
        def get_states_vias(self):
            raise Exception("Network error")

    service = ViaService(http_client=ErrorClient(), cache_ttl=60)

    result = await service.get_latest_vias()
    assert result == {}
