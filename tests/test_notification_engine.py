"""Tests for NotificationEngine."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.notification_engine import NotificationEngine


@pytest.fixture
def mock_services():
    via_service = AsyncMock()
    subscription_service = AsyncMock()
    notification_policy = MagicMock()
    bot = AsyncMock()

    return {
        "via_service": via_service,
        "subscription_service": subscription_service,
        "notification_policy": notification_policy,
        "bot": bot,
    }


@pytest.fixture
def engine(mock_services):
    return NotificationEngine(
        via_service=mock_services["via_service"],
        subscription_service=mock_services["subscription_service"],
        notification_policy=mock_services["notification_policy"],
        bot=mock_services["bot"],
    )


def test_build_message_new():
    """Should build message with new incidents."""
    changes = {
        "new": [{"descripcion": "Road closed"}],
        "removed": [],
        "updated": [],
    }
    message = NotificationEngine._build_message("azuay", changes)
    assert "Azuay" in message or "azuay" in message.lower()
    assert "Nuevas" in message or "new" in message.lower()


def test_build_message_removed():
    """Should build message with removed incidents."""
    changes = {
        "new": [],
        "removed": [{"descripcion": "Old incident"}],
        "updated": [],
    }
    message = NotificationEngine._build_message("azuay", changes)
    assert "Resueltas" in message or "removed" in message.lower()


def test_build_message_updated():
    """Should build message with updated incidents."""
    changes = {
        "new": [],
        "removed": [],
        "updated": [{"descripcion": "Changed road"}],
    }
    message = NotificationEngine._build_message("azuay", changes)
    assert "Actualizadas" in message or "updated" in message.lower()


@pytest.mark.asyncio
async def test_run_cycle_first_snapshot(engine, mock_services):
    """First cycle should store snapshot without comparing."""
    mock_services["via_service"].get_latest_vias.return_value = {
        "azuay": [{"descripcion": "via 1"}]
    }

    await engine.run_cycle()

    # Should not call compare on first run
    mock_services["notification_policy"].compare.assert_not_called()


@pytest.mark.asyncio
async def test_run_cycle_no_changes(engine, mock_services):
    """Should detect no changes when data is same."""
    data = {"azuay": [{"descripcion": "via 1"}]}
    mock_services["via_service"].get_latest_vias.return_value = data

    # First run - snapshot
    await engine.run_cycle()

    # Second run - same data
    mock_services["notification_policy"].compare.return_value = {
        "azuay": {"new": [], "removed": [], "updated": []}
    }
    await engine.run_cycle()

    # Should not notify anyone when no changes
    mock_services["subscription_service"].list_subscribers_by_province.assert_not_called()


@pytest.mark.asyncio
async def test_run_cycle_with_changes(engine, mock_services):
    """Should detect changes and prepare notifications."""
    mock_services["via_service"].get_latest_vias.return_value = {
        "azuay": [{"descripcion": "via 1"}]
    }

    # First run - snapshot
    await engine.run_cycle()

    # Second run - changes detected
    mock_services["via_service"].get_latest_vias.return_value = {
        "azuay": [{"descripcion": "via 1 updated"}]
    }
    mock_services["notification_policy"].compare.return_value = {
        "azuay": {"new": [], "removed": [], "updated": [{"descripcion": "via 1 updated"}]}
    }
    mock_services["subscription_service"].list_subscribers_by_province.return_value = []

    await engine.run_cycle()

    # Should have called compare
    mock_services["notification_policy"].compare.assert_called_once()


@pytest.mark.asyncio
async def test_run_cycle_error_handling(engine, mock_services):
    """Should handle errors gracefully."""
    mock_services["via_service"].get_latest_vias.side_effect = Exception("API down")

    # Should not crash
    await engine.run_cycle()
