""" src/bot.py """
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

from src.controller.commands.cancel import cancel
from src.controller.commands.config import config
from src.controller.languages.translations import language
from src.controller.moderator import moderator
from src.controller.notifications import notifications, alarm_notifications
from src.controller.start import start
from src.controller.subscription import subscription
from src.controller.unsubscription import unsubscription
from src.controller.utils.clean_text import clean_text
from src.libs.redis_persistence import RedisPersistence
from src.settings.config import settings

logger = logging.getLogger(__name__)


def start_bot():
    """

    Start the Telegram bot with predefined handlers for conversation states and persistence.

    This function initializes the bot using the `telegram` library and sets up a conversation handler
    with various states to manage user interactions. The bot's persistence is managed through a
    PicklePersistence object, ensuring that data is stored between sessions.

    Handlers:
    - entry_points: Defines the commands and messages to initiate the conversation
    - states: Maps bot states to their respective message handlers
    - fallbacks: Specifies the message handler for stopping the conversation

    The bot is configured to log the start of its execution and run in polling mode.
    """
    persistence = RedisPersistence(settings.REDIS_URL)
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
        fallbacks=[MessageHandler(filters.Regex(f"^{clean_text(language.menu_buttons_stop)}$"), cancel)],
    )

    logger.info("Iniciando Ejecucion de @ViasEC_bot")
    app.add_handler(conv_handler)
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error al ejecutar el bot: {e}")
