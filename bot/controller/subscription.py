import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.controller.menus.notifications import notification_menu
from bot.controller.menus.suscriptor import suscriptor_menu
from bot.controller.utils.clean_text import clean_text
from bot.controller.utils.conversation_context import toggle_province
from bot.settings import settings

logger = logging.getLogger(__name__)


async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles province selection for subscription flow.
    """
    province = clean_text(update.message.text)
    logger.info("Metodo suscription -> instruccion: %s", province)

    try:
        provinces = toggle_province(context.user_data, province)
    except Exception as e:
        logger.error("Error al manejar la suscripción: %s", e)
        await update.message.reply_text("Ocurrió un error procesando tu suscripción. Por favor, intenta nuevamente.")
        return settings.SUBSCRIPTION

    if province == clean_text(settings.CONTINUE_BUTTON) and len(provinces) >= 1:
        await update.message.reply_text(
            f"{str(trans.notifications.ask_when)}\n{str(trans.notifications.choose_options)}",
            reply_markup=notification_menu()
        )
        return settings.NOTIFICATIONS

    await update.message.reply_text(
        str(trans.subscription.choose_or_continue),
        reply_markup=suscriptor_menu(provinces)
    )
    return settings.SUBSCRIPTION
