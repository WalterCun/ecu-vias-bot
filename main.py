""" main.py """
import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, filters, MessageHandler

from tortoise import Tortoise, connections
from colorama import init

from bot.libs.translate import trans

init(autoreset=True)

from bot.controller.start import start
from bot.controller.commands.cancel import cancel
from bot.controller.commands.config import config
from bot.controller.moderator import moderator
from bot.controller.notifications import notifications, alarm_notifications
from bot.controller.subscription import subscription
from bot.controller.unsubscription import unsubscription
from bot.libs.redis_persistence import RedisPersistence

from bot.db.manager import sync_db
from bot.settings import settings

# Enable logging
logging.basicConfig(
    format="<%(lineno)d> [%(asctime)s] - [%(filename)s / %(funcName)s] - [%(levelname)s] -> %(message)s",
    level=logging.INFO
)

# set a higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

DATABASE_CONFIG = {
    "connections": {
        # "default": "sqlite://test.db"  # Cambia a PostgreSQL/MySQL si lo necesitas
        "default": f'sqlite://{settings.BASE_DIR / settings.DB_NAME}'
        # "default": str(settings.BASE_DIR / settings.DB_NAME)
    },
    "apps": {
        "models": {
            # "models": ["post_model", "aerich.models"],
            "models": ['bot.db.models'],
            "default_connection": "default",
        }
    },
}


# Inicialización de la base de datos
async def init_db():
    """
    Initializes the Tortoise ORM and generates database schemas asynchronously.

    This function sets up the ORM by initializing it with the provided database configuration
    and then generates the necessary schemas for the database according to the defined models.

    Raises:
        ConfigurationError: If the provided database configuration is invalid.
        OperationalError: If there is an issue connecting to the database.
    """
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas()


# Cierre de la base de datos
async def close_db():
    """
    Closes all database connections managed by Tortoise ORM.

    This asynchronous function ensures that all active database connections are
    properly closed. It is used to clean up resources when the application shuts
    down or when database connections need to be explicitly terminated.

    Raises:
        TortoiseException: If there is an issue during connection closure.
    """
    await Tortoise.close_connections()


# Crear aplicación y añadir handlers
def main():
    """
    Main function to initialize database connection, build the bot application, register
    handlers, and start polling.

    Raises:
        Exception: An exception will propagate if initialization or application setup fails.
    """
    # Init database connect
    # run_async(init_db())
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_db())
    finally:
        loop.run_until_complete(connections.close_all(discard=True))

    persistence = RedisPersistence(settings.REDIS_URL)
    # Crear la aplicación del bot
    app = ApplicationBuilder().token(settings.TELEGRAM_KEY_BOT).persistence(persistence).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(filters.TEXT & filters.COMMAND, start)],
        states={
            settings.MODERATOR: [MessageHandler(filters.TEXT, moderator)],
            settings.SUBSCRIPTION: [MessageHandler(filters.TEXT, subscription)],
            settings.NOTIFICATIONS: [MessageHandler(filters.TEXT, notifications)],
            settings.ALARM_NOTIFICATIONS: [MessageHandler(filters.TEXT, alarm_notifications)],
            settings.UNSUBSCRIPTION: [MessageHandler(filters.TEXT, unsubscription)],
            settings.CONFIG: [MessageHandler(filters.TEXT, config)],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{trans.main.menu.btns.stop}$"), cancel)],
    )

    app.add_handler(conv_handler)
    logger.info("Iniciando Ejecucion de @ViasEC_bot")

    # Crear un segundo hilo para la limpieza de la base de datos
    asyncio.create_task(sync_db())

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error al ejecutar el bot: {e}")
    finally:
        asyncio.run(close_db())


if __name__ == '__main__':
    main()
