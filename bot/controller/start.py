""" src/bot_controller/start.py """
import logging

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

from bot.controller.menus.initial import initial_menu
from bot.controller.utils.assemble_text import assemble_text
from bot.libs.translate import trans
from bot.settings import settings

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


async def start(update: Update, context: CallbackContext) -> int:
    """
    Starts the conversation and initializes the necessary variables.
    Parameters:
    - update (Update): The update object containing information about the incoming message.
    - context (CallbackContext): The context object containing the current conversation state and user data.
    Returns:
    - int: The next state in the chat conversation, which is 'MODERATOR'.
    """
    try:
        # Validar que update.message existe
        if not update.message:
            logger.warning("update.message is None in start function")
            return settings.MODERATOR

        # Validar que update.effective_user existe
        if not update.effective_user:
            logger.warning("update.effective_user is None in start function")
            await update.message.reply_text("Error: Usuario no identificado")
            return settings.MODERATOR

        # Obtener el idioma con validación mejorada
        default_lang = 'es'  # Idioma por defecto
        user_lang = update.effective_user.language_code
        stored_lang = context.user_data.get('language')
        
        # Usar idioma almacenado, luego idioma del usuario, finalmente por defecto
        _lang = stored_lang or user_lang or default_lang
        
        # Validar que el idioma sea válido (opcional: agregar lista de idiomas soportados)
        if not _lang or len(_lang) < 2:
            _lang = default_lang
            
        context.user_data['language'] = _lang

        # Validar que trans está disponible antes de usarlo
        try:
            trans.lang = _lang
        except (AttributeError, ValueError) as trans_error:
            logger.error(f"Error setting language {_lang}: {trans_error}")
            # Intentar con idioma por defecto
            trans.lang(default_lang)
            context.user_data['language'] = default_lang

        # Obtener nombre del usuario con validación
        user_name = update.effective_user.first_name or "Usuario"

        # Ensamblar mensaje de bienvenida con validación
        try:
            welcome_message = f"{assemble_text(str(trans.start.welcome), user=user_name)} \n\n {trans.start.description_welcome}"
        except (AttributeError, KeyError) as text_error:
            logger.error(f"Error assembling welcome message: {text_error}")
            welcome_message = f"¡Hola {user_name}! Bienvenido al bot."

        # Enviar mensaje con validación del teclado
        try:
            keyboard = initial_menu()
            await update.message.reply_text(welcome_message, reply_markup=keyboard)
        except Exception as keyboard_error:
            logger.error(f"Error creating keyboard: {keyboard_error}")
            # Enviar mensaje sin teclado como respaldo
            await update.message.reply_text(welcome_message)

    except Exception as e:
        # Manejo de errores más específico con logging mejorado
        logger.error(f"Unexpected error in start function: {type(e).__name__}: {e}", exc_info=True)
        
        try:
            await update.message.reply_text(
                "Ha ocurrido un error al iniciar la conversación. Por favor, inténtalo de nuevo más tarde.")
        except Exception as reply_error:
            logger.error(f"Could not send error message: {reply_error}")
    
    # Retornar el siguiente estado en la conversación
    return settings.MODERATOR