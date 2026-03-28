"""Tests for ViaSyncService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.via_sync_service import ViaSyncService


@pytest.fixture
def sync_service():
    return ViaSyncService()


def test_sync_service_initialization(sync_service):
    """Service should initialize with _initialized=False."""
    assert sync_service._initialized is False


def test_sync_service_default_db_url(sync_service):
    """Default DB URL should be sqlite://ecuavias.db."""
    from bot.services.via_sync_service import TORTOISE_CONFIG
    assert "sqlite" in TORTOISE_CONFIG["connections"]["default"]


@pytest.mark.asyncio
async def test_sync_vias_not_initialized(sync_service):
    """sync_vias should return zeros when DB is not initialized."""
    result = await sync_service.sync_vias([])
    assert result == {"created": 0, "updated": 0, "unchanged": 0, "errors": 0}


@pytest.mark.asyncio
async def test_get_vias_not_initialized(sync_service):
    """get_vias_by_province should return empty list when not initialized."""
    result = await sync_service.get_vias_by_province("azuay")
    assert result == []


@pytest.mark.asyncio
async def test_get_all_provinces_not_initialized(sync_service):
    """get_all_provinces should return empty list when not initialized."""
    result = await sync_service.get_all_provinces()
    assert result == []


@pytest.mark.asyncio
async def test_get_vias_from_api_fallback(sync_service):
    """get_vias_from_api should query via_service as fallback."""
    mock_via_service = AsyncMock()
    mock_via_service.get_latest_vias.return_value = {
        "azuay": [
            {
                "descripcion": "CUENCA - MACHALA",
                "estado": "A",
                "EstadoActual": {"nombre": "ABIERTA"},
                "observaciones": "",
                "Provincia": {"descripcion": "AZUAY"},
                "Canton": {"descripcion": "CUENCA"},
                "GroupDetail": {"nombre": "ARTERIAL"},
            }
        ]
    }

    result = await sync_service.get_vias_from_api("azuay", mock_via_service)
    assert len(result) == 1
    assert result[0]["descripcion"] == "CUENCA - MACHALA"
    assert result[0]["estado_actual"] == "ABIERTA"


@pytest.mark.asyncio
async def test_get_vias_from_api_empty(sync_service):
    """get_vias_from_api should return empty for unknown province."""
    mock_via_service = AsyncMock()
    mock_via_service.get_latest_vias.return_value = {"azuay": []}

    result = await sync_service.get_vias_from_api("unknown", mock_via_service)
    assert result == []


@pytest.mark.asyncio
async def test_get_vias_from_api_error(sync_service):
    """get_vias_from_api should handle errors gracefully."""
    mock_via_service = AsyncMock()
    mock_via_service.get_latest_vias.side_effect = Exception("API down")

    result = await sync_service.get_vias_from_api("azuay", mock_via_service)
    assert result == []
