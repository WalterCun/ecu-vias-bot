"""Tests for NotificationPolicy."""
import pytest

from bot.services.notification_policy import NotificationPolicy


@pytest.fixture
def policy():
    return NotificationPolicy()


def test_no_changes(policy):
    """Should detect no changes when data is identical."""
    old = {"azuay": [{"id": "1", "descripcion": "via 1"}]}
    new = {"azuay": [{"id": "1", "descripcion": "via 1"}]}

    result = policy.compare(old, new)
    assert result["azuay"]["new"] == []
    assert result["azuay"]["removed"] == []
    assert result["azuay"]["updated"] == []


def test_new_incident(policy):
    """Should detect new incidents."""
    old = {"azuay": [{"id": "1", "descripcion": "via 1"}]}
    new = {"azuay": [
        {"id": "1", "descripcion": "via 1"},
        {"id": "2", "descripcion": "via 2"},
    ]}

    result = policy.compare(old, new)
    assert len(result["azuay"]["new"]) == 1
    assert result["azuay"]["new"][0]["id"] == "2"


def test_removed_incident(policy):
    """Should detect removed incidents."""
    old = {"azuay": [
        {"id": "1", "descripcion": "via 1"},
        {"id": "2", "descripcion": "via 2"},
    ]}
    new = {"azuay": [{"id": "1", "descripcion": "via 1"}]}

    result = policy.compare(old, new)
    assert len(result["azuay"]["removed"]) == 1
    assert result["azuay"]["removed"][0]["id"] == "2"


def test_updated_incident(policy):
    """Should detect updated incidents (status change)."""
    old = {"azuay": [{"id": "1", "descripcion": "via 1", "estado": "ABIERTA"}]}
    new = {"azuay": [{"id": "1", "descripcion": "via 1", "estado": "CERRADA"}]}

    result = policy.compare(old, new)
    assert len(result["azuay"]["updated"]) == 1


def test_new_province(policy):
    """Should detect new province."""
    old = {"azuay": [{"id": "1"}]}
    new = {
        "azuay": [{"id": "1"}],
        "loja": [{"id": "2"}],
    }

    result = policy.compare(old, new)
    assert result["loja"]["new"] == [{"id": "2"}]


def test_removed_province(policy):
    """Should detect removed province."""
    old = {
        "azuay": [{"id": "1"}],
        "loja": [{"id": "2"}],
    }
    new = {"azuay": [{"id": "1"}]}

    result = policy.compare(old, new)
    assert result["loja"]["removed"] == [{"id": "2"}]


def test_multiple_provinces(policy):
    """Should handle changes across multiple provinces."""
    old = {
        "azuay": [{"id": "1"}],
        "loja": [{"id": "2"}],
    }
    new = {
        "azuay": [{"id": "1"}, {"id": "3"}],
        "loja": [{"id": "2", "status": "changed"}],
    }

    result = policy.compare(old, new)
    assert len(result["azuay"]["new"]) == 1
    assert len(result["loja"]["updated"]) == 1


def test_empty_to_populated(policy):
    """Should handle transition from empty to populated."""
    old = {}
    new = {"azuay": [{"id": "1"}]}

    result = policy.compare(old, new)
    assert len(result["azuay"]["new"]) == 1


def test_populated_to_empty(policy):
    """Should handle transition from populated to empty."""
    old = {"azuay": [{"id": "1"}]}
    new = {}

    result = policy.compare(old, new)
    assert len(result["azuay"]["removed"]) == 1
