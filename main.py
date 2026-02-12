"""Application entrypoint with production-ready lifecycle wiring."""

from __future__ import annotations

import asyncio
import logging
import os

from telegram.ext import Application

from bot.handlers import register_handlers
from bot.libs.redis_persistence import RedisJSONPersistence
from bot.services.api import ViasEcuadorAPI
from bot.services.notification_engine import NotificationEngine
from bot.services.notification_policy import NotificationPolicy
from bot.services.scheduler import AsyncScheduler
from bot.services.subscription_service import SubscriptionService
from bot.services.via_service import ViaService


def setup_logging() -> None:
    """Configure structured logging for the bot process."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(application: Application) -> None:
    """Start background scheduler after app initialization."""
    scheduler = application.bot_data.get("scheduler")
    if isinstance(scheduler, AsyncScheduler):
        await scheduler.start()


async def post_shutdown(application: Application) -> None:
    """Stop background scheduler before shutdown completes."""
    scheduler = application.bot_data.get("scheduler")
    if isinstance(scheduler, AsyncScheduler):
        await scheduler.stop()


async def create_application() -> Application:
    """Build and configure the Telegram application and background services."""
    token = os.getenv("TELEGRAM_KEY_BOT", "")
    if not token:
        raise ValueError("TELEGRAM_KEY_BOT environment variable is required")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    via_cache_ttl = int(os.getenv("VIA_CACHE_TTL", "60"))
    max_concurrent_sends = int(os.getenv("MAX_CONCURRENT_SENDS", "20"))

    persistence = RedisJSONPersistence(redis_url=redis_url)

    subscription_service = SubscriptionService(persistence)
    via_service = ViaService(http_client=ViasEcuadorAPI(), cache_ttl=via_cache_ttl)
    notification_policy = NotificationPolicy()

    application = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_handlers(application)

    notification_engine = NotificationEngine(
        via_service=via_service,
        subscription_service=subscription_service,
        notification_policy=notification_policy,
        bot=application.bot,
        max_concurrent_sends=max_concurrent_sends,
    )

    scheduler = AsyncScheduler(
        interval_seconds=60,
        task_callable=notification_engine.run_cycle,
    )

    application.bot_data["subscription_service"] = subscription_service
    application.bot_data["via_service"] = via_service
    application.bot_data["engine"] = notification_engine
    application.bot_data["scheduler"] = scheduler

    return application


def main() -> None:
    """Run polling application lifecycle."""
    setup_logging()
    application = asyncio.run(create_application())
    application.run_polling()


if __name__ == "__main__":
    main()
