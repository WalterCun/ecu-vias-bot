import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.controller.menus.initial import initial_menu
from bot.controller.utils.conversation_context import clear_subscription_state
from bot.settings import settings

logger = logging.getLogger(__name__)


async def unsubscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the unsubscription process for the user."""
    user_id = update.effective_user.id
    logger.info("Usuario %s esta desuscribiendose.", user_id)

    try:
        had_state = any(
            key in context.user_data for key in ('subscriptions', 'times', 'alarms', 'provinces')
        )
        clear_subscription_state(context.user_data)
        context.user_data.pop('provinces', None)

        if had_state:
            await update.message.reply_text(
                "Has sido desuscrito de todas las notificaciones.",
                reply_markup=initial_menu()
            )
        else:
            await update.message.reply_text(
                "No tienes suscripciones activas.",
                reply_markup=initial_menu()
            )

    except Exception as e:
        logger.error("Error desconocido al desuscribir al usuario %s: %s", user_id, e)
        await update.message.reply_text(
            "Hubo un problema al procesar tu desuscripción. Por favor, inténtalo más tarde."
        )
        return settings.UNSUBSCRIBE_FAIL

    return settings.MODERATOR
