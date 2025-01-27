from telegram import ReplyKeyboardMarkup

from src.controller.languages.translations import language
from src.controller.utils.assamble_keyboard_menu import assemble_keyboard, MenuOption, KeyboardType


def initial_menu() -> ReplyKeyboardMarkup:
    """
    Initial_menu() -> ReplyKeyboardMarkup

    Assembles and returns the initial menu as a ReplyKeyboardMarkup object.

    Returns:
        ReplyKeyboardMarkup: The initial menu keyboard markup.

    """
    actions = {language.menu_buttons_subscribe: MenuOption(row=0),
               language.menu_buttons_unsubscribe: MenuOption(row=0),
               language.menu_buttons_settings: MenuOption(row=1),
               language.menu_buttons_stop: MenuOption(row=1)}
    return assemble_keyboard(actions, KeyboardType.KEYBOARD)
