import logging

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.controller.menus.suscriptor import suscriptor_menu
from bot.libs.translate import trans
from bot.settings import settings

logger = logging.getLogger(__name__)


# async def moderator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """
#     Process the user's message and reply accordingly.
#
#     :param update: The update received from the user.
#     :param context: The context of the conversation.
#     :return: An integer representing the response.
#     """
#     text = update.message.text
#     logger.info(f"Leer instruccion: {text}")
#
#     if text == language.menu_buttons_subscribe:
#         provinces = context.user_data.get('provinces', None)
#         # try:
#         #     provinces = context.user_data.get('provinces', None)
#         # except Exception as e:
#         #     print(e)
#         #     provinces = None
#         # finally:
#         await update.message.reply_text(language.general_subscribe, reply_markup=suscriptor_menu(provinces))
#         return settings.SUBSCRIPTION
#
#     if text == language.menu_buttons_unsubscribe:
#         await update.message.reply_text(f"{text.lower()}")
#         return settings.UNSUBSCRIPTION
#
#     if text == language.menu_buttons_settings:
#         await update.message.reply_text(f"{text.lower()}")
#         return settings.CONFIG
#
#     return settings.MODERATOR

async def moderator(update: Update, context: CallbackContext) -> int:
    """
    Process the user's message and reply accordingly.

    :param update: The update received from the user.
    :param context: The context of the conversation.
    :return: An integer representing the response.
    """
    text = update.message.text
    logger.info(f"Leer instruccion: {text}")

    print(text == trans.moderator.menu.btns.subscribe)

    try:
        if text == trans.moderator.menu.btns.subscribe:
            provinces = context.user_data.get('provinces', None)
            await update.message.reply_text(trans.moderator.menu.btns.subscribe, reply_markup=suscriptor_menu(provinces))
            return settings.SUBSCRIPTION

        if text == trans.moderator.menu.btns.unsubscribe:
            await update.message.reply_text(f"{text.lower()}")
            return settings.UNSUBSCRIPTION

        if text == trans.moderator.menu.btns.settings:
            await update.message.reply_text(f"{text.lower()}")
            return settings.CONFIG

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Ha ocurrido un error procesando tu solicitud. Por favor, intenta nuevamente.")
        # Limpiar datos del usuario y finalizar conversación
        context.user_data.clear()
        return ConversationHandler.END

    # Enviar un mensaje de error o instrucciones adicionales en caso de entrada no reconocida
    await update.message.reply_text("Lo siento, no entiendo tu instrucción. Por favor, elige una opción del menú.")
    return settings.MODERATOR