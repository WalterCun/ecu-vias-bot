from telegram import ReplyKeyboardMarkup


from bot.controller.utils.assamble_keyboard_menu import assemble_keyboard, MenuOption, KeyboardType
from bot.libs.translate import trans


def initial_menu() -> ReplyKeyboardMarkup:
    """
    Initial_menu() -> ReplyKeyboardMarkup

    Assembles and returns the initial menu as a ReplyKeyboardMarkup object.

    Returns:
        ReplyKeyboardMarkup: The initial menu keyboard markup.

    """
    actions = {f"{trans.moderator.menu.btns.subscribe}": MenuOption(row=0),
               f"{trans.moderator.menu.btns.unsubscribe}": MenuOption(row=0),
               f"{trans.moderator.menu.btns.settings}": MenuOption(row=1),
               f"{trans.moderator.menu.btns.stop}": MenuOption(row=1)}
    return assemble_keyboard(actions, KeyboardType.KEYBOARD)
