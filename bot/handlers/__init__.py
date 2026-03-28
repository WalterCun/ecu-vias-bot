"""Telegram handlers registration for basic subscription and echo flows."""

from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


DEFAULT_SUBSCRIPTION_TIME = "08:00"


def _get_services(context: ContextTypes.DEFAULT_TYPE) -> tuple[Any, Any, Any]:
    """Get service instances from application bot_data."""
    subscription_service = context.application.bot_data.get("subscription_service")
    notification_engine = context.application.bot_data.get("engine")
    via_sync_service = context.application.bot_data.get("via_sync_service")
    return subscription_service, notification_engine, via_sync_service


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with a health-style confirmation message."""
    del context
    if update.effective_message is None:
        return
    await update.effective_message.reply_text(
        "🛣️ *Bot ECU Vías activo*\n\n"
        "Comandos disponibles:\n"
        "/vias <provincia> — Ver estado de vías\n"
        "/subscribe <provincia> — Suscribirse a alertas\n"
        "/unsubscribe <provincia> — Cancelar suscripción\n"
        "/mysubscriptions — Ver mis suscripciones",
        parse_mode="Markdown",
    )


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe user to a province using services from app context."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine, _ = _get_services(context)
    del notification_engine

    if subscription_service is None:
        await message.reply_text("Servicio de suscripciones no disponible.")
        return

    if not context.args:
        await message.reply_text("Uso: /subscribe <provincia>")
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

    await message.reply_text(f"✅ Suscripción registrada para *{province}*.", parse_mode="Markdown")


async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe user from a province using services from app context."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine, _ = _get_services(context)
    del notification_engine

    if subscription_service is None:
        await message.reply_text("Servicio de suscripciones no disponible.")
        return

    if not context.args:
        await message.reply_text("Uso: /unsubscribe <provincia>")
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

    await message.reply_text(f"🗑️ Suscripción eliminada para *{province}*.", parse_mode="Markdown")


async def mysubscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the current user subscriptions list."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    subscription_service, notification_engine, _ = _get_services(context)
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

    lines = ["📋 *Tus suscripciones:*"]
    for province, times in subscriptions.items():
        if isinstance(times, list) and times:
            lines.append(f"- {province}: {', '.join(times)}")
        else:
            lines.append(f"- {province}")

    await message.reply_text("\n".join(lines), parse_mode="Markdown")


async def vias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Query road status from the database for a given province."""
    message = update.effective_message
    if message is None:
        return

    _, _, via_sync_service = _get_services(context)

    if via_sync_service is None:
        await message.reply_text("Servicio de vías no disponible.")
        return

    if not context.args:
        # Show available provinces
        try:
            provinces = await via_sync_service.get_all_provinces()
        except Exception:
            await message.reply_text("No se pudieron obtener las provincias.")
            return

        if not provinces:
            await message.reply_text("No hay datos de vías en la base de datos aún.")
            return

        provinces_list = "\n".join(f"- {p}" for p in provinces)
        await message.reply_text(
            f"📍 *Provincias disponibles:*\n{provinces_list}\n\nUsa: /vias <provincia>",
            parse_mode="Markdown",
        )
        return

    province = " ".join(context.args).strip()

    try:
        vias = await via_sync_service.get_vias_by_province(province)
    except Exception:
        await message.reply_text("Error al consultar la base de datos.")
        return

    if not vias:
        await message.reply_text(f"No se encontraron vías para *{province}*.", parse_mode="Markdown")
        return

    lines = [f"🛣️ *Vías en {province}:*\n"]
    for via in vias[:20]:  # Limit to 20 results
        estado = via.get("estado_actual") or via.get("estado", "?")
        icono = "🟢" if estado.lower() in ("abierta", "a", "activa") else "🔴"
        obs = via.get("observaciones", "")
        obs_text = f"\n   _{obs}_" if obs else ""
        lines.append(f"{icono} {via['descripcion']} — *{estado}*{obs_text}")

    if len(vias) > 20:
        lines.append(f"\n_...y {len(vias) - 20} vías más_")

    await message.reply_text("\n".join(lines), parse_mode="Markdown")


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo plain text messages back to the user."""
    del context
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(message.text or "")


def register_handlers(application: Application) -> None:
    """Register core command and message handlers on the application."""
    # User commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("vias", vias_handler))
    application.add_handler(CommandHandler("subscribe", subscribe_handler))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    application.add_handler(CommandHandler("mysubscriptions", mysubscriptions_handler))

    # Admin commands
    from bot.handlers.admin import register_admin_handlers
    register_admin_handlers(application)

    # Echo (fallback)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
