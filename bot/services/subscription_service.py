"""Subscription domain service built on top of Redis JSON persistence."""

from __future__ import annotations

import re
from typing import Any

from redis.exceptions import ConnectionError as RedisConnectionError


class SubscriptionService:
    """Service layer for managing user province/time subscriptions."""

    _TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    def __init__(self, persistence: Any):
        """Initialize service with a persistence backend instance."""
        self.persistence = persistence

    @staticmethod
    def _validate_province(province: str) -> str:
        """Validate and normalize a province value."""
        if not isinstance(province, str):
            raise ValueError("province must be a lowercase string")

        normalized = province.strip()
        if not normalized or normalized != normalized.lower():
            raise ValueError("province must be lowercase")

        return normalized

    @classmethod
    def _normalize_times(cls, times: list[str]) -> list[str]:
        """Validate HH:MM format, deduplicate, and sort notification times."""
        if not isinstance(times, list):
            raise ValueError("times must be a list[str]")

        validated: set[str] = set()
        for value in times:
            if not isinstance(value, str):
                raise ValueError("invalid time format")
            candidate = value.strip()
            if not cls._TIME_PATTERN.match(candidate):
                raise ValueError("invalid time format")
            validated.add(candidate)

        return sorted(validated)

    async def _get_user_data(self, user_id: int) -> dict:
        """Fetch a single user's data using the persistence O(1) getter."""
        try:
            return await self.persistence.get_user_data_by_id(user_id)
        except RedisConnectionError:
            return {}

    async def subscribe(self, user_id: int, province: str, times: list[str]) -> dict:
        """Subscribe a user to a province and one or more notification times."""
        normalized_province = self._validate_province(province)
        normalized_times = self._normalize_times(times)

        user_data = await self._get_user_data(user_id)
        subscriptions = user_data.get("subscriptions", {})
        if not isinstance(subscriptions, dict):
            subscriptions = {}

        existing_times = subscriptions.get(normalized_province, [])
        if not isinstance(existing_times, list):
            existing_times = []

        merged_times = sorted(set(existing_times) | set(normalized_times))
        subscriptions[normalized_province] = merged_times

        user_data["subscriptions"] = subscriptions
        await self.persistence.update_user_data(user_id, user_data)
        return user_data

    async def unsubscribe(self, user_id: int, province: str | None = None) -> dict:
        """Unsubscribe a user from one province or all provinces."""
        user_data = await self._get_user_data(user_id)
        subscriptions = user_data.get("subscriptions", {})
        if not isinstance(subscriptions, dict):
            subscriptions = {}

        if province is None:
            user_data["subscriptions"] = {}
            await self.persistence.update_user_data(user_id, user_data)
            return user_data

        normalized_province = self._validate_province(province)
        subscriptions.pop(normalized_province, None)
        user_data["subscriptions"] = subscriptions

        await self.persistence.update_user_data(user_id, user_data)
        return user_data

    async def get_user_subscriptions(self, user_id: int) -> dict:
        """Return user subscription mapping by province."""
        user_data = await self._get_user_data(user_id)
        subscriptions = user_data.get("subscriptions", {})

        if not isinstance(subscriptions, dict):
            subscriptions = {}

        normalized: dict[str, list[str]] = {}
        for province, times in subscriptions.items():
            if isinstance(province, str) and isinstance(times, list):
                valid_times = [time for time in times if isinstance(time, str)]
                normalized[province] = sorted(set(valid_times))

        return {"subscriptions": normalized}

    async def list_subscribers_by_province(self, province: str) -> list[int]:
        """List user IDs subscribed to the given province.

        Note:
            This performs an O(n) scan via HGETALL because there is currently no
            secondary province index.
        """
        normalized_province = self._validate_province(province)

        try:
            # TODO: Introduce a province -> user_ids secondary index to make this O(1)/O(log n).
            raw_user_map = await self.persistence.redis.hgetall(self.persistence.USER_DATA_KEY)
        except RedisConnectionError:
            return []

        subscribers: list[int] = []

        for raw_user_id, payload in raw_user_map.items():
            try:
                user_id = int(raw_user_id)
            except (TypeError, ValueError):
                continue

            data = self.persistence._deserialize(payload)
            subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
            if not isinstance(subscriptions, dict):
                continue

            province_times = subscriptions.get(normalized_province)
            if isinstance(province_times, list) and province_times:
                subscribers.append(user_id)

        return subscribers
