from telegram import ReplyKeyboardMarkup

from bot.controller.utils.assamble_keyboard_menu import MenuOption, assemble_keyboard, KeyboardType

__all__ = ['suscriptor_menu']

from bot.controller.utils.cheack_options_buttons import cheack_options
from bot.libs.translate import trans
from bot.settings.const import PROVINCES


def suscriptor_menu(subscribed: list = None, hide_keyboard=False) -> ReplyKeyboardMarkup:
    """
    :param subscribed: A list of options that the subscriber has already subscribed to. Defaults to None.
    :param hide_keyboard: A boolean value indicating whether to hide the keyboard after displaying the menu. Defaults to False.
    :return: A ReplyKeyboardMarkup object containing the subscriber menu options.
    """
    actions = {
        trans.suscriptor.sms_continue: MenuOption(0)
               }
    row_count = 1
    for province_index, province in enumerate(PROVINCES):

        if province_index % 3 == 0 and province_index >= 2:
            row_count += 1
        actions.update(cheack_options(province, row_count, subscribed))

    return assemble_keyboard(actions, KeyboardType.KEYBOARD, hide_keyboard=hide_keyboard)
