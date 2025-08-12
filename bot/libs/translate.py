#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""  """
from pathlib import Path

from translator import Translator

from bot.settings import settings

trans = Translator(
    translations_dir=Path(settings.BASE_DIR) / 'locale',
    default_lang='es',
    nested=True,
    auto_add_missing_keys=False
)

# if __name__ == '__main__':
#     print(trans.start.start.welcome)
