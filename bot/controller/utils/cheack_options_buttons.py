from bot.controller.utils.assamble_keyboard_menu import MenuOption


def cheack_options(options: str, row_count: int, data: list = None):
    """
    Checks if time is in data list and returns a dictionary containing the menu icon, time, and MenuOption.

    :param time: The time to check.
    :param row_count: The row count for the MenuOption.
    :param data: (Optional) The list of data to check against. Default is None.
    :return: A dictionary containing the menu icon, time, and MenuOption.

    """
    menu_icon = '✅ ' if data and options in data else ''
    return {f"{menu_icon}{options}": MenuOption(row=row_count)}
