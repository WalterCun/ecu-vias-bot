"""Notification orchestration engine with time-aware scheduling."""

from __future__ import annotations

import asyncio
import copy
import logging
from datetime import datetime
from typing import Any

import pytz
from telegram.error import RetryAfter, TelegramError, TimedOut


LOGGER = logging.getLogger(__name__)
ECUADOR_TZ = pytz.timezone("America/Guayaquil")


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
        # Track which users were notified this cycle to avoid duplicates
        self._notified_this_cycle: set[tuple[int, str]] = set()
        # Track the last notification hour per user+province to avoid re-sending
        self._last_notification_hour: dict[str, str] = {}

    @staticmethod
    def _build_message(province: str, changes: dict[str, list[dict[str, Any]]]) -> str:
        """Build a human-readable message from change groups."""
        lines = [f"🛣️ *Actualizaciones de vías en {province.title()}:*\n"]

        new_items = changes.get("new", [])
        removed_items = changes.get("removed", [])
        updated_items = changes.get("updated", [])

        if new_items:
            lines.append(f"🆕 *Nuevas incidencias:* {len(new_items)}")
            for item in new_items[:5]:
                desc = item.get("descripcion", item.get("via", "?"))
                lines.append(f"   • {desc}")
            if len(new_items) > 5:
                lines.append(f"   _...y {len(new_items) - 5} más_")

        if updated_items:
            lines.append(f"\n🔄 *Actualizadas:* {len(updated_items)}")
            for item in updated_items[:3]:
                desc = item.get("descripcion", item.get("via", "?"))
                lines.append(f"   • {desc}")

        if removed_items:
            lines.append(f"\n✅ *Resueltas:* {len(removed_items)}")

        lines.append(f"\n_Hora: {datetime.now(ECUADOR_TZ).strftime('%H:%M')} (EC)_")
        return "\n".join(lines)

    def _should_notify_user(self, user_id: int, province: str, scheduled_times: list[str]) -> bool:
        """Check if it's time to notify this user for this province based on their schedule."""
        if not scheduled_times:
            return False

        now_ec = datetime.now(ECUADOR_TZ)
        current_time = now_ec.strftime("%H:%M")
        current_hour = now_ec.strftime("%H")

        # Check if current time matches any scheduled time (within 1 minute window)
        for scheduled in scheduled_times:
            sched_hour, sched_min = scheduled.split(":")
            curr_hour, curr_min = current_time.split(":")

            # Match if same hour and within 1 minute
            if sched_hour == curr_hour:
                sched_min_int = int(sched_min)
                curr_min_int = int(curr_min)
                if abs(sched_min_int - curr_min_int) <= 1:
                    # Check if already notified this hour
                    key = f"{user_id}:{province}:{current_hour}"
                    if key not in self._last_notification_hour:
                        self._last_notification_hour[key] = current_hour
                        return True

        return False

    async def _safe_send(self, user_id: int, text: str) -> None:
        """Send a notification with retries for transient Telegram errors."""
        async with self._send_semaphore:
            try:
                await self.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                return
            except RetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after))
                try:
                    await self.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                except TelegramError as retry_exc:
                    LOGGER.error("Failed send after RetryAfter to user %s: %s", user_id, retry_exc)
                except Exception as retry_exc:  # noqa: BLE001
                    LOGGER.error("Unexpected retry error for user %s: %s", user_id, retry_exc)
                return
            except TimedOut:
                await asyncio.sleep(1)
                try:
                    await self.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                except TelegramError as retry_exc:
                    LOGGER.error("Failed send after timeout to user %s: %s", user_id, retry_exc)
                except Exception as retry_exc:  # noqa: BLE001
                    LOGGER.error("Unexpected timeout error for user %s: %s", user_id, retry_exc)
                return
            except TelegramError as exc:
                LOGGER.error("Failed to send notification to user %s: %s", user_id, exc)
                return
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Unexpected send error for user %s: %s", user_id, exc)
                return

    async def run_cycle(self) -> None:
        """Run one notification cycle: fetch, compare, check schedules, notify."""
        try:
            latest_vias = await self.via_service.get_latest_vias()
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to fetch latest vias: %s", exc)
            return

        if not isinstance(latest_vias, dict):
            LOGGER.error("Invalid vias payload; expected dict, got %s", type(latest_vias).__name__)
            return

        # First cycle: just store snapshot
        if not self._last_vias:
            self._last_vias = copy.deepcopy(latest_vias)
            return

        try:
            changes = self.notification_policy.compare(self._last_vias, latest_vias)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to compare vias changes: %s", exc)
            self._last_vias = copy.deepcopy(latest_vias)
            return

        if not isinstance(changes, dict):
            LOGGER.error("Invalid policy output; expected dict, got %s", type(changes).__name__)
            self._last_vias = copy.deepcopy(latest_vias)
            return

        now_ec = datetime.now(ECUADOR_TZ)

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

                for user_id in subscribers:
                    # Get user's scheduled times for this province
                    try:
                        user_data = await self.subscription_service.get_user_subscriptions(user_id)
                        subs = user_data.get("subscriptions", {})
                        scheduled_times = subs.get(province, ["08:00"])
                    except Exception:
                        scheduled_times = ["08:00"]

                    # Check if it's time to notify
                    if self._should_notify_user(user_id, province, scheduled_times):
                        await self._safe_send(user_id, message)
                        LOGGER.info("Notified user %s for province %s at %s", user_id, province, now_ec.strftime("%H:%M"))

            except Exception as exc:  # noqa: BLE001
                LOGGER.error("Failed processing notifications for province %s: %s", province, exc)
                continue

        self._last_vias = copy.deepcopy(latest_vias)

        # Cleanup old notification tracking (keep last 24h)
        if now_ec.hour == 0 and now_ec.minute < 2:
            self._last_notification_hour.clear()
            LOGGER.info("Cleared notification hour tracking for new day")

    async def force_notify_user(self, user_id: int, province: str) -> str:
        """Force-send current via status to a specific user (admin use)."""
        try:
            latest_vias = await self.via_service.get_latest_vias()
            vias = latest_vias.get(province.lower(), [])
            if not vias:
                return f"No hay datos de vías para {province}."

            lines = [f"🛣️ *Estado actual de vías en {province.title()}:*\n"]
            for via in vias[:15]:
                desc = via.get("descripcion", "?")
                estado = via.get("EstadoActual", {}).get("nombre", via.get("estado", "?"))
                icono = "🟢" if str(estado).lower() in ("abierta", "a", "activa") else "🔴"
                lines.append(f"{icono} {desc} — *{estado}*")

            message = "\n".join(lines)
            await self._safe_send(user_id, message)
            return f"Enviado a usuario {user_id}"
        except Exception as exc:
            return f"Error: {exc}"
