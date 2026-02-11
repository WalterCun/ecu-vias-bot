""" src/bot_controller/notifications.py """
import logging
from datetime import time as dt_time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.controller.jobs import remove_job_if_exists
from bot.controller.menus.initial import initial_menu
from bot.controller.menus.notifications import notification_menu_times
from bot.controller.utils.assemble_text import assemble_text
from bot.controller.utils.clean_text import clean_text
from bot.libs.translate import trans

from bot.settings import settings

logger = logging.getLogger(__name__)

__all__ = ['notifications', 'alarm_notifications']
ONE_NOTIFICATION = 'UNA NOTIFICACION EN EL DIA'


async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the notification setup as per the user's choice.
    """
    time_option = clean_text(update.message.text)
    logger.info("Metodo notifications -> instruccion: %s", time_option)

    if time_option == clean_text(ONE_NOTIFICATION):
        times = context.user_data.get('times', [])
        if not isinstance(times, list):
            times = []
        context.user_data['times'] = [t for t in times if t in settings.ONCE_A_DAY]

        await update.message.reply_text(
            '¿Cuándo desea recibir las notificaciones?',
            reply_markup=notification_menu_times(context.user_data['times'], 'one')
        )
        return settings.ALARM_NOTIFICATIONS

    await update.message.reply_text(
        'Opción no válida. Por favor elige una opción del menú.',
        reply_markup=notification_menu_times(context.user_data.get('times', []), 'one')
    )
    return settings.NOTIFICATIONS


async def alarm_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Configures alarm notifications.
    """
    chat_id = update.effective_message.chat_id
    selected_time = clean_text(update.message.text)

    logger.info("Metodo alarm_notifications -> instruccion: %s -> %s", chat_id, selected_time)

    times = context.user_data.get('times', [])
    if not isinstance(times, list):
        times = []

    if selected_time == clean_text(settings.PROGRAMMING_DONE_BUTTON):
        if not times:
            await update.effective_message.reply_text(
                'Debes seleccionar al menos un horario antes de programar.',
                reply_markup=notification_menu_times(times, 'one')
            )
            return settings.ALARM_NOTIFICATIONS

        remove_job_if_exists(str(chat_id), context)

        scheduled_times: list[dt_time] = []
        for selected in times:
            clock = settings.ONCE_A_DAY.get(selected)
            if clock:
                context.job_queue.run_daily(
                    alarm,
                    clock,
                    chat_id=chat_id,
                    name=str(chat_id),
                    data={'clock': selected}
                )
                scheduled_times.append(clock)

        context.user_data['alarms'] = times
        context.user_data.pop('times', None)

        await update.effective_message.reply_text('NOTIFICACION CONFIGURADA', reply_markup=initial_menu())
        logger.info("Notificaciones configuradas para chat_id=%s horarios=%s", chat_id, scheduled_times)
        return settings.MODERATOR

    if selected_time in settings.ONCE_A_DAY:
        if selected_time in times:
            times.remove(selected_time)
        else:
            times.append(selected_time)

        context.user_data['times'] = times
        await update.effective_message.reply_text(
            'Selecciona más horarios o pulsa PROGRAMAR ✅ para guardar.',
            reply_markup=notification_menu_times(times, 'one')
        )
        return settings.ALARM_NOTIFICATIONS

    await update.effective_message.reply_text(
        'No reconozco ese horario. Selecciona una opción del teclado.',
        reply_markup=notification_menu_times(times, 'one')
    )
    return settings.ALARM_NOTIFICATIONS


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send alarm messages to the specified chat_id based on the provinces provided in the context.
    """
    provinces = context.user_data.get('provinces', [])
    job = context.job

    if provinces:
        for prov in provinces:
            logger.info("Provincia suscrita para enviar alerta: %s", prov)

        info_oficial = assemble_text(
            'Fuente oficial: {description_url}\n{url}',
            description_url='ECU911 Consulta de vias',
            url=settings.URL_SCRAPPING_WEB
        )
        await context.bot.send_message(job.chat_id, text=info_oficial, parse_mode=ParseMode.MARKDOWN)
