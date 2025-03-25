import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.controller.languages.translations import language
from src.controller.menus.suscriptor import suscriptor_menu
from src.settings.config import settings

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

async def moderator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the user's message and reply accordingly.

    :param update: The update received from the user.
    :param context: The context of the conversation.
    :return: An integer representing the response.
    """
    text = update.message.text
    logger.info(f"Leer instruccion: {text}")

    try:
        if text == language.menu_buttons_subscribe:
            provinces = context.user_data.get('provinces', None)
            await update.message.reply_text(language.general_subscribe, reply_markup=suscriptor_menu(provinces))
            return settings.SUBSCRIPTION

        if text == language.menu_buttons_unsubscribe:
            await update.message.reply_text(f"{text.lower()}")
            return settings.UNSUBSCRIPTION

        if text == language.menu_buttons_settings:
            await update.message.reply_text(f"{text.lower()}")
            return settings.CONFIG

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Ha ocurrido un error procesando tu solicitud. Por favor, intenta nuevamente.")

    # Enviar un mensaje de error o instrucciones adicionales en caso de entrada no reconocida
    await update.message.reply_text("Lo siento, no entiendo tu instrucción. Por favor, elige una opción del menú.")
    return settings.MODERATOR