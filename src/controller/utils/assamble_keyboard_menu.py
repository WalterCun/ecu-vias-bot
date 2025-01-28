""" src/bot_controller/utils/assamble_keyboard_menu.py """
from dataclasses import dataclass
from enum import Enum

from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

__all__ = ['KeyboardType', 'assemble_keyboard', 'MenuOption']


@dataclass
class MenuOption:
    """
    A class representing a menu option with a specified row.

    Attributes:
        row (int): The row number of the menu option.
    """
    row: int


class KeyboardType(Enum):
    """

    Enum class representing types of keyboards.

    Attributes:
        INLINE: Represents an inline keyboard.
        KEYBOARD: Represents a regular keyboard.

    """
    INLINE = 'inline'
    KEYBOARD = 'keyboard'


def add_button_to_keyboard(key: str, menu_option: MenuOption, keyboard: dict, to_upper: bool = False):
    """
    :param key: The label or text to be displayed on the button.
    :param menu_option: An instance of the MenuOption class representing the button's menu option.
    :param keyboard: A dictionary representing the keyboard layout.
    :param to_upper: A boolean value indicating whether the button label should be converted to uppercase.
    :return: None

    This method adds a button to the specified keyboard layout.
    The button is created using the provided label `key`
    and appended to the row specified by `menu_option`.
    If the row does not
    * exist in the `keyboard` dictionary, it will be created.
    The `to_upper` parameter determines whether the button
    label should be converted to uppercase before adding it.

    Example usage:

        menu_option = MenuOption(row=1, column=2)
        keyboard = {}
        add_button_to_keyboard("Click me", menu_option, keyboard)
    """
    if keyboard.get(menu_option.row) is None:
        keyboard[menu_option.row] = []
    keyboard[menu_option.row].append(KeyboardButton(key.upper() if to_upper else key))


def assemble_keyboard(actions: dict[str, MenuOption],
                      model: KeyboardType,
                      hide_keyboard=True) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Assembles a keyboard layout for a messaging application.

    Parameters:
        actions (dict[str, MenuOption]): A dictionary mapping action text to their corresponding menu options.
        model (KeyboardType): The type of keyboard to be assembled (inline or regular).
        hide_keyboard (bool): If True, the keyboard will be hidden after one use (applies to regular keyboards only).

    Returns:
        InlineKeyboardMarkup | ReplyKeyboardMarkup:
        The assembled keyboard markup object suitable for displaying in the
        chat interface.
    """
    keyboard = {}

    for action_text, menu_option in actions.items():
        if model == KeyboardType.INLINE:
            add_button_to_keyboard(action_text, menu_option, keyboard)
        elif model == KeyboardType.KEYBOARD:
            # add_button_to_keyboard(action_text, menu_option, keyboard, to_upper=True)
            add_button_to_keyboard(action_text, menu_option, keyboard)

    if model == KeyboardType.INLINE:
        return InlineKeyboardMarkup(list(keyboard.values()))
    else:
        return ReplyKeyboardMarkup(list(keyboard.values()), one_time_keyboard=hide_keyboard)
