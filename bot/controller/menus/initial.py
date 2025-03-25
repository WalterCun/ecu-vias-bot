from telegram import ReplyKeyboardMarkup


from bot.controller.utils.assamble_keyboard_menu import assemble_keyboard, MenuOption, KeyboardType
from bot.translations.core import translate


def initial_menu() -> ReplyKeyboardMarkup:
    """
    Initial_menu() -> ReplyKeyboardMarkup

    Assembles and returns the initial menu as a ReplyKeyboardMarkup object.

    Returns:
        ReplyKeyboardMarkup: The initial menu keyboard markup.

    """
    actions = {translate.menu_buttons_subscribe: MenuOption(row=0),
               translate.menu_buttons_unsubscribe: MenuOption(row=0),
               translate.menu_buttons_settings: MenuOption(row=1),
               translate.menu_buttons_stop: MenuOption(row=1)}
    return assemble_keyboard(actions, KeyboardType.KEYBOARD)
