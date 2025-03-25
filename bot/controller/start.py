""" src/bot_controller/start.py """
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.controller.menus.initial import initial_menu
from bot.controller.utils.assemble_text import assemble_text
from settings import settings

logger = logging.getLogger(__name__)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """
#     Starts the conversation and initializes the necessary variables.
#
#     This method is called when the conversation starts. It checks if the user has already started the conversation.
#     If not, it sets the 'started' flag in the user_data dictionary to True *. If the user has already started the
#     conversation, it checks if the user's language is set in the user_data dictionary. If the language is not set,
#     it sets the language based on the * user's language_code in the update object, loads the language translations,
#     and sends a welcome message to the user. If the language is already set, it loads the language translations *.
#
#     After initializing the necessary variables, it sends a message to the user with instructions for the next steps
#     and displays an initial menu with options.
#
#     Parameters:
#     - update (Update): The update object containing information about the incoming message.
#     - context (ContextTypes.DEFAULT_TYPE): The context object containing the current conversation state and user data.
#
#     Returns:
#     - int: The next state in the chat conversation, which is 'MODERATOR'.
#
#     Example Usage:
#     state = await start(update, context)
#     """
#     print(context.user_data)
#     # if not context.user_data.get('started', False):
#     #     print('Reiniciando la conversacion')
#     #     context.user_data['started'] = True
#     # else:
#     try:
#         lang = context.user_data['language']
#     except Exception as e:
#         logger.error(e)
#         context.user_data['language'] = update.effective_user.language_code
#         lang = update.effective_user.language_code
#         language.load_translations(lang)
#     else:
#         # Load language translations based on the user's language setting
#         language.load_translations(lang)
#     finally:
#         # Reply to the user's message with a welcome message and replace the placeholder with the user's first name
#         await update.message.reply_text(
#             assemble_text(language.general_start, user=update.effective_user.first_name))
#
#         # Send another message to the user with instructions for next steps and display an initial menu with options
#         await update.message.reply_text(language.general_select_option, reply_markup=initial_menu())
#
#     # The function returns the next state in the chat conversation which is 'MODERATOR'.
#     return settings.MODERATOR


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation and initializes the necessary variables.

    Parameters:
    - update (Update): The update object containing information about the incoming message.
    - context (ContextTypes.DEFAULT_TYPE): The context object containing the current conversation state and user data.

    Returns:
    - int: The next state in the chat conversation, which is 'MODERATOR'.
    """
    try:
        # Obtener el idioma almacenado o configurar por defecto
        lang = context.user_data.get('language', update.effective_user.language_code)
        context.user_data.setdefault('language', lang)

        # Cargar traducciones según el idioma del usuario
        translate.load_translations(lang)

        # Enviar mensaje de bienvenida y menú inicial
        welcome_message = assemble_text(translate.general_start,
                                        user=update.effective_user.first_name) + "\n\n" + translate.general_select_option
        await update.message.reply_text(welcome_message, reply_markup=initial_menu())

    except Exception as e:
        # Manejo de errores y logueo
        logger.error(f"Error in start function: {e}")
        await update.message.reply_text(
            "Ha ocurrido un error al iniciar la conversación. Por favor, inténtalo de nuevo más tarde.")

    # Retornar el siguiente estado en la conversación
    return settings.MODERATOR