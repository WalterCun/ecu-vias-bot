"""Subscription service backed by SQLite (Tortoise ORM) instead of Redis."""

from __future__ import annotations

import logging
import re
from typing import Any

from bot.db.models import Subscription

LOGGER = logging.getLogger(__name__)


class SubscriptionService:
    """Manage user province/time subscriptions via SQLite."""

    _TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    def __init__(self, persistence: Any = None):
        """persistence is kept for API compatibility but not used."""
        self._persistence = persistence

    @staticmethod
    def _validate_province(province: str) -> str:
        if not isinstance(province, str):
            raise ValueError("province must be a string")
        normalized = province.strip().lower()
        if not normalized:
            raise ValueError("province must not be empty")
        return normalized

    @classmethod
    def _normalize_times(cls, times: list[str]) -> list[str]:
        if not isinstance(times, list):
            raise ValueError("times must be a list[str]")
        validated: set[str] = set()
        for value in times:
            if not isinstance(value, str):
                raise ValueError("invalid time format")
            candidate = value.strip()
            if not cls._TIME_PATTERN.match(candidate):
                raise ValueError(f"invalid time format: {candidate}")
            validated.add(candidate)
        return sorted(validated)

    async def subscribe(self, user_id: int, province: str, times: list[str]) -> dict:
        """Subscribe a user to a province and notification times."""
        normalized_province = self._validate_province(province)
        normalized_times = self._normalize_times(times)

        count = 0
        for time_str in normalized_times:
            _, created = await Subscription.get_or_create(
                user_id=user_id,
                province=normalized_province,
                notify_time=time_str,
                defaults={"active": True},
            )
            if not created:
                # Reactivate if it was deactivated
                sub = await Subscription.filter(
                    user_id=user_id,
                    province=normalized_province,
                    notify_time=time_str,
                ).first()
                if sub and not sub.active:
                    sub.active = True
                    await sub.save()
            count += 1

        LOGGER.info("Subscribed user %s to %s at %s", user_id, normalized_province, normalized_times)

        # Return in same format as before
        subs = await self.get_user_subscriptions(user_id)
        return {"subscriptions": subs["subscriptions"]}

    async def unsubscribe(self, user_id: int, province: str | None = None) -> dict:
        """Deactivate subscriptions for a user."""
        if province is None:
            # Deactivate all
            await Subscription.filter(user_id=user_id).update(active=False)
            LOGGER.info("Deactivated all subscriptions for user %s", user_id)
        else:
            normalized = self._validate_province(province)
            await Subscription.filter(
                user_id=user_id,
                province=normalized,
            ).update(active=False)
            LOGGER.info("Deactivated subscriptions for user %s province %s", user_id, normalized)

        subs = await self.get_user_subscriptions(user_id)
        return {"subscriptions": subs["subscriptions"]}

    async def get_user_subscriptions(self, user_id: int) -> dict:
        """Return active subscriptions grouped by province."""
        subs = await Subscription.filter(
            user_id=user_id,
            active=True,
        ).all()

        grouped: dict[str, list[str]] = {}
        for sub in subs:
            if sub.province not in grouped:
                grouped[sub.province] = []
            if sub.notify_time not in grouped[sub.province]:
                grouped[sub.province].append(sub.notify_time)

        # Sort times within each province
        for province in grouped:
            grouped[province] = sorted(set(grouped[province]))

        LOGGER.info("User %s subscriptions: %s", user_id, grouped)
        return {"subscriptions": grouped}

    async def list_subscribers_by_province(self, province: str) -> list[int]:
        """List user IDs subscribed to a province."""
        normalized = self._validate_province(province)
        subs = await Subscription.filter(
            province=normalized,
            active=True,
        ).all()

        user_ids = list({sub.user_id for sub in subs})
        LOGGER.debug("Province %s has %d subscribers", normalized, len(user_ids))
        return user_ids
