"""Notification orchestration engine."""

from __future__ import annotations

import asyncio
import copy
import logging
from typing import Any

from telegram.error import RetryAfter, TelegramError, TimedOut


LOGGER = logging.getLogger(__name__)


class NotificationEngine:
    """Coordinate vias changes detection and subscriber notifications."""

    def __init__(
        self,
        via_service: Any,
        subscription_service: Any,
        notification_policy: Any,
        bot: Any,
        max_concurrent_sends: int = 20,
    ) -> None:
        """Initialize notification engine dependencies."""
        self.via_service = via_service
        self.subscription_service = subscription_service
        self.notification_policy = notification_policy
        self.bot = bot
        self._send_semaphore = asyncio.Semaphore(max(1, max_concurrent_sends))
        self._last_vias: dict[str, list[dict[str, Any]]] = {}

    @staticmethod
    def _build_message(province: str, changes: dict[str, list[dict[str, Any]]]) -> str:
        """Build a human-readable message from change groups."""
        lines = [f"Actualizaciones de vías en {province}:"]

        new_items = changes.get("new", [])
        removed_items = changes.get("removed", [])
        updated_items = changes.get("updated", [])

        if new_items:
            lines.append(f"- Nuevas incidencias: {len(new_items)}")
        if removed_items:
            lines.append(f"- Incidencias removidas: {len(removed_items)}")
        if updated_items:
            lines.append(f"- Incidencias actualizadas: {len(updated_items)}")

        return "\n".join(lines)

    async def _safe_send(self, user_id: int, text: str) -> None:
        """Send a notification with retries for transient Telegram errors."""
        async with self._send_semaphore:
            try:
                await self.bot.send_message(chat_id=user_id, text=text)
                return
            except RetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after))
                try:
                    await self.bot.send_message(chat_id=user_id, text=text)
                except TelegramError as retry_exc:
                    LOGGER.error("Failed to send notification after RetryAfter to user %s: %s", user_id, retry_exc)
                except Exception as retry_exc:  # noqa: BLE001
                    LOGGER.error("Unexpected retry error for user %s: %s", user_id, retry_exc)
                return
            except TimedOut:
                await asyncio.sleep(1)
                try:
                    await self.bot.send_message(chat_id=user_id, text=text)
                except TelegramError as retry_exc:
                    LOGGER.error("Failed to send notification after timeout retry to user %s: %s", user_id, retry_exc)
                except Exception as retry_exc:  # noqa: BLE001
                    LOGGER.error("Unexpected timeout retry error for user %s: %s", user_id, retry_exc)
                return
            except TelegramError as exc:
                LOGGER.error("Failed to send notification to user %s: %s", user_id, exc)
                return
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Unexpected send error for user %s: %s", user_id, exc)
                return

    async def run_cycle(self) -> None:
        """Run one notification cycle: fetch, compare, notify, and update state."""
        try:
            latest_vias = await self.via_service.get_latest_vias()
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to fetch latest vias: %s", exc)
            return

        if not isinstance(latest_vias, dict):
            LOGGER.error("Invalid vias payload received; expected dict, got %s", type(latest_vias).__name__)
            return

        if not self._last_vias:
            self._last_vias = copy.deepcopy(latest_vias)
            return

        try:
            changes = self.notification_policy.compare(self._last_vias, latest_vias)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to compare vias changes: %s", exc)
            return

        if not isinstance(changes, dict):
            LOGGER.error("Invalid policy output; expected dict, got %s", type(changes).__name__)
            self._last_vias = copy.deepcopy(latest_vias)
            return

        for province, province_changes in changes.items():
            try:
                if not isinstance(province_changes, dict):
                    continue

                has_changes = any(
                    province_changes.get(change_type)
                    for change_type in ("new", "removed", "updated")
                )
                if not has_changes:
                    continue

                subscribers = await self.subscription_service.list_subscribers_by_province(province)
                if not subscribers:
                    continue

                message = self._build_message(province, province_changes)
                tasks = [self._safe_send(user_id, message) for user_id in subscribers]
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed processing notifications for province %s: %s", province, exc)
                continue

        self._last_vias = copy.deepcopy(latest_vias)
