"""Admin-only command handlers with user ID authorization."""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

LOGGER = logging.getLogger(__name__)

# Admin IDs from env var: comma-separated list of Telegram user IDs
# e.g., ADMIN_IDS=123456789,987654321
def _load_admin_ids() -> set[int]:
    """Load admin IDs from ADMIN_IDS environment variable."""
    raw = os.getenv("ADMIN_IDS", "")
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


ADMIN_IDS: set[int] = _load_admin_ids()


def is_admin(user_id: int) -> bool:
    """Check if a user ID is in the admin list."""
    return user_id in ADMIN_IDS


def admin_only(func: Callable) -> Callable:
    """Decorator that restricts a handler to admin users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        message = update.effective_message

        if user is None or message is None:
            return

        if not is_admin(user.id):
            await message.reply_text("⛔ No tienes permisos para este comando.")
            LOGGER.warning("Non-admin user %s tried to access admin command: %s", user.id, func.__name__)
            return

        return await func(update, context)

    return wrapper


def _get_services(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    """Get all services from bot_data."""
    return {
        "via_service": context.application.bot_data.get("via_service"),
        "via_sync_service": context.application.bot_data.get("via_sync_service"),
        "subscription_service": context.application.bot_data.get("subscription_service"),
        "scheduler": context.application.bot_data.get("scheduler"),
        "db_scheduler": context.application.bot_data.get("db_scheduler"),
    }


@admin_only
async def admin_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status (admin only)."""
    del context
    message = update.effective_message
    if message is None:
        return

    services = _get_services(context)
    lines = [
        "📊 *Estado del Bot*",
        "",
        f"Admins configurados: {len(ADMIN_IDS)}",
        f"Scheduler notificaciones: {'✅ Activo' if services['scheduler'] else '❌ Inactivo'}",
        f"Scheduler DB sync: {'✅ Activo' if services['db_scheduler'] else '❌ Inactivo'}",
    ]

    via_sync = services.get("via_sync_service")
    if via_sync:
        try:
            provinces = await via_sync.get_all_provinces()
            lines.append(f"Provincias en DB: {len(provinces)}")
        except Exception:
            lines.append("Provincias en DB: error al consultar")

    await message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def admin_sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force a DB sync from API (admin only)."""
    message = update.effective_message
    if message is None:
        return

    services = _get_services(context)
    via_service = services.get("via_service")
    via_sync = services.get("via_sync_service")

    if not via_service or not via_sync:
        await message.reply_text("❌ Servicios no disponibles.")
        return

    await message.reply_text("🔄 Sincronizando datos desde API...")

    try:
        vias_by_province = await via_service.get_latest_vias()
        all_rows = []
        for rows in vias_by_province.values():
            all_rows.extend(rows)

        if not all_rows:
            await message.reply_text("⚠️ No se obtuvieron datos de la API.")
            return

        stats = await via_sync.sync_vias(all_rows)
        await message.reply_text(
            f"✅ Sync completado:\n"
            f"- Creados: {stats['created']}\n"
            f"- Actualizados: {stats['updated']}\n"
            f"- Sin cambios: {stats['unchanged']}\n"
            f"- Errores: {stats['errors']}"
        )
    except Exception as exc:
        LOGGER.error("Admin sync failed: %s", exc)
        await message.reply_text(f"❌ Error en sync: {exc}")


@admin_only
async def admin_setinterval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change the DB sync interval (admin only)."""
    message = update.effective_message
    if message is None:
        return

    if not context.args:
        await message.reply_text(
            "Uso: /setinterval <segundos>\n"
            "Ejemplo: /setinterval 600 (10 minutos)"
        )
        return

    try:
        seconds = int(context.args[0])
        if seconds < 60:
            await message.reply_text("⚠️ Intervalo mínimo: 60 segundos.")
            return
    except ValueError:
        await message.reply_text("❌ Valor inválido. Usa un número en segundos.")
        return

    services = _get_services(context)
    db_scheduler = services.get("db_scheduler")

    if not db_scheduler:
        await message.reply_text("❌ Scheduler de DB no disponible.")
        return

    db_scheduler.interval_seconds = seconds
    await message.reply_text(f"✅ Intervalo de sync DB actualizado a *{seconds}s* ({seconds // 60} min).", parse_mode="Markdown")


@admin_only
async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to all subscribed users (admin only)."""
    message = update.effective_message
    if message is None:
        return

    if not context.args:
        await message.reply_text("Uso: /broadcast <mensaje>")
        return

    text = " ".join(context.args)
    services = _get_services(context)
    subscription_service = services.get("subscription_service")

    if not subscription_service:
        await message.reply_text("❌ Servicio de suscripciones no disponible.")
        return

    await message.reply_text(f"📡 Enviando broadcast a todos los suscriptores...")

    try:
        raw_user_map = await subscription_service.persistence.redis.hgetall(
            subscription_service.persistence.USER_DATA_KEY
        )
        sent = 0
        errors = 0

        for raw_user_id, payload in raw_user_map.items():
            try:
                user_id = int(raw_user_id)
                await context.bot.send_message(chat_id=user_id, text=text)
                sent += 1
            except Exception:
                errors += 1

        await message.reply_text(f"✅ Broadcast completado: {sent} enviados, {errors} errores.")
    except Exception as exc:
        await message.reply_text(f"❌ Error en broadcast: {exc}")


def register_admin_handlers(application: Application) -> None:
    """Register admin-only handlers on the application."""
    application.add_handler(CommandHandler("status", admin_status_handler))
    application.add_handler(CommandHandler("sync", admin_sync_handler))
    application.add_handler(CommandHandler("setinterval", admin_setinterval_handler))
    application.add_handler(CommandHandler("broadcast", admin_broadcast_handler))

    if ADMIN_IDS:
        LOGGER.info("Admin commands registered for %d admin(s): %s", len(ADMIN_IDS), ADMIN_IDS)
    else:
        LOGGER.warning("No ADMIN_IDS configured — admin commands will be inaccessible")
