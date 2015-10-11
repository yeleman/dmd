#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

import openpyxl

logger = logging.getLogger(__name__)


def letter_to_column(letter):
    return openpyxl.cell.column_index_from_string(letter)


def column_to_letter(column):
    return openpyxl.cell.get_column_letter(column)
