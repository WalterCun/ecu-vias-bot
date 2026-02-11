#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""  """

MAJOR = 0
MINOR = 1
MICRO = 25
RELEASE = False

__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

if not RELEASE:
    # if it's a rcx release, it's not proceeded by a period. If it is a
    # devx release, it must start with a period
    __version__ += '.dev0'

