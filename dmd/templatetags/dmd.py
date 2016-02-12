#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django import template
from babel.numbers import format_decimal

from dmd.models.Indicators import Indicator

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


def default_compute_value(numerator, denominator,
                          itype=Indicator.PERCENTAGE):
        if itype == Indicator.PROPORTION:
            return numerator / denominator
        else:
            coef = Indicator.TYPES_COEFFICIENT.get(itype)
            try:
                return (numerator * coef) / denominator
            except ZeroDivisionError:
                raise


@register.filter(name='format_number')
def default_format_number(value):
        if value is None:
            return None
        return format_decimal(value, format="#,##0.##;-#")


def default_format_value(value, numerator, denominator,
                         itype=Indicator.PERCENTAGE,
                         value_format=Indicator.PERCENT_FMT):
        if value is None:
            return "n/a"
        fval = default_format_number(
            default_compute_value(numerator, denominator, itype=itype))
        numerator = default_format_number(numerator)
        denominator = default_format_number(denominator)
        return value_format.format(
            value=fval, numerator=numerator, denominator=denominator)
