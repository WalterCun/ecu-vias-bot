"""Application entrypoint — uses telegram-telegram-bot's JobQueue for background tasks."""

from __future__ import annotations

import logging

from telegram.ext import Application, ContextTypes

from bot.handlers import register_handlers
from bot.libs.redis_persistence import RedisJSONPersistence
from bot.services.api import ViasEcuadorAPI
from bot.services.notification_engine import NotificationEngine
from bot.services.notification_policy import NotificationPolicy
from bot.services.subscription_service import SubscriptionService
from bot.services.via_service import ViaService
from bot.services.via_sync_service import ViaSyncService
from bot.settings import settings


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging — only show our code."""
    level = "DEBUG" if settings.DEBUG else "INFO"
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=level,
    )
    for lib in ("httpcore", "httpx", "telegram", "telegram.ext", "urllib3", "requests", "asyncio", "apscheduler"):
        logging.getLogger(lib).setLevel(logging.WARNING)


# ============== Job callbacks ==============

async def db_sync_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: sync API data to database."""
    via_service = context.bot_data.get("via_service")
    via_sync = context.bot_data.get("via_sync_service")

    if not via_service or not via_sync:
        logger.warning("DB sync job: services not available")
        return

    try:
        vias_by_province = await via_service.get_latest_vias()
        all_rows = []
        for rows in vias_by_province.values():
            all_rows.extend(rows)

        if all_rows:
            stats = await via_sync.sync_vias(all_rows)
            logger.info("DB sync job complete: %s", stats)
        else:
            logger.warning("DB sync job: no data from API")
    except Exception as exc:
        logger.error("DB sync job failed: %s", exc)


async def notification_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: check for changes and notify subscribers."""
    engine = context.bot_data.get("engine")
    if not engine:
        return

    try:
        await engine.run_cycle()
    except Exception as exc:
        logger.error("Notification job failed: %s", exc)


# ============== App lifecycle ==============

async def post_init(application: Application) -> None:
    """Initialize services and schedule jobs after bot starts."""
    # Init DB
    via_sync = application.bot_data.get("via_sync_service")
    if isinstance(via_sync, ViaSyncService):
        try:
            await via_sync.init_db()
            logger.info("DB initialized successfully")
        except Exception as exc:
            logger.error("Failed to init DB: %s", exc)

    # Run initial DB sync
    try:
        await db_sync_job(application)
    except Exception as exc:
        logger.error("Initial DB sync failed: %s", exc)

    # Run initial notification snapshot
    engine = application.bot_data.get("engine")
    if engine:
        try:
            await engine.run_cycle()
            logger.info("Initial notification snapshot stored")
        except Exception as exc:
            logger.error("Initial notification snapshot failed: %s", exc)

    # Schedule recurring jobs via JobQueue
    jq = application.job_queue
    if jq:
        # DB sync every N seconds
        jq.run_repeating(
            db_sync_job,
            interval=settings.DB_SYNC_INTERVAL_SECONDS,
            first=10,
            name="db_sync",
        )
        logger.info("DB sync job scheduled (every %ss)", settings.DB_SYNC_INTERVAL_SECONDS)

        # Notification check every 60s
        jq.run_repeating(
            notification_job,
            interval=60,
            first=30,
            name="notification_check",
        )
        logger.info("Notification job scheduled (every 60s)")
    else:
        logger.error("JobQueue not available — install python-telegram-bot[job-queue]")


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    via_sync = application.bot_data.get("via_sync_service")
    if isinstance(via_sync, ViaSyncService):
        await via_sync.close_db()
        logger.info("DB connections closed")


async def create_application() -> Application:
    """Build and configure the Telegram application."""
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

    application.bot_data["subscription_service"] = subscription_service
    application.bot_data["via_service"] = via_service
    application.bot_data["via_sync_service"] = via_sync_service
    application.bot_data["engine"] = notification_engine

    logger.info("Application configured")
    return application


def main() -> None:
    """Run the bot with polling."""
    setup_logging()
    application = asyncio.run(create_application())
    application.run_polling()


if __name__ == "__main__":
    import asyncio
    main()
