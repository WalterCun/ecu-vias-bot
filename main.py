""" main.py """
import asyncio
import logging
import threading

from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, filters, MessageHandler

from tortoise import Tortoise
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
        "default": f'sqlite://{settings.BASE_DIR / settings.DB_NAME}'
    },
    "apps": {
        "models": {
            "models": ['bot.db.models'],
            "default_connection": "default",
        }
    },
}


async def init_db():
    """
    Initializes the Tortoise ORM and generates database schemas asynchronously.
    """
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas()


async def close_db():
    """
    Closes all database connections managed by Tortoise ORM.
    """
    await Tortoise.close_connections()


def start_sync_db_thread():
    """
    Inicia el hilo de sincronización de base de datos.
    """
    def run_sync_db():
        try:
            # Crear un bucle de eventos para este hilo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Ejecutar sync_db
            loop.run_until_complete(sync_db())
        except Exception as e:
            logger.error(f"Error en sync_db: {e}")
        finally:
            try:
                loop.close()
            except:
                pass

    # Crear y iniciar el hilo daemon
    thread = threading.Thread(target=run_sync_db, daemon=True)
    thread.start()
    logger.info("Hilo de sincronización de DB iniciado")
    return thread


async def run_application():
    """
    Función asíncrona principal que ejecuta la aplicación del bot.
    """
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("Base de datos inicializada correctamente")

        # Configurar persistencia y aplicación
        persistence = RedisPersistence(settings.REDIS_URL)
        app = ApplicationBuilder().token(settings.TELEGRAM_KEY_BOT).persistence(persistence).build()

        # Configurar conversation handler
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

        # Iniciar el hilo de sincronización de DB
        start_sync_db_thread()

        # Inicializar y ejecutar el bot
        async with app:
            await app.initialize()
            await app.start()

            # Ejecutar polling
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

            # Mantener el bot ejecutándose
            try:
                # Esperar indefinidamente hasta que se interrumpa
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            finally:
                # Detener polling y cerrar aplicación
                await app.updater.stop()
                await app.stop()
                await app.shutdown()

    except Exception as e:
        logger.error(f"Error al ejecutar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cerrar conexiones de base de datos
        try:
            await close_db()
            logger.info("Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"Error al cerrar la base de datos: {e}")


def main():
    """
    Main function to initialize and run the application.
    """
    try:
        # Ejecutar la aplicación asíncrona
        asyncio.run(run_application())
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico en main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()