from telegram import ReplyKeyboardMarkup

from bot.controller.utils.assamble_keyboard_menu import assemble_keyboard, KeyboardType, MenuOption

__all__ = ['notification_menu', 'notification_menu_times']

from bot.controller.utils.cheack_options_buttons import cheack_options
from bot.settings import settings


ONE_NOTIFICATION = 'UNA NOTIFICACION EN EL DIA'


def notification_menu(times: list = None, hide_keyboard=False) -> ReplyKeyboardMarkup:
    """
    Creates a notification menu as a ReplyKeyboardMarkup object.
    """
    options = [ONE_NOTIFICATION]
    actions = {}
    row_count = 0
    for index, option in enumerate(options):
        if index % 1 == 0 and index >= 1:
            row_count += 1
        actions.update(cheack_options(option, row_count, times))

    return assemble_keyboard(actions, KeyboardType.KEYBOARD, hide_keyboard=hide_keyboard)


def notification_menu_times(times: list = None, option: str = 'one', hide_keyboard=False) -> ReplyKeyboardMarkup:
    """
    :param option:
    :param times: A list of times for notification menu options. Defaults to None.
    :param hide_keyboard: A boolean flag indicating whether to hide the keyboard after selecting an option. Defaults to False.
    :return: A ReplyKeyboardMarkup object representing the notification menu.
    """
    actions = {settings.PROGRAMMING_DONE_BUTTON: MenuOption(0)}

    row_count = 1
    available_times = list(settings.ONCE_A_DAY.keys())

    if option in {'one', 'all'}:
        for index, selected_time in enumerate(available_times):
            if index % 3 == 0 and index >= 2:
                row_count += 1
            actions.update(cheack_options(selected_time, row_count, times))

    return assemble_keyboard(actions, KeyboardType.KEYBOARD, hide_keyboard=hide_keyboard)
