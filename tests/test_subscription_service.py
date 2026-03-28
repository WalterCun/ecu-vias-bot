"""Tests for SubscriptionService (SQLite-backed)."""
import pytest
from tortoise import Tortoise

from bot.services.subscription_service import SubscriptionService
from bot.db.models import Subscription


@pytest.fixture(autouse=True)
async def setup_db():
    """Initialize in-memory SQLite for tests."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["bot.db.models"]},
    )
    await Tortoise.generate_schemas(safe=True)
    yield
    await Tortoise.close_connections()


@pytest.fixture
def service():
    return SubscriptionService()


@pytest.mark.asyncio
async def test_subscribe_creates_subscription(service):
    """subscribe should create active subscription."""
    result = await service.subscribe(123456, "azuay", ["08:00"])

    assert "azuay" in result["subscriptions"]
    assert "08:00" in result["subscriptions"]["azuay"]


@pytest.mark.asyncio
async def test_subscribe_merges_times(service):
    """subscribe should add new times without removing existing."""
    await service.subscribe(123456, "azuay", ["08:00"])
    result = await service.subscribe(123456, "azuay", ["12:00"])

    times = result["subscriptions"]["azuay"]
    assert "08:00" in times
    assert "12:00" in times


@pytest.mark.asyncio
async def test_subscribe_multiple_provinces(service):
    """subscribe should support multiple provinces."""
    await service.subscribe(123456, "azuay", ["08:00"])
    result = await service.subscribe(123456, "loja", ["09:00"])

    assert "azuay" in result["subscriptions"]
    assert "loja" in result["subscriptions"]


@pytest.mark.asyncio
async def test_subscribe_normalizes_province(service):
    """subscribe should normalize province to lowercase."""
    result = await service.subscribe(123456, "azuay", ["08:00"])
    assert "azuay" in result["subscriptions"]


@pytest.mark.asyncio
async def test_subscribe_invalid_province(service):
    """subscribe should reject empty province."""
    with pytest.raises(ValueError):
        await service.subscribe(123456, "", ["08:00"])


@pytest.mark.asyncio
async def test_subscribe_invalid_time(service):
    """subscribe should reject invalid time format."""
    with pytest.raises(ValueError):
        await service.subscribe(123456, "azuay", ["invalid"])


@pytest.mark.asyncio
async def test_unsubscribe_single_province(service):
    """unsubscribe should deactivate single province."""
    await service.subscribe(123456, "azuay", ["08:00"])
    await service.subscribe(123456, "loja", ["09:00"])

    result = await service.unsubscribe(123456, "azuay")

    assert "azuay" not in result["subscriptions"]
    assert "loja" in result["subscriptions"]


@pytest.mark.asyncio
async def test_unsubscribe_all(service):
    """unsubscribe with no province should deactivate all."""
    await service.subscribe(123456, "azuay", ["08:00"])
    await service.subscribe(123456, "loja", ["09:00"])

    result = await service.unsubscribe(123456)

    assert result["subscriptions"] == {}


@pytest.mark.asyncio
async def test_get_user_subscriptions(service):
    """get_user_subscriptions should return active subscriptions."""
    await service.subscribe(123456, "azuay", ["08:00", "12:00"])
    await service.subscribe(123456, "loja", ["09:00"])

    result = await service.get_user_subscriptions(123456)

    assert "azuay" in result["subscriptions"]
    assert sorted(result["subscriptions"]["azuay"]) == ["08:00", "12:00"]
    assert result["subscriptions"]["loja"] == ["09:00"]


@pytest.mark.asyncio
async def test_get_user_subscriptions_empty(service):
    """get_user_subscriptions should return empty when no data."""
    result = await service.get_user_subscriptions(999999)
    assert result["subscriptions"] == {}


@pytest.mark.asyncio
async def test_list_subscribers_by_province(service):
    """list_subscribers_by_province should return matching user IDs."""
    await service.subscribe(123, "azuay", ["08:00"])
    await service.subscribe(456, "loja", ["09:00"])
    await service.subscribe(789, "azuay", ["12:00"])

    result = await service.list_subscribers_by_province("azuay")

    assert 123 in result
    assert 789 in result
    assert 456 not in result


@pytest.mark.asyncio
async def test_subscribe_reactivates(service):
    """subscribe should reactivate deactivated subscriptions."""
    await service.subscribe(123456, "azuay", ["08:00"])
    await service.unsubscribe(123456, "azuay")

    # Should be empty
    result = await service.get_user_subscriptions(123456)
    assert "azuay" not in result["subscriptions"]

    # Re-subscribe
    result = await service.subscribe(123456, "azuay", ["08:00"])
    assert "azuay" in result["subscriptions"]


@pytest.mark.asyncio
async def test_subscribe_deduplicates(service):
    """subscribe should not create duplicate entries."""
    await service.subscribe(123456, "azuay", ["08:00"])
    await service.subscribe(123456, "azuay", ["08:00"])

    result = await service.get_user_subscriptions(123456)
    assert result["subscriptions"]["azuay"] == ["08:00"]
