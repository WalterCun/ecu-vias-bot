"""Notification flow handlers."""
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
from bot.controller.utils.conversation_context import (
    get_selected_provinces,
    get_selected_times,
    set_alarm_times,
    toggle_time,
)
from bot.settings import settings

logger = logging.getLogger(__name__)

__all__ = ['notifications', 'alarm_notifications']
ONE_NOTIFICATION = 'UNA NOTIFICACION EN EL DIA'


async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles notification mode selection and preserves previous selection context."""
    time_option = clean_text(update.message.text)
    logger.info("Metodo notifications -> instruccion: %s", time_option)

    if time_option != clean_text(ONE_NOTIFICATION):
        await update.message.reply_text('Opción no válida. Por favor elige una opción del menú.')
        return settings.NOTIFICATIONS

    selected_times = get_selected_times(context.user_data)
    context.user_data['times'] = selected_times

    prefix = '¿Cuándo desea recibir las notificaciones?'
    if context.user_data.get('alarms'):
        prefix = 'Tienes horarios guardados. Puedes ajustarlos y volver a programar.'

    await update.message.reply_text(
        prefix,
        reply_markup=notification_menu_times(selected_times, 'one')
    )
    return settings.ALARM_NOTIFICATIONS


async def alarm_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configures and persists alarm schedule selection flow."""
    chat_id = update.effective_message.chat_id
    selected_time = clean_text(update.message.text)

    logger.info("Metodo alarm_notifications -> instruccion: %s -> %s", chat_id, selected_time)

    if selected_time == clean_text(settings.PROGRAMMING_DONE_BUTTON):
        selected_times = get_selected_times(context.user_data)

        if not selected_times:
            await update.effective_message.reply_text(
                'Debes seleccionar al menos un horario antes de programar.',
                reply_markup=notification_menu_times(selected_times, 'one')
            )
            return settings.ALARM_NOTIFICATIONS

        remove_job_if_exists(str(chat_id), context)

        scheduled_times: list[dt_time] = []
        for selected in selected_times:
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

        set_alarm_times(context.user_data, selected_times)

        await update.effective_message.reply_text('NOTIFICACION CONFIGURADA', reply_markup=initial_menu())
        logger.info("Notificaciones configuradas para chat_id=%s horarios=%s", chat_id, scheduled_times)
        return settings.MODERATOR

    if selected_time not in settings.ONCE_A_DAY:
        await update.effective_message.reply_text(
            'No reconozco ese horario. Selecciona una opción del teclado.',
            reply_markup=notification_menu_times(get_selected_times(context.user_data), 'one')
        )
        return settings.ALARM_NOTIFICATIONS

    selected_times = toggle_time(context.user_data, selected_time)
    await update.effective_message.reply_text(
        'Selecciona más horarios o pulsa PROGRAMAR ✅ para guardar.',
        reply_markup=notification_menu_times(selected_times, 'one')
    )
    return settings.ALARM_NOTIFICATIONS


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends periodic reminder message from official source."""
    provinces = get_selected_provinces(context.user_data)
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
