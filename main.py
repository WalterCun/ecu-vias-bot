"""Application entrypoint with production-ready lifecycle wiring."""

from __future__ import annotations

import asyncio
import logging

from telegram.ext import Application

from bot.handlers import register_handlers
from bot.libs.redis_persistence import RedisJSONPersistence
from bot.services.api import ViasEcuadorAPI
from bot.services.notification_engine import NotificationEngine
from bot.services.notification_policy import NotificationPolicy
from bot.services.scheduler import AsyncScheduler
from bot.services.subscription_service import SubscriptionService
from bot.services.via_service import ViaService
from bot.services.via_sync_service import ViaSyncService
from bot.settings import settings


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure structured logging — only show our code and DB sync."""
    level = "DEBUG" if settings.DEBUG else "INFO"

    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=level,
    )

    # Silence noisy third-party libraries
    for lib in ("httpcore", "httpx", "telegram", "telegram.ext", "urllib3", "requests", "asyncio"):
        logging.getLogger(lib).setLevel(logging.WARNING)


async def post_init(application: Application) -> None:
    """Initialize DB and start background schedulers after app initialization."""
    # Init Tortoise ORM
    via_sync = application.bot_data.get("via_sync_service")
    if isinstance(via_sync, ViaSyncService):
        try:
            await via_sync.init_db()
            logger.info("DB initialized successfully")
        except Exception as exc:
            logger.error("Failed to init DB: %s — sync disabled", exc)

    # Run initial sync
    try:
        await _run_db_sync(application)
    except Exception as exc:
        logger.error("Initial DB sync failed: %s — will retry on schedule", exc)

    # Start notification scheduler
    scheduler = application.bot_data.get("scheduler")
    if isinstance(scheduler, AsyncScheduler):
        await scheduler.start()

    # Start DB sync scheduler
    db_scheduler = application.bot_data.get("db_scheduler")
    if isinstance(db_scheduler, AsyncScheduler):
        await db_scheduler.start()
        logger.info("DB sync scheduler started (every %ss)", db_scheduler.interval_seconds)
    else:
        logger.warning("DB sync scheduler not found in bot_data")


async def post_shutdown(application: Application) -> None:
    """Stop background services and close DB before shutdown."""
    scheduler = application.bot_data.get("scheduler")
    if isinstance(scheduler, AsyncScheduler):
        await scheduler.stop()

    db_scheduler = application.bot_data.get("db_scheduler")
    if isinstance(db_scheduler, AsyncScheduler):
        await db_scheduler.stop()

    via_sync = application.bot_data.get("via_sync_service")
    if isinstance(via_sync, ViaSyncService):
        await via_sync.close_db()


async def _run_db_sync(application: Application) -> None:
    """Fetch API data and sync to database."""
    via_service = application.bot_data.get("via_service")
    via_sync = application.bot_data.get("via_sync_service")

    if not via_service or not via_sync:
        return

    try:
        vias_by_province = await via_service.get_latest_vias()
        all_rows = []
        for rows in vias_by_province.values():
            all_rows.extend(rows)

        if all_rows:
            await via_sync.sync_vias(all_rows)
        else:
            logging.getLogger(__name__).warning("No API data to sync to DB")
    except Exception as exc:
        logging.getLogger(__name__).error("DB sync cycle failed: %s", exc)


async def create_application() -> Application:
    """Build and configure the Telegram application and background services."""
    token = settings.TELEGRAM_KEY_BOT
    if not token:
        raise ValueError("TELEGRAM_KEY_BOT is required in .env")

    persistence = RedisJSONPersistence(redis_url=settings.REDIS_URL)

    subscription_service = SubscriptionService(persistence)
    via_service = ViaService(http_client=ViasEcuadorAPI(), cache_ttl=settings.VIA_CACHE_TTL)
    via_sync_service = ViaSyncService()
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
        max_concurrent_sends=settings.MAX_CONCURRENT_SENDS,
    )

    # Notification scheduler (every 60s)
    scheduler = AsyncScheduler(
        interval_seconds=60,
        task_callable=notification_engine.run_cycle,
    )

    # DB sync scheduler (configurable, default 15 min)
    async def db_sync_task() -> None:
        await _run_db_sync(application)

    db_scheduler = AsyncScheduler(
        interval_seconds=settings.DB_SYNC_INTERVAL_SECONDS,
        task_callable=db_sync_task,
    )

    application.bot_data["subscription_service"] = subscription_service
    application.bot_data["via_service"] = via_service
    application.bot_data["via_sync_service"] = via_sync_service
    application.bot_data["engine"] = notification_engine
    application.bot_data["scheduler"] = scheduler
    application.bot_data["db_scheduler"] = db_scheduler

    return application


def main() -> None:
    """Run polling application lifecycle."""
    setup_logging()
    application = asyncio.run(create_application())
    application.run_polling()


if __name__ == "__main__":
    main()
