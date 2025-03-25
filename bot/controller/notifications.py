""" src/bot_controller/notifications.py """
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.controller.jobs import remove_job_if_exists
from bot.controller.menus.initial import initial_menu
from bot.controller.menus.notifications import notification_menu_times
from bot.controller.utils.assemble_text import assemble_text
from bot.controller.utils.clean_text import clean_text

from bot.translations.core import translate
from settings import settings

logger = logging.getLogger(__name__)

__all__ = ['notifications', 'alarm_notifications']
ONE_NOTIFICATION = 'UNA NOTIFICACION EN EL DIA'


# async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """
#     Handles the notification setup as per the user's choice.
#     This method listens for the user's input on their preferred notification frequency,
#     and responds with the appropriate menu for further configuration.
#
#     Args:
#         update (Update): The update object that contains information about the incoming update.
#         context (ContextTypes.DEFAULT_TYPE): The context object that contains data pertaining to the user's session.
#
#     Returns:
#         int: The next state in the conversation flow, indicating the notification setup process status.
#     """
#     time_option = update.message.text
#
#     logger.info(f"Metodo notifications -> instruccion: {time_option}")
#
#     if time_option == 'UNA NOTIFICACION EN EL DIA':
#         try:
#             times = context.user_data['times']
#         except Exception as e:
#             times = context.user_data['times'] = []
#         else:
#             # Eliminar los tiempos que no corresonden al origen
#             for time in times:
#                 if time not in ONCE_A_DAY.keys():
#                     del times[times.index(time)]
#             context.user_data['times'] = times
#
#         await update.message.reply_text('Cuando desea recibir las notificaciones',
#                                         reply_markup=notification_menu_times(times, 'one'))
#
#     # elif time_option == 'VARIAS NOTIFICACIONES EN EL DIA':
#     #     try:
#     #         times = context.user_data['times']
#     #     except Exception as e:
#     #         times = context.user_data['times'] = []
#     #     else:
#     #         # Eliminar los tiempos que no corresonden al origen
#     #         for time in times:
#     #             if time not in SEVERAL_TIMES_A_DAY:
#     #                 del times[times.index(time)]
#     #         context.user_data['times'] = times
#     #
#     #     await update.message.reply_text('Cuando desea recibir las notificaciones',
#     #                                     reply_markup=notification_menu_times(times, 'all'))
#
#     return settings.ALARM_NOTIFICATIONS

async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the notification setup as per the user's choice.
    Args:
        update (Update): Contains information about the incoming update.
        context (ContextTypes.DEFAULT_TYPE): Contains data pertaining to the user's session.
    Returns:
        int: The next state in the conversation flow.
    """
    time_option = update.message.text
    logger.info(f"Metodo notifications -> instruccion: {time_option}")

    if time_option == ONE_NOTIFICATION:
        try:
            times = context.user_data.setdefault('times', [])
            # Eliminar los tiempos que no corresponden al origen
            # times = [time for time in times if time in ONCE_A_DAY.keys()]
            # context.user_data['times'] = times
            context.user_data['times'] = 'times'
        except Exception as e:
            logger.error(f"Error al configurar notificaciones: {e}")
            await update.message.reply_text(
                "Ocurrió un error al configurar las notificaciones. Por favor, intenta nuevamente.")
            return settings.NOTIFICATIONS

        await update.message.reply_text('¿Cuándo desea recibir las notificaciones?',
                                        reply_markup=notification_menu_times(times, 'one'))

    return settings.ALARM_NOTIFICATIONS


# async def alarm_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """
#     :param update: An object that represents an incoming update from Telegram. It contains information about the message, chat, and user.
#     :param context: An object that provides access to various data related to the current update. It includes user-specific data, job queues, and other utility functions.
#
#     :return: No return value
#     """
#     chat_id = update.effective_message.chat_id
#     time = clean_text(update.message.text)
#
#     logger.info(f"Metodo alarm_notifications -> instruccion: {chat_id} -> {time}")
#
#     times = context.user_data['times']
#
#     if time in times:
#         del times[times.index(time)]
#     elif time != clean_text(language.general_msm_programming):
#         times.append(time)  # Agregar el nuevo tiempo a la lista
#
#     context.user_data['times'] = times
#
#     if times:
#         remove_job_if_exists(str(chat_id), context)
#
#         format_24 = [elemento for elemento in times if any(palabra in elemento for palabra in ["AM", "PM"])]
#
#         if format_24:
#             clock = ONCE_A_DAY[time]
#             context.job_queue.run_daily(alarm, clock, chat_id=chat_id, name=str(chat_id), data=clock)
#             del context.user_data['times']
#             context.user_data['alarms'] = [times]
#
#             await update.effective_message.reply_text('NOTIFICACION CONFIGURADA', reply_markup=initial_menu())
#             return settings.MODERATOR
#         else:
#             # TODO: Completar cuando se requiere varias veces al dia
#             await update.effective_message.reply_text('OPCION NO CONFIGURADA', reply_markup=initial_menu())
#             return settings.MODERATOR
#
#         # TODO: Completar cuando la informacion cambie
#
#     return settings.ALARM_NOTIFICATIONS

async def alarm_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Configures alarm notifications.
    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Provides access to user-specific data, job queues, etc.
    Returns:
        int: The next state in the conversation flow.
    """
    chat_id = update.effective_message.chat_id
    time = clean_text(update.message.text)

    logger.info(f"Metodo alarm_notifications -> instruccion: {chat_id} -> {time}")

    times = context.user_data.setdefault('times', [])

    if time in times:
        times.remove(time)
    elif time != clean_text(translate.general_msm_programming):
        times.append(time)

    context.user_data['times'] = times

    if times:
        remove_job_if_exists(str(chat_id), context)

        format_24 = [t for t in times if any(p in t for p in ["AM", "PM"])]

        if format_24:
            # clock = ONCE_A_DAY[time]
            clock = "ONCE_A_DAY[time]"
            context.job_queue.run_daily(alarm, clock, chat_id=chat_id, name=str(chat_id), data=clock)
            del context.user_data['times']
            context.user_data['alarms'] = [times]

            await update.effective_message.reply_text('NOTIFICACION CONFIGURADA', reply_markup=initial_menu())
        else:
            await update.effective_message.reply_text('OPCION NO CONFIGURADA', reply_markup=initial_menu())

        return settings.MODERATOR

    return settings.ALARM_NOTIFICATIONS


# async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
#     """
#     Send alarm messages to the specified chat_id based on the provinces provided in the context.
#
#     Args:
#         context: The context object that contains the user data.
#
#     Returns:
#         None
#     """
#     db = Database()
#     provinces = context.user_data['provinces']
#     job = context.job
#
#     if provinces:
#         """
#         # Build SQL condition to query all provinces at once
#         prov_condition = " OR ".join([f'provincia = "{prov}"' for prov in provinces])
#         all_vias = db.fetch_all('vias_ec', prov_condition).iterrows()
#         for via in all_vias:
#             information = assemble_text(language.general_msg_vias,
#                                         province=via['Provincia'],
#                                         via=via['Vía'],
#                                         state=via['Estado'],
#                                         observation=via['Observaciones'])
#             await context.bot.send_message(job.chat_id, text=information, parse_mode=ParseMode.MARKDOWN)
#         """
#         for prov in provinces:
#             for via in db.fetch_all('vias_ec', f'provincia = "{prov}"]').iterrows():
#                 information = assemble_text(language.general_msg_vias,
#                                             province=via['Provincia'],
#                                             via=via['Vía'],
#                                             state=via['Estado'],
#                                             observation=via['Observaciones'])
#
#                 await context.bot.send_message(job.chat_id, text=information, parse_mode=ParseMode.MARKDOWN)
#
#         info_oficial = assemble_text(
#             language.general_msg_info_oficial,
#             description_url='ECU911 Consulta de vias',
#             url=settings.URL
#         )
#         await context.bot.send_message(job.chat_id, text=info_oficial, parse_mode=ParseMode.MARKDOWN)

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send alarm messages to the specified chat_id based on the provinces provided in the context.
    Args:
        context: The context object containing the user data.
    """
    provinces = context.user_data['provinces']
    job = context.job

    if provinces:
        for prov in provinces:
            # for _, via in db.fetch_all('vias_ec', f'provincia = "{prov}"').iterrows():
            #     information = assemble_text(translate.general_msg_vias,
            #                                 province=via['Provincia'],
            #                                 via=via['Vía'],
            #                                 state=via['Estado'],
            #                                 observation=via['Observaciones'])
            #
            #     await context.bot.send_message(job.chat_id, text=information, parse_mode=ParseMode.MARKDOWN)
            print(prov)
            pass
        info_oficial = assemble_text(
            translate.general_msg_info_oficial,
            description_url='ECU911 Consulta de vias',
            url=settings.URL
        )
        await context.bot.send_message(job.chat_id, text=info_oficial, parse_mode=ParseMode.MARKDOWN)
