"""Telegram handlers registration for basic subscription and echo flows."""

from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


DEFAULT_SUBSCRIPTION_TIME = "08:00"


def _get_services(context: ContextTypes.DEFAULT_TYPE) -> tuple[Any, Any]:
    """Get service instances from application bot_data."""
    subscription_service = context.application.bot_data.get("subscription_service")
    notification_engine = context.application.bot_data.get("engine")
    return subscription_service, notification_engine


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with a health-style confirmation message."""
    del context
    if update.effective_message is None:
        return
    await update.effective_message.reply_text("Bot activo y funcionando correctamente.")


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe user to a province using services from app context."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine = _get_services(context)
    del notification_engine

    if subscription_service is None:
        await message.reply_text("Servicio de suscripciones no disponible.")
        return

    if not context.args:
        await message.reply_text("Uso: /subscribe <province>")
        return

    province = context.args[0].strip().lower()
    if not province:
        await message.reply_text("Provincia inválida.")
        return

    try:
        await subscription_service.subscribe(user.id, province, [DEFAULT_SUBSCRIPTION_TIME])
    except ValueError as exc:
        await message.reply_text(f"Error de validación: {exc}")
        return
    except Exception:
        await message.reply_text("No se pudo registrar la suscripción en este momento.")
        return

    await message.reply_text(f"Suscripción registrada para {province}.")


async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe user from a province using services from app context."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine = _get_services(context)
    del notification_engine

    if subscription_service is None:
        await message.reply_text("Servicio de suscripciones no disponible.")
        return

    if not context.args:
        await message.reply_text("Uso: /unsubscribe <province>")
        return

    province = context.args[0].strip().lower()

    try:
        await subscription_service.unsubscribe(user.id, province)
    except ValueError as exc:
        await message.reply_text(f"Error de validación: {exc}")
        return
    except Exception:
        await message.reply_text("No se pudo eliminar la suscripción en este momento.")
        return

    await message.reply_text(f"Suscripción eliminada para {province}.")


async def mysubscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the current user subscriptions list."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine = _get_services(context)
    del notification_engine

    if subscription_service is None:
        await message.reply_text("Servicio de suscripciones no disponible.")
        return

    try:
        data = await subscription_service.get_user_subscriptions(user.id)
    except Exception:
        await message.reply_text("No se pudieron obtener tus suscripciones.")
        return

    subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
    if not subscriptions:
        await message.reply_text("No tienes suscripciones activas.")
        return

    lines = ["Tus suscripciones:"]
    for province, times in subscriptions.items():
        if isinstance(times, list) and times:
            lines.append(f"- {province}: {', '.join(times)}")
        else:
            lines.append(f"- {province}")

    await message.reply_text("\n".join(lines))


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
    application.add_handler(CommandHandler("subscribe", subscribe_handler))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    application.add_handler(CommandHandler("mysubscriptions", mysubscriptions_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
