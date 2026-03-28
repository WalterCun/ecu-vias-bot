"""Telegram handlers registration with interactive menus and conversation flows."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from bot.settings.const import PROVINCES

LOGGER = logging.getLogger(__name__)

# Conversation states
MENU, SELECT_PROVINCE, SELECT_TIME, CONFIG_MENU = range(4)

DEFAULT_SUBSCRIPTION_TIME = "08:00"

# Time options for notification schedule
TIME_OPTIONS = [
    "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00", "22:00",
]


def _get_services(context: ContextTypes.DEFAULT_TYPE) -> tuple[Any, Any, Any, Any]:
    """Get service instances from application bot_data."""
    subscription_service = context.application.bot_data.get("subscription_service")
    notification_engine = context.application.bot_data.get("engine")
    via_sync_service = context.application.bot_data.get("via_sync_service")
    via_service = context.application.bot_data.get("via_service")
    return subscription_service, notification_engine, via_sync_service, via_service


def _main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the main menu keyboard."""
    keyboard = [
        [KeyboardButton("🛣️ Consultar Vías"), KeyboardButton("📋 Mis Suscripciones")],
        [KeyboardButton("🔔 Suscribirse"), KeyboardButton("🔕 Cancelar Suscripción")],
        [KeyboardButton("⚙️ Configuración"), KeyboardButton("ℹ️ Ayuda")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def _provinces_keyboard() -> ReplyKeyboardMarkup:
    """Build keyboard with Ecuador provinces."""
    keyboard = []
    row = []
    for i, province in enumerate(PROVINCES):
        row.append(KeyboardButton(province))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("✅ Continuar"), KeyboardButton("🔙 Volver")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def _time_keyboard() -> ReplyKeyboardMarkup:
    """Build keyboard with time options."""
    keyboard = []
    row = []
    for i, time_opt in enumerate(TIME_OPTIONS):
        row.append(KeyboardButton(time_opt))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("✅ Confirmar"), KeyboardButton("🔙 Volver")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# ============== Command Handlers ==============

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start — show main menu."""
    user = update.effective_user
    message = update.effective_message
    if message is None or user is None:
        return MENU

    LOGGER.info("User %s (%s) started bot", user.id, user.first_name)
    name = user.first_name or "Usuario"
    await message.reply_text(
        f"🛣️ *¡Hola {name}! Bienvenido al Bot de Vías ECU*\n\n"
        "¿Qué deseas hacer?",
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )
    return MENU


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /help or Ayuda button."""
    message = update.effective_message
    if message is None:
        return MENU

    await message.reply_text(
        "ℹ️ *Comandos disponibles:*\n\n"
        "🛣️ *Consultar Vías* — Ver estado de vías por provincia\n"
        "🔔 *Suscribirse* — Recibir alertas de vías\n"
        "🔕 *Cancelar Suscripción* — Dejar de recibir alertas\n"
        "📋 *Mis Suscripciones* — Ver tus suscripciones activas\n\n"
        "También puedes usar comandos:\n"
        "/start — Menú principal\n"
        "/vias <provincia> — Consultar vías\n"
        "/subscribe <provincia> — Suscribirse\n"
        "/unsubscribe <provincia> — Cancelar\n"
        "/mysubscriptions — Ver suscripciones",
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )
    return MENU


async def vias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /vias or 'Consultar Vías' button."""
    message = update.effective_message
    if message is None:
        return MENU

    # If called with argument (e.g., /vias Azuay)
    if context.args:
        province = " ".join(context.args).strip()
        _, _, via_sync_service = _get_services(context)
        if via_sync_service:
            try:
                vias = await via_sync_service.get_vias_by_province(province)
                if vias:
                    lines = [f"🛣️ *Vías en {province}:*\n"]
                    for via in vias[:15]:
                        estado = via.get("estado_actual") or via.get("estado", "?")
                        icono = "🟢" if estado.lower() in ("abierta", "a", "activa") else "🔴"
                        obs = via.get("observaciones", "")
                        obs_text = f"\n   _{obs}_" if obs else ""
                        lines.append(f"{icono} {via['descripcion']} — *{estado}*{obs_text}")
                    if len(vias) > 15:
                        lines.append(f"\n_...y {len(vias) - 15} vías más_")
                    await message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=_main_menu_keyboard())
                else:
                    await message.reply_text(f"No hay vías para *{province}*. Usa el menú para seleccionar.", parse_mode="Markdown", reply_markup=_provinces_keyboard())
            except Exception:
                await message.reply_text("Error al consultar la base de datos.", reply_markup=_main_menu_keyboard())
        else:
            await message.reply_text("Servicio no disponible.", reply_markup=_main_menu_keyboard())
        return MENU

    # Show provinces for selection
    _, _, via_sync_service = _get_services(context)
    context.user_data["flow"] = "vias"  # Track that we're in via query mode

    if via_sync_service:
        try:
            provinces = await via_sync_service.get_all_provinces()
            if provinces:
                provinces_list = "\n".join(f"- {p}" for p in provinces[:20])
                await message.reply_text(
                    f"📍 *Provincias con datos:*\n{provinces_list}\n\n"
                    "Escribe el nombre de la provincia o usa /vias <provincia>",
                    parse_mode="Markdown",
                    reply_markup=_provinces_keyboard(),
                )
                return SELECT_PROVINCE
        except Exception:
            pass

    # Fallback: show all provinces
    await message.reply_text(
        "Selecciona una provincia para ver el estado de sus vías:",
        reply_markup=_provinces_keyboard(),
    )
    return SELECT_PROVINCE


async def mysubscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /mysubscriptions or button."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return MENU

    subscription_service, _, _ = _get_services(context)
    if subscription_service is None:
        await message.reply_text("Servicio no disponible.", reply_markup=_main_menu_keyboard())
        return MENU

    try:
        data = await subscription_service.get_user_subscriptions(user.id)
    except Exception:
        await message.reply_text("No se pudieron obtener tus suscripciones.", reply_markup=_main_menu_keyboard())
        return MENU

    subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
    if not subscriptions:
        await message.reply_text("No tienes suscripciones activas.", reply_markup=_main_menu_keyboard())
        return MENU

    lines = ["📋 *Tus suscripciones:*"]
    for province, times in subscriptions.items():
        if isinstance(times, list) and times:
            lines.append(f"- {province}: {', '.join(times)}")
        else:
            lines.append(f"- {province}")

    await message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=_main_menu_keyboard())
    return MENU


async def subscribe_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /subscribe or 'Suscribirse' button — show provinces."""
    message = update.effective_message
    if message is None:
        return MENU

    # If called with argument (e.g., /subscribe azuay)
    if context.args:
        province = context.args[0].strip().lower()
        subscription_service, _, _ = _get_services(context)
        if subscription_service:
            try:
                await subscription_service.subscribe(update.effective_user.id, province, [DEFAULT_SUBSCRIPTION_TIME])
                await message.reply_text(
                    f"✅ Suscrito a *{province}* (notificaciones a las {DEFAULT_SUBSCRIPTION_TIME})",
                    parse_mode="Markdown",
                    reply_markup=_main_menu_keyboard(),
                )
            except ValueError as exc:
                await message.reply_text(f"Error: {exc}", reply_markup=_main_menu_keyboard())
            except Exception:
                await message.reply_text("No se pudo registrar la suscripción.", reply_markup=_main_menu_keyboard())
        return MENU

    # Store selected provinces in context
    context.user_data["subscribe_provinces"] = []
    context.user_data["flow"] = "subscribe"  # Track that we're in subscription mode
    await message.reply_text(
        "🔔 *Suscribirse a alertas de vías*\n\n"
        "Selecciona las provincias que te interesan.\n"
        "Presiona ✅ Continuar cuando termines.",
        parse_mode="Markdown",
        reply_markup=_provinces_keyboard(),
    )
    return SELECT_PROVINCE


async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /unsubscribe or 'Cancelar Suscripción' button."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return MENU

    subscription_service, _, _ = _get_services(context)
    if subscription_service is None:
        await message.reply_text("Servicio no disponible.", reply_markup=_main_menu_keyboard())
        return MENU

    if context.args:
        province = context.args[0].strip().lower()
        try:
            await subscription_service.unsubscribe(user.id, province)
            await message.reply_text(
                f"🗑️ Suscripción cancelada para *{province}*",
                parse_mode="Markdown",
                reply_markup=_main_menu_keyboard(),
            )
        except Exception:
            await message.reply_text("Error al cancelar suscripción.", reply_markup=_main_menu_keyboard())
        return MENU

    # Show current subscriptions for cancellation
    try:
        data = await subscription_service.get_user_subscriptions(user.id)
        subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
        if not subscriptions:
            await message.reply_text("No tienes suscripciones activas.", reply_markup=_main_menu_keyboard())
            return MENU

        context.user_data["flow"] = "unsubscribe"

        # Build keyboard with subscribed provinces
        keyboard = []
        row = []
        for i, province in enumerate(subscriptions.keys()):
            row.append(KeyboardButton(f"🗑️ {province}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([KeyboardButton("🔙 Volver")])

        await message.reply_text(
            "🔕 *Cancelar suscripción*\n\nSelecciona la provincia:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        return SELECT_PROVINCE
    except Exception:
        await message.reply_text("Error al obtener suscripciones.", reply_markup=_main_menu_keyboard())
        return MENU


# ============== State Handlers ==============

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button presses."""
    message = update.effective_message
    text = message.text if message else ""
    user = update.effective_user

    LOGGER.info("User %s pressed menu: %s", user.id if user else "?", text[:30])

    if "Consultar Vías" in text or "vias" in text.lower():
        return await vias_handler(update, context)
    elif "Mis Suscripciones" in text or "subscriptions" in text.lower():
        return await mysubscriptions_handler(update, context)
    elif "Suscribirse" in text or "subscribe" in text.lower():
        return await subscribe_start(update, context)
    elif "Cancelar" in text or "unsubscribe" in text.lower():
        return await unsubscribe_handler(update, context)
    elif "Configuración" in text or "config" in text.lower():
        return await config_handler(update, context)
    elif "Ayuda" in text or "help" in text.lower():
        return await help_handler(update, context)
    else:
        await message.reply_text(
            "Selecciona una opción del menú:",
            reply_markup=_main_menu_keyboard(),
        )
        return MENU


async def config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /config or 'Configuración' button — show user settings."""
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return MENU

    subscription_service, _, _ = _get_services(context)

    # Get current subscriptions
    subs_text = "No tienes suscripciones activas."
    if subscription_service:
        try:
            data = await subscription_service.get_user_subscriptions(user.id)
            subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
            if subscriptions:
                lines = []
                for province, times in subscriptions.items():
                    lines.append(f"  • {province}: {', '.join(times)}")
                subs_text = "\n".join(lines)
        except Exception:
            pass

    keyboard = [
        [KeyboardButton("🕐 Cambiar Horario"), KeyboardButton("🌍 Cambiar Idioma")],
        [KeyboardButton("🗑️ Borrar Todas las Suscripciones")],
        [KeyboardButton("🔙 Volver")],
    ]

    await message.reply_text(
        f"⚙️ *Configuración*\n\n"
        f"👤 Usuario: {user.first_name}\n"
        f"🆔 ID: `{user.id}`\n\n"
        f"📋 *Suscripciones activas:*\n{subs_text}\n\n"
        "¿Qué deseas cambiar?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return CONFIG_MENU


async def config_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle configuration menu options."""
    message = update.effective_message
    user = update.effective_user
    text = message.text if message else ""

    if message is None or user is None:
        return CONFIG_MENU

    if "Volver" in text or "volver" in text:
        await message.reply_text("Menú principal:", reply_markup=_main_menu_keyboard())
        return MENU

    if "Cambiar Horario" in text:
        # Show time selection
        context.user_data["config_mode"] = "change_time"
        await message.reply_text(
            "🕐 Selecciona tu horario preferido para recibir notificaciones:",
            reply_markup=_time_keyboard(),
        )
        return SELECT_TIME

    if "Borrar" in text or "borrar" in text:
        subscription_service, _, _ = _get_services(context)
        if subscription_service:
            try:
                await subscription_service.unsubscribe(user.id)
                await message.reply_text(
                    "🗑️ Todas las suscripciones eliminadas.",
                    reply_markup=_main_menu_keyboard(),
                )
            except Exception:
                await message.reply_text("Error al eliminar suscripciones.", reply_markup=_main_menu_keyboard())
        return MENU

    if "Idioma" in text or "idioma" in text:
        keyboard = [
            [KeyboardButton("🇪🇸 Español"), KeyboardButton("🇺🇸 English")],
            [KeyboardButton("🔙 Volver")],
        ]
        await message.reply_text(
            "🌍 Selecciona tu idioma:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        return CONFIG_MENU

    if "Español" in text:
        context.user_data["lang"] = "es"
        await message.reply_text("🇪🇸 Idioma configurado: Español", reply_markup=_main_menu_keyboard())
        return MENU

    if "English" in text:
        context.user_data["lang"] = "en"
        await message.reply_text("🇺🇸 Language set: English", reply_markup=_main_menu_keyboard())
        return MENU

    await message.reply_text("Selecciona una opción:", reply_markup=_main_menu_keyboard())
    return CONFIG_MENU


async def province_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle province selection for via query or subscription."""
    message = update.effective_message
    user = update.effective_user
    text = message.text if message else ""

    if message is None or user is None:
        return SELECT_PROVINCE

    # Handle navigation buttons
    if text == "🔙 Volver" or text == "Volver":
        context.user_data.pop("flow", None)
        await message.reply_text("Menú principal:", reply_markup=_main_menu_keyboard())
        return MENU

    if text == "✅ Continuar":
        provinces = context.user_data.get("subscribe_provinces", [])
        if not provinces:
            await message.reply_text("No seleccionaste ninguna provincia.", reply_markup=_main_menu_keyboard())
            context.user_data.pop("flow", None)
            return MENU
        # Show time selection
        await message.reply_text(
            f"🕐 *Horarios de notificación*\n\n"
            f"Provincias: {', '.join(provinces)}\n\n"
            "Selecciona la hora en que quieres recibir notificaciones:",
            parse_mode="Markdown",
            reply_markup=_time_keyboard(),
        )
        return SELECT_TIME

    # Handle unsubscription (text starts with 🗑️)
    if text.startswith("🗑️"):
        province = text.replace("🗑️ ", "").strip().lower()
        subscription_service, _, _ = _get_services(context)
        if subscription_service:
            try:
                await subscription_service.unsubscribe(user.id, province)
                await message.reply_text(
                    f"🗑️ Suscripción cancelada para *{province}*",
                    parse_mode="Markdown",
                    reply_markup=_main_menu_keyboard(),
                )
            except Exception:
                await message.reply_text("Error al cancelar.", reply_markup=_main_menu_keyboard())
        context.user_data.pop("flow", None)
        return MENU

    # Normalize province name
    province = text.strip()
    province_lower = province.lower()

    # Match against known provinces
    matched_province = None
    for p in PROVINCES:
        if p.lower() == province_lower:
            matched_province = p
            break

    # Get current flow
    flow = context.user_data.get("flow", "vias")  # Default to vias

    # === FLOW: Consultar Vías ===
    if flow == "vias":
        query_province = matched_province or province
        LOGGER.info("User %s querying vias for: %s", user.id, query_province)
        _, _, via_sync_service, via_service = _get_services(context)

        vias = []

        # Try DB first
        if via_sync_service:
            try:
                vias = await via_sync_service.get_vias_by_province(query_province)
            except Exception:
                pass

        # Fallback: query API directly if DB is empty
        if not vias and via_sync_service and via_service:
            try:
                vias = await via_sync_service.get_vias_from_api(query_province, via_service)
            except Exception:
                pass

        # Fallback: query ViaService directly
        if not vias and via_service:
            try:
                vias_by_province = await via_service.get_latest_vias()
                rows = vias_by_province.get(query_province.lower(), [])
                vias = [
                    {
                        "descripcion": row.get("descripcion", "?"),
                        "estado_actual": row.get("EstadoActual", {}).get("nombre", "?"),
                        "observaciones": row.get("observaciones", ""),
                    }
                    for row in rows
                ]
            except Exception:
                pass

        if vias:
            # Format as table-like output
            lines = [f"🛣️ *Estado de vías — {query_province.title()}*\n"]
            lines.append("```")
            lines.append(f"{'Vía':<35} {'Estado':<15}")
            lines.append("-" * 50)

            for via in vias[:20]:
                desc = via.get("descripcion", "?")
                estado = via.get("estado_actual") or via.get("estado", "?")
                icono = "🟢" if str(estado).lower() in ("abierta", "a", "activa") else "🔴"
                desc_short = desc[:32] + "..." if len(desc) > 32 else desc
                lines.append(f"{icono} {desc_short:<32} {estado}")

            lines.append("```")

            if len(vias) > 20:
                lines.append(f"_...y {len(vias) - 20} vías más_")

            # Show observations
            obs_lines = []
            for via in vias[:20]:
                obs = via.get("observaciones", "")
                if obs:
                    obs_lines.append(f"• _{via.get('descripcion', '?')}_: {obs}")

            if obs_lines:
                lines.append("\n📝 *Observaciones:*")
                lines.extend(obs_lines[:5])

            await message.reply_text(
                "\n".join(lines),
                parse_mode="Markdown",
                reply_markup=_main_menu_keyboard(),
            )
        else:
            await message.reply_text(
                f"No hay datos de vías para *{query_province}*.\n"
                "Intenta con otra provincia o más tarde.",
                parse_mode="Markdown",
                reply_markup=_main_menu_keyboard(),
            )

        context.user_data.pop("flow", None)
        return MENU

    # === FLOW: Suscribirse ===
    LOGGER.info("User %s selected province: %s (subscribe flow)", user.id, matched_province or province)
    if not matched_province:
        await message.reply_text(
            f"No reconozco \"{province}\". Selecciona una provincia de la lista:",
            reply_markup=_provinces_keyboard(),
        )
        return SELECT_PROVINCE

    # Add to subscription list
    selected = context.user_data.get("subscribe_provinces", [])
    if matched_province not in selected:
        selected.append(matched_province)
        context.user_data["subscribe_provinces"] = selected

    await message.reply_text(
        f"✅ *{matched_province}* seleccionada.\n"
        f"Seleccionadas: {', '.join(selected)}\n\n"
        "Selecciona más provincias o presiona ✅ Continuar.",
        parse_mode="Markdown",
        reply_markup=_provinces_keyboard(),
    )
    return SELECT_PROVINCE


async def time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle time selection for subscription."""
    message = update.effective_message
    user = update.effective_user
    text = message.text if message else ""

    if message is None or user is None:
        return SELECT_TIME

    if text == "🔙 Volver":
        await message.reply_text("Selecciona provincias:", reply_markup=_provinces_keyboard())
        return SELECT_PROVINCE

    if text == "✅ Confirmar":
        provinces = context.user_data.get("subscribe_provinces", [])
        times = context.user_data.get("subscribe_times", [DEFAULT_SUBSCRIPTION_TIME])

        LOGGER.info("User %s confirming subscription: provinces=%s, times=%s", user.id, provinces, times)

        if not provinces:
            await message.reply_text("No hay provincias seleccionadas.", reply_markup=_main_menu_keyboard())
            return MENU

        subscription_service, _, _ = _get_services(context)
        if subscription_service:
            results = []
            for province in provinces:
                try:
                    await subscription_service.subscribe(user.id, province.lower(), times)
                    results.append(f"✅ {province}")
                except Exception:
                    results.append(f"❌ {province}")

            context.user_data.pop("subscribe_provinces", None)
            context.user_data.pop("subscribe_times", None)

            await message.reply_text(
                "🔔 *Resultado de suscripciones:*\n\n" + "\n".join(results) +
                f"\n\nHorario: {', '.join(times)}",
                parse_mode="Markdown",
                reply_markup=_main_menu_keyboard(),
            )
        return MENU

    # Check if it's a time
    if text in TIME_OPTIONS:
        # Check if we're in config mode (changing time for existing subscriptions)
        if context.user_data.get("config_mode") == "change_time":
            subscription_service, _, _ = _get_services(context)
            if subscription_service:
                try:
                    data = await subscription_service.get_user_subscriptions(user.id)
                    subscriptions = data.get("subscriptions", {}) if isinstance(data, dict) else {}
                    for province in subscriptions:
                        await subscription_service.subscribe(user.id, province, [text])
                    context.user_data.pop("config_mode", None)
                    await message.reply_text(
                        f"🕐 Horario actualizado a *{text}* para todas las suscripciones.",
                        parse_mode="Markdown",
                        reply_markup=_main_menu_keyboard(),
                    )
                except Exception:
                    await message.reply_text("Error al actualizar horario.", reply_markup=_main_menu_keyboard())
            else:
                await message.reply_text("Servicio no disponible.", reply_markup=_main_menu_keyboard())
            return MENU

        context.user_data["subscribe_times"] = [text]
        await message.reply_text(
            f"🕐 Hora seleccionada: *{text}*\n\n"
            "Presiona ✅ Confirmar para guardar.",
            parse_mode="Markdown",
            reply_markup=_time_keyboard(),
        )
        return SELECT_TIME

    await message.reply_text("Selecciona una hora válida:", reply_markup=_time_keyboard())
    return SELECT_TIME


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel — return to main menu."""
    del context
    message = update.effective_message
    if message:
        await message.reply_text("Operación cancelada.", reply_markup=_main_menu_keyboard())
    return MENU


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unrecognized input in any state."""
    del context
    message = update.effective_message
    if message:
        await message.reply_text(
            "No entendí eso. Usa el menú o escribe /start para comenzar.",
            reply_markup=_main_menu_keyboard(),
        )
    return MENU


def register_handlers(application: Application) -> None:
    """Register conversation handlers with interactive menus."""
    # Conversation handler for interactive flows
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_handler),
            CommandHandler("help", help_handler),
            CommandHandler("vias", vias_handler),
            CommandHandler("subscribe", subscribe_start),
            CommandHandler("unsubscribe", unsubscribe_handler),
            CommandHandler("mysubscriptions", mysubscriptions_handler),
        ],
        states={
            MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
            SELECT_PROVINCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, province_selected),
            ],
            SELECT_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, time_selected),
            ],
            CONFIG_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, config_menu_handler),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_handler),
            CommandHandler("cancel", cancel_handler),
            MessageHandler(filters.ALL, fallback_handler),
        ],
        name="main_conversation",
        persistent=False,
    )

    application.add_handler(conv_handler)

    # Admin commands (registered AFTER conversation handler)
    from bot.handlers.admin import register_admin_handlers
    register_admin_handlers(application)
