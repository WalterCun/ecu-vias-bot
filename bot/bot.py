""" src/bot.py """
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

from bot.controller.commands.cancel import cancel
from bot.controller import config
from bot.controller import language
from bot.controller import moderator
from bot.controller import notifications, alarm_notifications
from bot.controller import start
from bot.controller.subscription import subscription
from bot.controller import unsubscription
from bot.controller.utils.clean_text import clean_text
from bot.libs import RedisPersistence
from settings import settings

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

