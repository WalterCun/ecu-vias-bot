"""Helpers for conversation state management.

Keeps handlers small and consistent while preserving existing behavior.
"""

from __future__ import annotations

from typing import Any

from bot.settings import settings


def get_language(user_data: dict[str, Any], fallback: str = 'es') -> str:
    lang = user_data.get('language') or fallback
    return lang if isinstance(lang, str) and len(lang) >= 2 else fallback


def set_language(user_data: dict[str, Any], lang: str) -> None:
    user_data['language'] = lang


def get_selected_provinces(user_data: dict[str, Any]) -> list[str]:
    provinces = user_data.get('provinces', [])
    return provinces if isinstance(provinces, list) else []


def toggle_province(user_data: dict[str, Any], province: str) -> list[str]:
    provinces = get_selected_provinces(user_data)

    if province == settings.CONTINUE_BUTTON:
        user_data['provinces'] = provinces
        return provinces

    if province in provinces:
        provinces.remove(province)
    else:
        provinces.append(province)

    user_data['provinces'] = provinces
    return provinces


def get_selected_times(user_data: dict[str, Any]) -> list[str]:
    times = user_data.get('times', [])
    if not isinstance(times, list):
        return []
    return [value for value in times if value in settings.ONCE_A_DAY]


def toggle_time(user_data: dict[str, Any], selected_time: str) -> list[str]:
    times = get_selected_times(user_data)

    if selected_time in times:
        times.remove(selected_time)
    elif selected_time in settings.ONCE_A_DAY:
        times.append(selected_time)

    user_data['times'] = times
    return times


def set_alarm_times(user_data: dict[str, Any], times: list[str]) -> None:
    user_data['alarms'] = list(times)
    user_data.pop('times', None)


def clear_subscription_state(user_data: dict[str, Any]) -> None:
    user_data.pop('subscriptions', None)
    user_data.pop('times', None)
    user_data.pop('alarms', None)
