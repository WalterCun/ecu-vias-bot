"""Application entrypoint — services initialized in post_init."""

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
    level = "DEBUG" if settings.DEBUG else "INFO"
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    # File logging if enabled
    if settings.GENERATE_LOGS:
        from pathlib import Path
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"bot_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # File always gets DEBUG
        handlers.append(file_handler)
        print(f"Logging to: {log_file}")

    logging.basicConfig(format=log_format, level=level, handlers=handlers)

    for lib in ("httpcore", "httpx", "telegram", "telegram.ext", "urllib3", "requests", "asyncio", "apscheduler"):
        logging.getLogger(lib).setLevel(logging.WARNING)


# ============== Job callbacks ==============

async def db_sync_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    via_service = context.bot_data.get("via_service")
    via_sync = context.bot_data.get("via_sync_service")

    if not via_service or not via_sync:
        logger.warning("DB sync job: services not available yet")
        return

    try:
        vias_by_province = await via_service.get_latest_vias()
        all_rows = []
        for rows in vias_by_province.values():
            all_rows.extend(rows)

        if all_rows:
            stats = await via_sync.sync_vias(all_rows)
            logger.info("DB sync complete: %s", stats)
        else:
            logger.warning("DB sync: no data from API")
    except Exception as exc:
        logger.error("DB sync failed: %s", exc)


async def notification_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    engine = context.bot_data.get("engine")
    if not engine:
        logger.warning("Notification job: engine not available yet")
        return

    try:
        await engine.run_cycle()
    except Exception as exc:
        logger.error("Notification job failed: %s", exc)


# ============== Lifecycle ==============

async def post_init(application: Application) -> None:
    """Initialize ALL services and schedule jobs. This runs after bot starts."""
    logger.info("Initializing services...")

    # Use the SAME persistence as Telegram (not a new one)
    persistence = application.persistence
    subscription_service = SubscriptionService(persistence)
    via_service = ViaService(http_client=ViasEcuadorAPI(), cache_ttl=settings.VIA_CACHE_TTL)
    via_sync_service = ViaSyncService()
    notification_policy = NotificationPolicy()

    notification_engine = NotificationEngine(
        via_service=via_service,
        subscription_service=subscription_service,
        notification_policy=notification_policy,
        bot=application.bot,
        max_concurrent_sends=settings.MAX_CONCURRENT_SENDS,
    )

    # Store in bot_data
    application.bot_data["subscription_service"] = subscription_service
    application.bot_data["via_service"] = via_service
    application.bot_data["via_sync_service"] = via_sync_service
    application.bot_data["engine"] = notification_engine
    logger.info("Services created and stored in bot_data")

    # Init DB
    try:
        await via_sync_service.init_db()
        logger.info("DB initialized")
    except Exception as exc:
        logger.error("DB init failed: %s", exc)

    # Initial sync
    try:
        await db_sync_job(application)
    except Exception as exc:
        logger.error("Initial DB sync failed: %s", exc)

    # Initial notification snapshot
    try:
        await notification_engine.run_cycle()
        logger.info("Initial notification snapshot stored")
    except Exception as exc:
        logger.error("Initial snapshot failed: %s", exc)

    # Schedule recurring jobs
    jq = application.job_queue
    if jq:
        jq.run_repeating(db_sync_job, interval=settings.DB_SYNC_INTERVAL_SECONDS, first=15, name="db_sync")
        jq.run_repeating(notification_job, interval=60, first=30, name="notification")
        logger.info("Jobs scheduled: db_sync every %ss, notification every 60s", settings.DB_SYNC_INTERVAL_SECONDS)
    else:
        logger.error("JobQueue not available!")


async def post_shutdown(application: Application) -> None:
    via_sync = application.bot_data.get("via_sync_service")
    if isinstance(via_sync, ViaSyncService):
        await via_sync.close_db()
        logger.info("DB closed")


def main() -> None:
    setup_logging()

    token = settings.TELEGRAM_KEY_BOT
    if not token:
        raise ValueError("TELEGRAM_KEY_BOT required in .env")

    persistence = RedisJSONPersistence(redis_url=settings.REDIS_URL)

    application = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_handlers(application)
    logger.info("Starting bot polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
