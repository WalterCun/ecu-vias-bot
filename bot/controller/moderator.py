import logging

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.controller.menus.suscriptor import suscriptor_menu
from bot.libs.translate import trans
from bot.settings import settings

logger = logging.getLogger(__name__)


async def moderator(update: Update, context: CallbackContext) -> int:
    """
    Process the user's message and reply accordingly.

    :param update: The update received from the user.
    :param context: The context of the conversation.
    :return: An integer representing the response.
    """
    text = update.message.text
    logger.info(f"Leer instruccion: {text}")


    try:
        if text == str(trans.moderator.menu.btns.subscribe):
            provinces = context.user_data.get('provinces', None)
            print('context', context)
            print('context.user_data', context.user_data)
            print('Provinces', provinces)
            await update.message.reply_text(f'{trans.moderator.menu.btns.subscribe}',
                                            reply_markup=suscriptor_menu(provinces))
            return settings.SUBSCRIPTION

        if text == str(trans.moderator.menu.btns.unsubscribe):
            await update.message.reply_text(f"{text.lower()}")
            return settings.UNSUBSCRIPTION

        if text == str(trans.moderator.menu.btns.settings):
            await update.message.reply_text(f"{text.lower()}")
            return settings.CONFIG

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(f'{trans.errors.generic_error}')

    # Enviar un mensaje de error o instrucciones adicionales en caso de entrada no reconocida
    await update.message.reply_text(f'{trans.errors.unknown_instruction}')
    return settings.MODERATOR
