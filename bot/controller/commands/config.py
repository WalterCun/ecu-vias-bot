from telegram import Update
from telegram.ext import ContextTypes

from bot.controller.menus.initial import initial_menu
from bot.settings import settings


async def config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Simple config endpoint to keep conversation stable."""
    await update.message.reply_text(
        "Configuraciones aún en desarrollo. Te devolvemos al menú principal.",
        reply_markup=initial_menu()
    )
    return settings.MODERATOR
