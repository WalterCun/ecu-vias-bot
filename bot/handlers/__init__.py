"""Basic Telegram handlers registration."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with a health-style confirmation message."""
    del context
    if update.effective_message is None:
        return
    await update.effective_message.reply_text("Bot activo y funcionando correctamente.")


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo plain text messages back to the user."""
    del context
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(message.text or "")


def register_handlers(application: Application) -> None:
    """Register core command and message handlers on the application."""
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
