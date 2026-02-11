#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation integration using ToolsTranslator (local-first).

This project uses translation files stored in `locale/*.json` as its primary
source. Translation server features are optional and not required for runtime.
"""

from __future__ import annotations

from pathlib import Path

from translator import Translator

from bot.settings import settings

trans = Translator(
    translations_dir=Path(settings.LOCALES_PATH),
    default_lang='es',
    nested=True,
    auto_add_missing_keys=False,
)
