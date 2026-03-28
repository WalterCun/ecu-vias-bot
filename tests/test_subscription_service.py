"""Tests for SubscriptionService with mocked persistence."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.subscription_service import SubscriptionService


@pytest.fixture
def mock_persistence():
    persistence = MagicMock()
    persistence.USER_DATA_KEY = "bot:user_data"
    persistence.redis = AsyncMock()
    persistence._deserialize = MagicMock(side_effect=lambda x: __import__("json").loads(x) if isinstance(x, str) else x)
    persistence.update_user_data = AsyncMock()
    persistence.get_user_data_by_id = AsyncMock(return_value={})
    return persistence


@pytest.fixture
def service(mock_persistence):
    return SubscriptionService(mock_persistence)


@pytest.mark.asyncio
async def test_subscribe_creates_subscription(service, mock_persistence):
    """subscribe should create subscription for a province."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={})

    result = await service.subscribe(123456, "azuay", ["08:00"])

    assert "subscriptions" in result
    assert "azuay" in result["subscriptions"]
    assert "08:00" in result["subscriptions"]["azuay"]
    mock_persistence.update_user_data.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_merges_times(service, mock_persistence):
    """subscribe should merge new times with existing ones."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={
        "subscriptions": {"azuay": ["08:00"]}
    })

    result = await service.subscribe(123456, "azuay", ["12:00"])

    times = result["subscriptions"]["azuay"]
    assert "08:00" in times
    assert "12:00" in times


@pytest.mark.asyncio
async def test_subscribe_multiple_provinces(service, mock_persistence):
    """subscribe should support multiple provinces."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={
        "subscriptions": {"azuay": ["08:00"]}
    })

    result = await service.subscribe(123456, "loja", ["09:00"])

    assert "azuay" in result["subscriptions"]
    assert "loja" in result["subscriptions"]


@pytest.mark.asyncio
async def test_subscribe_normalizes_province(service, mock_persistence):
    """subscribe should reject non-lowercase province (validates strictly)."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={})

    # _validate_province requires lowercase
    with pytest.raises(ValueError, match="lowercase"):
        await service.subscribe(123456, "AZUAY", ["08:00"])

    # Lowercase should work
    result = await service.subscribe(123456, "azuay", ["08:00"])
    assert "azuay" in result["subscriptions"]


@pytest.mark.asyncio
async def test_unsubscribe_single_province(service, mock_persistence):
    """unsubscribe should remove single province."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={
        "subscriptions": {"azuay": ["08:00"], "loja": ["09:00"]}
    })

    result = await service.unsubscribe(123456, "azuay")

    assert "azuay" not in result["subscriptions"]
    assert "loja" in result["subscriptions"]


@pytest.mark.asyncio
async def test_unsubscribe_all(service, mock_persistence):
    """unsubscribe with no province should remove all."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={
        "subscriptions": {"azuay": ["08:00"], "loja": ["09:00"]}
    })

    result = await service.unsubscribe(123456)

    assert result["subscriptions"] == {}


@pytest.mark.asyncio
async def test_get_user_subscriptions(service, mock_persistence):
    """get_user_subscriptions should return normalized subscriptions."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={
        "subscriptions": {"azuay": ["08:00", "12:00"], "loja": ["09:00"]}
    })

    result = await service.get_user_subscriptions(123456)

    assert "azuay" in result["subscriptions"]
    assert result["subscriptions"]["azuay"] == ["08:00", "12:00"]
    assert result["subscriptions"]["loja"] == ["09:00"]


@pytest.mark.asyncio
async def test_get_user_subscriptions_empty(service, mock_persistence):
    """get_user_subscriptions should return empty dict when no data."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={})

    result = await service.get_user_subscriptions(123456)

    assert result["subscriptions"] == {}


@pytest.mark.asyncio
async def test_get_user_subscriptions_redis_error(service, mock_persistence):
    """get_user_subscriptions should handle Redis errors gracefully."""
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_persistence.get_user_data_by_id = AsyncMock(side_effect=RedisConnectionError("Redis down"))

    result = await service.get_user_subscriptions(123456)

    assert result["subscriptions"] == {}


@pytest.mark.asyncio
async def test_list_subscribers_by_province(service, mock_persistence):
    """list_subscribers_by_province should return matching user IDs."""
    import json
    mock_persistence.redis.hgetall = AsyncMock(return_value={
        "123": json.dumps({"subscriptions": {"azuay": ["08:00"]}}),
        "456": json.dumps({"subscriptions": {"loja": ["09:00"]}}),
        "789": json.dumps({"subscriptions": {"azuay": ["12:00"], "loja": ["09:00"]}}),
    })

    result = await service.list_subscribers_by_province("azuay")

    assert 123 in result
    assert 789 in result
    assert 456 not in result


@pytest.mark.asyncio
async def test_subscribe_invalid_time(service, mock_persistence):
    """subscribe should reject invalid time format."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={})

    with pytest.raises(ValueError):
        await service.subscribe(123456, "azuay", ["invalid"])


@pytest.mark.asyncio
async def test_subscribe_valid_province(service, mock_persistence):
    """subscribe should work with lowercase province."""
    mock_persistence.get_user_data_by_id = AsyncMock(return_value={})

    result = await service.subscribe(123456, "azuay", ["08:00"])
    assert "azuay" in result["subscriptions"]
