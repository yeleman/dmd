#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import re

from py3compat import text_type

from dmd.utils import import_path

logger = logging.getLogger(__name__)


def build_sections_list():
    d = {}
    for fname in os.listdir(os.path.join(*['dmd', 'analysis'])):
        if not fname.endswith('.py') \
                or not re.match(r'^section([0-9]+)\.py$', fname):
            continue
        mod = import_path('dmd.analysis.{}'.format(fname[:-3]), failsafe=True)
        if mod is None:
            continue
        d.update({text_type(mod.SECTION_ID): mod.SECTION_NAME})
    return d

SECTIONS = build_sections_list()
