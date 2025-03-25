import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.settings.config import settings

logger = logging.getLogger(__name__)


# async def unsubscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     await update.message.reply_text("Hello, moderator!")
#
#     return 0

async def unsubscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the unsubscription process for the user.

    Args:
        update (Update): Contains information about the incoming update.
        context (ContextTypes.DEFAULT_TYPE): Contains data pertaining to the user's session.

    Returns:
        int: The next state in the conversation flow.
    """
    user_id = update.effective_user.id
    logger.info(f"Usuario {user_id} esta desuscribiendose.")

    try:
        # Asume que tienes algún dato de suscripción en user_data, ejemplo 'subscriptions'
        subscriptions = context.user_data.get('subscriptions', [])
        if subscriptions:
            context.user_data['subscriptions'] = []
            await update.message.reply_text("Has sido desuscrito de todas las notificaciones.")
        else:
            await update.message.reply_text("No tienes suscripciones activas.")

    except Exception as e:
        logger.error(f"Error desconocido al desuscribir al usuario {user_id}: {e}")
        await update.message.reply_text(
            "Hubo un problema al procesar tu desuscripción. Por favor, inténtalo más tarde.")
        return settings.UNSUBSCRIBE_FAIL  # Asume un estado de fallo en desuscripción.

    return settings.UNSUBSCRIBE  # Asume un estado de éxito en desuscripción.
