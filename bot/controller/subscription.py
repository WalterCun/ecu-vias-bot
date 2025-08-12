import logging

from telegram import Update
from telegram.ext import ContextTypes


from bot.controller.menus.notifications import notification_menu
from bot.controller.menus.suscriptor import suscriptor_menu
from bot.controller.utils.clean_text import clean_text
from bot.libs.translate import trans

from bot.settings import settings

logger = logging.getLogger(__name__)


# async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """
#     This method is used for handling subscriptions.
#
#     :param update: Object containing the updated information
#     :type update: Update
#
#     :param context: Object containing the context information
#     :type context: ContextTypes.DEFAULT_TYPE
#
#     :return: The status code indicating the result of the subscription
#     :rtype: int
#     """
#     province = clean_text(update.message.text)
#     logger.info(f"Metodo suscription -> instruccion: {province}")
#
#     try:
#         provinces = context.user_data['provinces']
#     except Exception as e:
#         context.user_data['provinces'] = []
#         context.user_data['provinces'].append(province)
#         provinces = context.user_data['provinces']
#     else:
#         if province in provinces:
#             del provinces[provinces.index(province)]
#         elif province != clean_text(language.general_msm_continue):
#             provinces.append(province)
#
#         context.user_data['provinces'] = provinces
#
#     if province == clean_text(language.general_msm_continue) and len(provinces) >= 1:
#         await update.message.reply_text('Cuando desea recibir las notificaciones')
#         await update.message.reply_text('Eliga una de las 2 opciones:', reply_markup=notification_menu())
#         return settings.NOTIFICATIONS
#
#     await update.message.reply_text('Puede elegir otra provincias o darle en el boton de continuar...',
#                                     reply_markup=suscriptor_menu(provinces))
#
#     return settings.SUBSCRIPTION

async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    This method is used for handling subscriptions.

    :param update: Object containing the updated information
    :type update: Update

    :param context: Object containing the context information
    :type context: ContextTypes.DEFAULT_TYPE

    :return: The status code indicating the result of the subscription
    :rtype: int
    """
    province = clean_text(update.message.text)
    logger.info(f"Metodo suscription -> instruccion: {province}")

    try:
        # Obtener o inicializar la lista de provincias
        provinces = context.user_data.setdefault('provinces', [])

        if province in provinces:
            provinces.remove(province)
            logger.info(f"Provincia removida: {province}")
        elif province != clean_text(trans.general_msm_continue):
            provinces.append(province)
            logger.info(f"Provincia añadida: {province}")

        context.user_data['provinces'] = provinces

    except Exception as e:
        logger.error(f"Error al manejar la suscripción: {e}")
        await update.message.reply_text("Ocurrió un error procesando tu suscripción. Por favor, intenta nuevamente.")
        return settings.SUBSCRIPTION

    if province == clean_text(trans.general_msm_continue) and len(provinces) >= 1:
        await update.message.reply_text(
            '¿Cuándo deseas recibir las notificaciones?\nElige una de las siguientes opciones:',
            reply_markup=notification_menu()
        )
        return settings.NOTIFICATIONS

    # Combina las instrucciones en un solo mensaje
    await update.message.reply_text(
        'Puedes elegir otra provincia o presionar el botón de continuar...',
        reply_markup=suscriptor_menu(provinces)
    )

    return settings.SUBSCRIPTION