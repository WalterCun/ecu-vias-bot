#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local-first translation proxy.

This module intentionally prioritizes static translation files and does not
require any translation server to work.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from bot.settings import settings

logger = logging.getLogger(__name__)


class TranslationNode:
    """Dynamic accessor for nested translation dictionaries."""

    def __init__(self, value: Any, path: str = "") -> None:
        self._value = value
        self._path = path

    def __getattr__(self, item: str) -> "TranslationNode | str":
        if isinstance(self._value, dict):
            if item in self._value:
                child = self._value[item]
                child_path = f"{self._path}.{item}" if self._path else item
                if isinstance(child, dict):
                    return TranslationNode(child, child_path)
                return child

            missing_path = f"{self._path}.{item}" if self._path else item
            logger.warning("Missing translation key: %s", missing_path)
            return missing_path

        raise AttributeError(f"'{type(self._value).__name__}' object has no attribute '{item}'")

    def __str__(self) -> str:
        if isinstance(self._value, str):
            return self._value
        return str(self._value)


class LocalTranslator:
    """Translator that resolves keys from local JSON files only."""

    def __init__(self, translations_dir: Path, default_lang: str = "es") -> None:
        self.translations_dir = translations_dir
        self.default_lang = default_lang
        self._lang = default_lang
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def lang(self) -> str:
        return self._lang

    @lang.setter
    def lang(self, value: str) -> None:
        normalized = (value or self.default_lang).split("-")[0].lower()
        if normalized not in self.available_languages:
            logger.info(
                "Translation language '%s' not found. Falling back to '%s'.",
                normalized,
                self.default_lang,
            )
            normalized = self.default_lang
        self._lang = normalized

    @property
    def available_languages(self) -> set[str]:
        if not self.translations_dir.exists():
            return {self.default_lang}
        return {file.stem.lower() for file in self.translations_dir.glob("*.json")}

    def set_lang(self, value: str) -> None:
        self.lang = value

    def _load_language(self, lang: str) -> dict[str, Any]:
        if lang in self._cache:
            return self._cache[lang]

        lang_file = self.translations_dir / f"{lang}.json"
        if not lang_file.exists():
            logger.warning("Translation file not found for '%s'. Using empty map.", lang)
            self._cache[lang] = {}
            return self._cache[lang]

        with lang_file.open("r", encoding="utf-8") as file:
            self._cache[lang] = json.load(file)
        return self._cache[lang]

    def __getattr__(self, item: str) -> TranslationNode | str:
        selected = self._load_language(self._lang)
        fallback = self._load_language(self.default_lang)

        if item in selected:
            value = selected[item]
        elif item in fallback:
            value = fallback[item]
            logger.info("Using fallback translation key '%s' from '%s'.", item, self.default_lang)
        else:
            logger.warning("Missing top-level translation key: %s", item)
            return item

        if isinstance(value, dict):
            return TranslationNode(value, item)
        return value


trans = LocalTranslator(
    translations_dir=Path(settings.LOCALES_PATH),
    default_lang='es',
)
