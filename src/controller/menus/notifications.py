from telegram import ReplyKeyboardMarkup

from src.controller.utils.assamble_keyboard_menu import assemble_keyboard, KeyboardType

__all__ = ['notification_menu', 'notification_menu_times']

from src.controller.utils.cheack_options_buttons import cheack_options
from src.settings.const import ONCE_A_DAY, SEVERAL_TIMES_A_DAY


def notification_menu(times: list = None, hide_keyboard=False) -> ReplyKeyboardMarkup:
    """
    :param times: A list of times for notification menu options. Defaults to None. :param hide_keyboard: A boolean
    flag indicating whether to hide the keyboard after selecting an option. Defaults to False. :return: A
    ReplyKeyboardMarkup object representing the notification menu.

    """
    options = [
        'UNA NOTIFICACION EN EL DIA',
        # 'VARIAS NOTIFICACIONES EN EL DIA',
        # 'CUANDO EXISISTAN CAMBIOS'
    ]
    actions = {}
    row_count = 0
    for index, province in enumerate(options):
        if index % 1 == 0 and index >= 1:
            row_count += 1
        actions.update(cheack_options(province, row_count, times))

    return assemble_keyboard(actions, KeyboardType.KEYBOARD, hide_keyboard=hide_keyboard)


def notification_menu_times(times: list = None, option: str = 'one', hide_keyboard=False) -> ReplyKeyboardMarkup:
    """
    :param option:
    :param times: A list of times for notification menu options. Defaults to None.
    :param hide_keyboard: A boolean flag indicating whether to hide the keyboard after selecting an option. Defaults to False.
    :return: A ReplyKeyboardMarkup object representing the notification menu.

    """
    actions = {
        # language.general_msm_programming: MenuOption(0)
    }
    row_count = 1

    if option == 'one':
        for index, time in enumerate(ONCE_A_DAY.keys()):
            if index % 3 == 0 and index >= 2:
                row_count += 1
            actions.update(cheack_options(time, row_count, times))

    elif option == 'all':
        for index, time in enumerate(SEVERAL_TIMES_A_DAY):
            if index % 3 == 0 and index >= 2:
                row_count += 1
            actions.update(cheack_options(time, row_count, times))

    return assemble_keyboard(actions, KeyboardType.KEYBOARD, hide_keyboard=hide_keyboard)
