#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django import template
from babel.numbers import format_decimal


register = template.Library()


@register.simple_tag
def get_prefix_key(form, prefix, rid, attribute=None):
    field = form["{p}-{id}".format(p=prefix, id=rid)]
    if attribute is None:
        return field
    attr = getattr(field, attribute)
    if hasattr(attr, '__call__'):
        return attr()
    return attr


@register.filter(name='percent')
def percent(number):
    return "{}%".format(format_decimal(number * 100, format='#,##0.#;-#'))
