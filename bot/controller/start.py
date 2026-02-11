""" src/bot_controller/start.py """
import asyncio
import logging

from telegram import Update
from telegram.error import TimedOut, RetryAfter, NetworkError
from telegram.ext import CallbackContext

from bot.controller.menus.initial import initial_menu
from bot.controller.utils.assemble_text import assemble_text
from bot.libs.translate import trans
from bot.settings import settings

logger = logging.getLogger(__name__)

async def send_message_with_retry(update, message, reply_markup=None, max_retries=3):
    """
    Envía un mensaje con reintentos automáticos en caso de timeout.
    """
    for attempt in range(max_retries):
        try:
            if reply_markup:
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message)
            return True
        except TimedOut:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Backoff exponencial: 1s, 2s, 4s
                logger.warning(f"Timeout en intento {attempt + 1}. Reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Falló después de {max_retries} intentos por timeout")
                raise
        except RetryAfter as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after + 1
                logger.warning(f"Rate limit alcanzado. Esperando {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Rate limit persistente después de {max_retries} intentos")
                raise
        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Error de red en intento {attempt + 1}: {e}. Reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Error de red persistente después de {max_retries} intentos: {e}")
                raise
    return False

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
            try:
                await send_message_with_retry(update, "Error: Usuario no identificado")
            except Exception as e:
                logger.error(f"No se pudo enviar mensaje de error: {e}")
            return settings.MODERATOR

        # Obtener el idioma con validación mejorada
        default_lang = 'es'  # Idioma por defecto
        user_lang = update.effective_user.language_code
        stored_lang = context.user_data.get('language')

        # Usar idioma almacenado, luego idioma del usuario, finalmente por defecto
        _lang = stored_lang or user_lang or default_lang

        # Validar que el idioma sea válido
        if not _lang or len(_lang) < 2:
            _lang = default_lang

        context.user_data['language'] = _lang

        # Validar que trans está disponible antes de usarlo
        try:
            trans.lang = _lang
        except (AttributeError, ValueError) as trans_error:
            logger.error(f"Error setting language {_lang}: {trans_error}")
            # Intentar con idioma por defecto
            trans.lang = default_lang
            context.user_data['language'] = default_lang

        # Obtener nombre del usuario con validación
        user_name = update.effective_user.first_name or "Usuario"

        # Ensamblar mensaje de bienvenida con validación
        try:
            welcome_message = (f"{assemble_text(str(trans.start.welcome), user=user_name)} \n\n"
                               f"{trans.start.description}")
        except (AttributeError, KeyError) as text_error:
            logger.error(f"Error assembling welcome message: {text_error}")
            welcome_message = f"¡Hola {user_name}! Bienvenido al bot."

        # Limitar longitud del mensaje para evitar timeouts
        if len(welcome_message) > 4000:
            welcome_message = welcome_message[:4000] + "..."
            logger.warning("Mensaje de bienvenida truncado por longitud")

        # Enviar mensaje con sistema de reintentos
        try:
            keyboard = initial_menu()
            print('WELCOME: ', welcome_message)
            await send_message_with_retry(update, welcome_message, keyboard)
        except Exception as keyboard_error:
            logger.error(f"Error creating keyboard: {keyboard_error}")
            # Enviar mensaje sin teclado como respaldo
            try:
                await send_message_with_retry(update, welcome_message)
            except Exception as fallback_error:
                logger.error(f"Error en mensaje de respaldo: {fallback_error}")
                # Último recurso: mensaje simple
                try:
                    await send_message_with_retry(update, f"¡Hola {user_name}! Bot iniciado correctamente.")
                except Exception as final_error:
                    logger.critical(f"No se pudo enviar ningún mensaje: {final_error}")

    except Exception as e:
        # Manejo de errores más específico con logging mejorado
        logger.error(f"Unexpected error in start function: {type(e).__name__}: {e}", exc_info=True)
        try:
            await send_message_with_retry(
                update,
                "Ha ocurrido un error al iniciar la conversación. Por favor, inténtalo de nuevo más tarde."
            )
        except Exception as final_error:
            logger.critical(f"No se pudo enviar mensaje de error final: {final_error}")

    # Retornar el siguiente estado en la conversación
    return settings.MODERATOR

