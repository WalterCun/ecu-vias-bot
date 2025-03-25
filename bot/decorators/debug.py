#!/usr/bin/env python3
""" debug.py """
import inspect

from settings import settings


def print_result(func):
    """
    A decorator that prints the name of the function and its result after
    the function is executed.

    Args:
        func (function): The function to be wrapped by the decorator.

    Returns:
        function: The wrapper function that adds the printing functionality.
    """

    async def async_wrapper(*args, **kwargs):
        """
        A decorator that prints the name of the function and its result after
        the function is executed.

        Args:
            func (function): The function to be wrapped by the decorator.

        Returns:
            function: The wrapper function that adds the printing functionality.
        """
        result = await func(*args, **kwargs)
        print(func.__name__, result)

    def sync_wrapper(*args, **kwargs):
        """
        A wrapper for sync functions.
        """
        result = func(*args, **kwargs)
        print(func.__name__, result)

    if settings.DEBUG:
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return func
